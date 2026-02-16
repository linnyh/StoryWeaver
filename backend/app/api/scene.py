import json
import re
import asyncio
from typing import AsyncGenerator, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db, AsyncSessionLocal
from app.models import Scene, Chapter, Character, Novel, Relationship
from app.services import scene_generator, summarizer, state_analyzer, relationship_analyzer
from app.rag import rag_service
from app.api.scene_chat import router as chat_router

class SceneUpdateRequest(BaseModel):
    content: Optional[str] = None
    summary: Optional[str] = None
    status: Optional[str] = None
    tension_level: Optional[int] = None
    emotional_target: Optional[str] = None
    characters_present: Optional[list[str]] = None

class SceneDetailResponse(BaseModel):
    id: str
    chapter_id: str
    order_index: int
    title: Optional[str] = None
    location: Optional[str] = None
    beat_description: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    status: Optional[str] = None
    context_summary: Optional[str] = None 
    tension_level: Optional[int] = None
    emotional_target: Optional[str] = None

    class Config:
        from_attributes = True

router = APIRouter()
router.include_router(chat_router)



async def background_analyze_state(scene_id: str):
    """后台任务：分析角色状态变化 & 角色关系变化"""
    print(f"Starting background state/relationship analysis for scene {scene_id}")
    async with AsyncSessionLocal() as db:
        try:
            # 联合查询 Scene 和 Chapter, Novel 以获取 genre
            stmt = (
                select(Scene, Chapter, Novel)
                .join(Chapter, Scene.chapter_id == Chapter.id)
                .join(Novel, Chapter.novel_id == Novel.id)
                .where(Scene.id == scene_id)
            )
            result = await db.execute(stmt)
            row = result.first()
            
            if not row:
                return
                
            scene, chapter, novel = row
            
            if not scene.content or not scene.characters_present:
                return

            # 收集参与场景的角色对象
            characters = []
            
            # 1. 分析个人状态 (Power State)
            for char_id in scene.characters_present:
                # 获取角色
                char_result = await db.execute(select(Character).where(Character.id == char_id))
                character = char_result.scalar_one_or_none()
                if not character:
                    continue
                
                characters.append(character)
                
                # 分析状态
                print(f"Analyzing state for character {character.name} in scene {scene_id} (Genre: {novel.genre})...")
                new_state = await state_analyzer.analyze_state(character, scene.content, genre=novel.genre or "玄幻")
                
                if new_state:
                    print(f"Updating state for {character.name}: {new_state}")
                    character.power_state = new_state
                    db.add(character)
            
            # 2. 分析角色关系 (Relationships)
            if len(characters) >= 2:
                from sqlalchemy import or_, and_
                char_ids = [c.id for c in characters]
                
                # 获取现有的关系记录
                stmt = select(Relationship).where(
                    and_(
                        Relationship.character_a_id.in_(char_ids),
                        Relationship.character_b_id.in_(char_ids)
                    )
                )
                rels_result = await db.execute(stmt)
                existing_rels = rels_result.scalars().all()
                
                # 建立映射 key = "id_a:id_b" (确保 id_a < id_b)
                rels_map = {}
                for r in existing_rels:
                    key = f"{r.character_a_id}:{r.character_b_id}"
                    rels_map[key] = r
                
                # 调用 AI 分析
                print(f"Analyzing relationships for {len(characters)} characters...")
                updates = await relationship_analyzer.analyze_relationships(
                    scene.content, characters, rels_map
                )
                
                # 应用更新
                for update in updates:
                    id_a = update["char_a_id"]
                    id_b = update["char_b_id"]
                    # 确保顺序一致
                    id_a, id_b = sorted([id_a, id_b])
                    key = f"{id_a}:{id_b}"
                    
                    rel = rels_map.get(key)
                    if not rel:
                        # 创建新关系
                        rel = Relationship(
                            novel_id=novel.id,
                            character_a_id=id_a,
                            character_b_id=id_b,
                            affinity_score=0
                        )
                        db.add(rel)
                    
                    # 更新字段
                    change = update.get("affinity_change", 0)
                    if change != 0:
                        rel.affinity_score = max(-100, min(100, rel.affinity_score + change))
                    
                    if update.get("new_conflict"):
                        rel.core_conflict = update["new_conflict"]
                        
                    print(f"Updated relationship {id_a}<->{id_b}: Affinity {rel.affinity_score} (Delta {change})")

            await db.commit()
            print(f"Finished state & relationship analysis for scene {scene_id}")
            
        except Exception as e:
            print(f"Error in background_analyze_state for scene {scene_id}: {str(e)}")


async def background_summarize(scene_id: str):
    """后台任务：生成场景摘要"""
    print(f"Starting background summary for scene {scene_id}")
    async with AsyncSessionLocal() as db:
        try:
            # 联合查询 Scene 和 Chapter 以获取 novel_id
            stmt = (
                select(Scene, Chapter)
                .join(Chapter, Scene.chapter_id == Chapter.id)
                .where(Scene.id == scene_id)
            )
            result = await db.execute(stmt)
            row = result.first()
            
            if not row:
                print(f"Scene {scene_id} not found")
                return
                
            scene, chapter = row
            
            if not scene.content:
                print(f"Scene {scene_id} has no content")
                return

            # 生成摘要
            summary = await summarizer.generate_summary(scene.content)
            
            # 更新场景摘要
            scene.summary = summary
            await db.commit()

            # 存入向量数据库 (务必包含 novel_id)
            rag_service.add_knowledge(
                text=summary,
                doc_id=f"scene_summary_{scene_id}",
                type="scene_summary",
                metadata={
                    "scene_id": scene_id,
                    "novel_id": chapter.novel_id,
                    "chapter_id": chapter.id
                }
            )
            print(f"Successfully generated summary for scene {scene_id} (novel={chapter.novel_id}): {summary[:50]}...")
        except Exception as e:
            print(f"Error in background_summarize for scene {scene_id}: {str(e)}")


@router.get("/")
async def list_scenes(chapter_id: str, db: AsyncSession = Depends(get_db)):
    """获取章节的场景列表"""
    result = await db.execute(
        select(Scene).where(Scene.chapter_id == chapter_id).order_by(Scene.order_index)
    )
    scenes = result.scalars().all()
    return scenes


@router.get("/{scene_id}", response_model=SceneDetailResponse)
async def get_scene(scene_id: str, db: AsyncSession = Depends(get_db)):
    """获取场景详情"""
    result = await db.execute(select(Scene).where(Scene.id == scene_id))
    scene = result.scalar_one_or_none()
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
        
    # 动态计算前情提要
    context = await scene_generator._build_context(scene, db)
    context_summary = "\n".join(context.get("prev_summaries", []))
    
    # 构造响应
    response = SceneDetailResponse.model_validate(scene)
    response.context_summary = context_summary
    return response

@router.get("/{scene_id}/generate")
async def generate_scene_content(
    scene_id: str,
    db: AsyncSession = Depends(get_db)
):
    """生成场景正文 (SSE 流式)"""
    # 验证场景存在
    result = await db.execute(select(Scene).where(Scene.id == scene_id))
    scene = result.scalar_one_or_none()
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    async def event_generator():
        """生成 SSE 事件流"""
        full_content = ""

        try:
            async for chunk in scene_generator.generate_scene_content(scene_id, db):
                full_content += chunk
                # 发送 SSE 格式的数据
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"

            # 保存生成的内容到数据库（过滤思考内容）
            # 先过滤思考内容 (支持多行)
            clean_content = re.sub(r'<think>.*?</think>', '', full_content, flags=re.DOTALL)
            clean_content = re.sub(r'\*\*', '', clean_content)  # 移除Markdown加粗
            scene.content = clean_content.strip()
            await db.commit()

            # 触发后台状态分析 (Fire-and-forget)
            # 注意：这里我们不能使用 BackgroundTasks，因为这是在 StreamingResponse 的生成器内部
            # 使用 asyncio.create_task 来异步执行
            asyncio.create_task(background_analyze_state(scene_id))

            # 发送完成信号
            yield f"data: {json.dumps({'done': True, 'scene_id': scene_id})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.post("/{scene_id}/summarize")
async def generate_scene_summary(
    scene_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    自动生成场景摘要

    将场景正文压缩成 200 字摘要，并存入向量数据库
    """
    # 验证场景存在
    result = await db.execute(select(Scene).where(Scene.id == scene_id))
    scene = result.scalar_one_or_none()
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    if not scene.content:
        raise HTTPException(status_code=400, detail="Scene has no content to summarize")

    # 生成摘要
    summary = await summarizer.generate_summary(scene.content)

    # 更新场景摘要
    scene.summary = summary
    await db.commit()

    # 存入向量数据库
    rag_service.add_knowledge(
        text=summary,
        doc_id=f"scene_summary_{scene_id}",
        type="scene_summary",
        metadata={"scene_id": scene_id}
    )

    return {"scene_id": scene_id, "summary": summary}


@router.put("/{scene_id}")
async def update_scene(
    scene_id: str,
    scene_update: SceneUpdateRequest,  # 使用 Pydantic 模型
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """更新场景信息"""
    
    # 1. 查找场景
    result = await db.execute(select(Scene).where(Scene.id == scene_id))
    scene = result.scalar_one_or_none()
    
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    # 2. 更新字段
    # 注意：这里我们只更新传入的字段
    update_data = scene_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(scene, key, value)
    
    # 提交事务保存更改
    await db.commit()
    await db.refresh(scene)

    # 3. 触发后台任务：生成摘要并更新 RAG
    # 策略：
    # - 如果状态变为 'approved' (审核通过/定稿)
    # - 或者 内容更新了且长度 > 200 字 (避免为空内容生成摘要)
    # - 注意：如果前端显式传了 summary，我们通常信任前端的 summary，
    #   但这里 background_summarize 会重新生成覆盖它。
    #   如果用户手动修改了 summary，我们应该把那份 summary 存入 RAG，而不是重新生成。
    
    should_auto_summarize = False
    should_update_rag_only = False
    
    if update_data.get("content") and len(update_data["content"]) > 200:
        should_auto_summarize = True
        
    if update_data.get("status") == "approved":
        should_auto_summarize = True
        
    # 如果用户手动更新了 summary，我们直接把这份 summary 更新到 RAG，而不重新生成
    if update_data.get("summary"):
        should_update_rag_only = True
        should_auto_summarize = False # 手动更新优先
        
    # 只要更新了内容或角色列表，就应该触发状态分析
    should_analyze_state = False
    if update_data.get("content") or update_data.get("characters_present"):
        should_analyze_state = True

    if should_update_rag_only:
        # 直接更新 RAG
        background_tasks.add_task(background_update_rag, scene_id, scene.summary)
    elif should_auto_summarize:
        # 自动生成摘要并更新 RAG
        background_tasks.add_task(background_summarize, scene_id)
        
    if should_analyze_state or should_update_rag_only or should_auto_summarize:
        # 自动分析角色状态
        background_tasks.add_task(background_analyze_state, scene_id)
        
    return scene

async def background_update_rag(scene_id: str, summary: str):
    """后台任务：仅更新 RAG (用于手动修改摘要的情况)"""
    async with AsyncSessionLocal() as db:
        try:
             # 联合查询 Scene 和 Chapter 以获取 novel_id
            stmt = (
                select(Scene, Chapter)
                .join(Chapter, Scene.chapter_id == Chapter.id)
                .where(Scene.id == scene_id)
            )
            result = await db.execute(stmt)
            row = result.first()
            
            if not row:
                return
            
            scene, chapter = row
            
            rag_service.add_knowledge(
                text=summary,
                doc_id=f"scene_summary_{scene_id}",
                type="scene_summary",
                metadata={
                    "scene_id": scene_id,
                    "novel_id": chapter.novel_id,
                    "chapter_id": chapter.id
                }
            )
            print(f"Successfully updated RAG for scene {scene_id} (manual update)")
        except Exception as e:
            print(f"Error in background_update_rag: {e}")
