import json
import re
from typing import AsyncGenerator, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db, AsyncSessionLocal
from app.models import Scene, Chapter
from app.services import scene_generator, summarizer
from app.rag import rag_service

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

    class Config:
        from_attributes = True

router = APIRouter()


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
    scene_update: dict,  # 使用 dict 接收请求体，或者定义 Pydantic 模型
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
    if "content" in scene_update:
        scene.content = scene_update["content"]
    if "summary" in scene_update:
        scene.summary = scene_update["summary"]
    if "status" in scene_update:
        scene.status = scene_update["status"]
    
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
    
    if "content" in scene_update and len(scene_update["content"]) > 200:
        should_auto_summarize = True
        
    if scene_update.get("status") == "approved":
        should_auto_summarize = True
        
    # 如果用户手动更新了 summary，我们直接把这份 summary 更新到 RAG，而不重新生成
    if "summary" in scene_update and scene_update["summary"]:
        should_update_rag_only = True
        should_auto_summarize = False # 手动更新优先
        
    if should_update_rag_only:
        # 直接更新 RAG
        background_tasks.add_task(background_update_rag, scene_id, scene.summary)
    elif should_auto_summarize:
        # 自动生成摘要并更新 RAG
        background_tasks.add_task(background_summarize, scene_id)
        
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
