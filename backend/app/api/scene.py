import json
import re
import asyncio
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.logging import get_logger
from app.models import Scene
from app.services import scene_generator
from app.services.scene_postprocess import (
    analyze_state_and_relationships,
)
from app.services.scene_image_service import generate_scene_images
from app.services.scene_usecases import (
    summarize_scene_content,
    update_scene_and_schedule_tasks,
)
from app.api.scene_chat import router as chat_router
from app.config import settings

logger = get_logger(__name__)


class SceneUpdateRequest(BaseModel):
    content: Optional[str] = None
    summary: Optional[str] = None
    status: Optional[str] = None
    tension_level: Optional[int] = None
    emotional_target: Optional[str] = None
    characters_present: Optional[list[str]] = None
    image_url: Optional[str] = None
    image_prompts: Optional[list[dict]] = None

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
    image_url: Optional[str] = None
    image_prompts: Optional[list[dict]] = None

    class Config:
        from_attributes = True

router = APIRouter()
router.include_router(chat_router)


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
    enable_editorial: bool = True, # Query param, default True
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
            async for item in scene_generator.generate_scene_content(scene_id, db, enable_editorial=enable_editorial):
                # item 是字典: {"type": "...", "content": "..."}
                
                if item["type"] == "content":
                    full_content += item["content"]
                    yield f"data: {json.dumps({'chunk': item['content']})}\n\n"
                    
                elif item["type"] == "log":
                    yield f"data: {json.dumps({'log': item['content']})}\n\n"
                    
                elif item["type"] == "system":
                    yield f"data: {json.dumps({'system': item['content']})}\n\n"

            # 保存生成的内容到数据库（过滤思考内容）
            # 先过滤思考内容 (支持多行)
            clean_content = re.sub(r'<think>.*?</think>', '', full_content, flags=re.DOTALL)
            clean_content = re.sub(r'\*\*', '', clean_content)  # 移除Markdown加粗
            scene.content = clean_content.strip()
            await db.commit()

            # 触发后台状态分析 (Fire-and-forget)
            asyncio.create_task(analyze_state_and_relationships(scene_id))

            # 发送完成信号
            yield f"data: {json.dumps({'done': True, 'scene_id': scene_id})}\n\n"

        except Exception as e:
            logger.exception("Scene generate stream failed scene=%s", scene_id)
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.post("/{scene_id}/generate_image")
async def generate_scene_image(
    scene_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    生成场景分镜配图 (MiniMax) - 多张
    1. 调用 LLM 生成 3-4 个分镜 Prompt
    2. 并行调用 MiniMax 文生图
    3. 存储结果
    """
    if not settings.minimax_api_key:
        raise HTTPException(status_code=500, detail="MiniMax API Key not configured")

    result = await db.execute(select(Scene).where(Scene.id == scene_id))
    scene = result.scalar_one_or_none()
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
        
    generated_images = await generate_scene_images(
        scene_location=scene.location,
        scene_content=scene.content,
        scene_beat_description=scene.beat_description,
    )
    
    if not generated_images:
        raise HTTPException(status_code=500, detail="Failed to generate any images")

    # --- Step 3: Save to DB ---
    scene.image_prompts = generated_images
    # Update image_url to the first one for backward compatibility if needed, or just leave it
    if generated_images:
        scene.image_url = generated_images[0]["url"]
        
    await db.commit()
    
    return {"scene_id": scene_id, "images": generated_images}


@router.post("/{scene_id}/summarize")
async def generate_scene_summary(
    scene_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    自动生成场景摘要

    将场景正文压缩成 200 字摘要，并存入向量数据库
    """
    return await summarize_scene_content(scene_id, db)


@router.put("/{scene_id}")
async def update_scene(
    scene_id: str,
    scene_update: SceneUpdateRequest,  # 使用 Pydantic 模型
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """更新场景信息"""
    
    update_data = scene_update.model_dump(exclude_unset=True)
    return await update_scene_and_schedule_tasks(
        scene_id=scene_id,
        scene_update_data=update_data,
        background_tasks=background_tasks,
        db=db,
    )
