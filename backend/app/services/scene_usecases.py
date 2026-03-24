"""Scene-oriented usecases to keep router thin."""
from fastapi import BackgroundTasks, HTTPException
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Chapter, Scene, SceneVersion
from app.rag import rag_service
from app.api.settings import get_llm_config_from_db

MAX_SCENE_VERSIONS = 20
from app.services import summarizer
from app.services.scene_postprocess import (
    analyze_state_and_relationships,
    summarize_scene,
    update_scene_summary_in_rag,
)


async def summarize_scene_content(scene_id: str, db: AsyncSession) -> dict[str, str]:
    """Generate and persist summary for one scene."""
    result = await db.execute(
        select(Scene, Chapter)
        .join(Chapter, Scene.chapter_id == Chapter.id)
        .where(Scene.id == scene_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Scene not found")

    scene, chapter = row
    if not scene.content:
        raise HTTPException(status_code=400, detail="Scene has no content to summarize")

    llm_config = await get_llm_config_from_db(db)
    summary = await summarizer.generate_summary(scene.content, model_override=llm_config.summary_model)
    scene.summary = summary
    await db.commit()

    rag_service.add_knowledge(
        text=summary,
        doc_id=f"scene_summary_{scene_id}",
        type="scene_summary",
        metadata={
            "scene_id": scene_id,
            "novel_id": chapter.novel_id,
            "chapter_id": chapter.id,
        },
    )
    return {"scene_id": scene_id, "summary": summary}


async def _save_scene_version_if_content_changed(
    scene: Scene, new_content: str, db: AsyncSession
) -> None:
    """若当前有正文且与新内容不同，则保存为历史版本并保留最近 MAX_SCENE_VERSIONS 条。"""
    if not new_content or not (scene.content or "").strip():
        return
    if scene.content.strip() == new_content.strip():
        return
    db.add(SceneVersion(scene_id=scene.id, content=scene.content))
    await db.flush()
    # 只保留最近 MAX_SCENE_VERSIONS 条
    result = await db.execute(
        select(SceneVersion.id)
        .where(SceneVersion.scene_id == scene.id)
        .order_by(SceneVersion.created_at.desc())
    )
    ids_ordered = [row[0] for row in result.all()]
    to_remove = ids_ordered[MAX_SCENE_VERSIONS:]
    if to_remove:
        await db.execute(delete(SceneVersion).where(SceneVersion.id.in_(to_remove)))
    await db.flush()


async def update_scene_and_schedule_tasks(
    scene_id: str,
    scene_update_data: dict,
    background_tasks: BackgroundTasks,
    db: AsyncSession,
) -> Scene:
    """Update scene and schedule follow-up background jobs."""
    result = await db.execute(select(Scene).where(Scene.id == scene_id))
    scene = result.scalar_one_or_none()
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    new_content = scene_update_data.get("content")
    if new_content is not None:
        await _save_scene_version_if_content_changed(scene, new_content, db)

    for key, value in scene_update_data.items():
        setattr(scene, key, value)

    await db.commit()
    await db.refresh(scene)

    should_auto_summarize = False
    should_update_rag_only = False

    content = scene_update_data.get("content")
    if content and len(content) > 200:
        should_auto_summarize = True

    if scene_update_data.get("status") == "approved":
        should_auto_summarize = True

    if scene_update_data.get("summary"):
        should_update_rag_only = True
        should_auto_summarize = False

    should_analyze_state = bool(
        scene_update_data.get("content") or scene_update_data.get("characters_present")
    )

    if should_update_rag_only:
        background_tasks.add_task(
            update_scene_summary_in_rag,
            scene_id,
            scene.summary or "",
        )
    elif should_auto_summarize:
        background_tasks.add_task(summarize_scene, scene_id)

    if should_analyze_state or should_update_rag_only or should_auto_summarize:
        background_tasks.add_task(analyze_state_and_relationships, scene_id)

    return scene
