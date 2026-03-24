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
from app.models import Scene, SceneVersion, Chapter, Character
from app.services import scene_generator
from app.services.scene_postprocess import (
    analyze_state_and_relationships,
)
from app.services.scene_image_service import generate_scene_images
from app.services.scene_video_service import (
    create_scene_video_task,
    query_video_task_status,
    fetch_video_download_url,
    _build_video_prompt,
)
from app.services.scene_usecases import (
    summarize_scene_content,
    update_scene_and_schedule_tasks,
)
from app.api.scene_chat import router as chat_router
from app.api.settings import get_llm_config_from_db
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
    video_task_id: Optional[str] = None
    video_url: Optional[str] = None
    video_prompt: Optional[str] = None

    class Config:
        from_attributes = True


class GenerateVideoRequest(BaseModel):
    prompt: Optional[str] = None  # 可选，不传则用场景信息自动拼装


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


class SceneVersionItem(BaseModel):
    id: str
    scene_id: str
    content_preview: str
    created_at: str

    class Config:
        from_attributes = True


@router.get("/{scene_id}/versions", response_model=list)
async def list_scene_versions(scene_id: str, db: AsyncSession = Depends(get_db)):
    """列出场景历史版本（按时间倒序，最近在前）。"""
    result = await db.execute(
        select(SceneVersion)
        .where(SceneVersion.scene_id == scene_id)
        .order_by(SceneVersion.created_at.desc())
    )
    rows = result.scalars().all()
    out = []
    for v in rows:
        created = v.created_at.isoformat() if hasattr(v.created_at, "isoformat") else str(v.created_at)
        out.append({
            "id": v.id,
            "scene_id": v.scene_id,
            "content_preview": (v.content or "")[:200],
            "content": v.content,
            "created_at": created,
        })
    return out


class RestoreVersionRequest(BaseModel):
    version_id: str


@router.post("/{scene_id}/restore_version", response_model=SceneDetailResponse)
async def restore_scene_version(
    scene_id: str,
    body: RestoreVersionRequest,
    db: AsyncSession = Depends(get_db),
):
    """将场景正文恢复为指定历史版本。"""
    ver_result = await db.execute(
        select(SceneVersion).where(
            SceneVersion.id == body.version_id,
            SceneVersion.scene_id == scene_id,
        )
    )
    version = ver_result.scalar_one_or_none()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    scene_result = await db.execute(select(Scene).where(Scene.id == scene_id))
    scene = scene_result.scalar_one_or_none()
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    scene.content = version.content
    await db.commit()
    await db.refresh(scene)
    response = SceneDetailResponse.model_validate(scene)
    response.context_summary = ""
    return response


@router.get("/{scene_id}/generate")
async def generate_scene_content(
    scene_id: str,
    enable_editorial: bool = False,  # 默认关闭，优先生成速度；开启后会进行逻辑/爽点/思想审查
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
            llm_config = await get_llm_config_from_db(db)
            async for item in scene_generator.generate_scene_content(
                scene_id, db,
                enable_editorial=enable_editorial,
                writing_model=llm_config.writing_model,
                editorial_model=llm_config.editorial_model if enable_editorial else None,
            ):
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
    生成场景分镜配图 (MiniMax) - 多张。
    若场景中有角色且该角色已生成肖像，则使用主体参考使分镜中人物与肖像一致。
    """
    if not settings.minimax_api_key:
        raise HTTPException(status_code=500, detail="MiniMax API Key not configured")

    result = await db.execute(select(Scene).where(Scene.id == scene_id))
    scene = result.scalar_one_or_none()
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    ch_result = await db.execute(select(Chapter).where(Chapter.id == scene.chapter_id))
    chapter = ch_result.scalar_one_or_none()
    novel_id = chapter.novel_id if chapter else None
    subject_reference_url = None
    if novel_id:
        present_list = (scene.characters_present or []) if isinstance(scene.characters_present, list) else []
        char_result = await db.execute(
            select(Character).where(
                Character.novel_id == novel_id,
                Character.portrait_url.isnot(None),
            )
        )
        for c in char_result.scalars().all():
            if not (c.portrait_url and c.portrait_url.strip()):
                continue
            if not present_list or c.id in present_list or (getattr(c, "name", None) and c.name in present_list):
                subject_reference_url = c.portrait_url.strip()
                break

    generated_images = await generate_scene_images(
        scene_location=scene.location,
        scene_content=scene.content,
        scene_beat_description=scene.beat_description,
        subject_reference_url=subject_reference_url,
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


@router.post("/{scene_id}/generate_video")
async def generate_scene_video(
    scene_id: str,
    body: Optional[GenerateVideoRequest] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    为分镜创建视频生成任务（MiniMax 主体参考），人物与角色肖像一致。
    可传 body.prompt 使用自定义提示词；不传则按场景地点、节拍、分镜 prompt 自动拼装。
    """
    if not settings.minimax_api_key:
        raise HTTPException(status_code=500, detail="MiniMax API Key not configured")
    result = await db.execute(select(Scene).where(Scene.id == scene_id))
    scene = result.scalar_one_or_none()
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    ch_result = await db.execute(select(Chapter).where(Chapter.id == scene.chapter_id))
    chapter = ch_result.scalar_one_or_none()
    novel_id = chapter.novel_id if chapter else None
    if not novel_id:
        raise HTTPException(status_code=400, detail="Scene has no novel")
    # characters_present 可能是角色 ID 或名字列表（beats 多为名字）；名单可能为空或与 DB 不一致，故需回退
    present_list = (scene.characters_present or []) if isinstance(scene.characters_present, list) else []
    present_set = {str(x).strip() for x in present_list if x is not None}
    portrait_urls = []
    fallback_urls = []
    char_result = await db.execute(
        select(Character).where(
            Character.novel_id == novel_id,
            Character.portrait_url.isnot(None),
        )
    )
    for c in char_result.scalars().all():
        url = (c.portrait_url or "").strip()
        if not url:
            continue
        if not present_set:
            portrait_urls.append(url)
        elif c.id in present_set or (getattr(c, "name", None) and (c.name or "").strip() in present_set):
            portrait_urls.append(url)
        fallback_urls.append(url)
    if not portrait_urls:
        portrait_urls = fallback_urls
    if not portrait_urls:
        raise HTTPException(
            status_code=400,
            detail="请先为场景中的角色生成肖像，至少一个角色需有肖像图",
        )
    first_prompt = None
    if scene.image_prompts and len(scene.image_prompts) > 0 and isinstance(scene.image_prompts[0], dict):
        first_prompt = scene.image_prompts[0].get("prompt")
    prompt = (
        (body and body.prompt and body.prompt.strip())
        or _build_video_prompt(
            scene.location,
            scene.beat_description,
            first_prompt,
        )
    )
    task_id, err_msg = await create_scene_video_task(prompt=prompt, subject_image_urls=portrait_urls)
    if not task_id:
        raise HTTPException(
            status_code=502,
            detail=err_msg or "Video task creation failed",
        )
    scene.video_task_id = task_id
    scene.video_url = None
    scene.video_prompt = prompt
    await db.commit()
    await db.refresh(scene)
    return {"scene_id": scene_id, "task_id": task_id, "status": "Pending"}


@router.get("/{scene_id}/video_status")
async def get_scene_video_status(scene_id: str, db: AsyncSession = Depends(get_db)):
    """
    轮询分镜视频任务状态。若任务成功则拉取 video_url 并写入场景，返回 status 与 video_url。
    """
    result = await db.execute(select(Scene).where(Scene.id == scene_id))
    scene = result.scalar_one_or_none()
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    task_id = scene.video_task_id
    if not task_id:
        return {"status": "None", "video_url": scene.video_url}
    status, file_id = await query_video_task_status(task_id)
    if status == "Success" and file_id:
        video_url = await fetch_video_download_url(file_id)
        if video_url:
            scene.video_url = video_url
            scene.video_task_id = None
            await db.commit()
            await db.refresh(scene)
            return {"status": "Success", "video_url": video_url}
        return {"status": "Success", "video_url": None}
    if status == "Fail":
        scene.video_task_id = None
        await db.commit()
        return {"status": "Fail", "video_url": None}
    return {"status": status or "Pending", "video_url": None}


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
