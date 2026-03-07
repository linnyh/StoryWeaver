"""Chapter-oriented usecases to keep router thin."""
import re

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Chapter, Scene
from app.services import scene_generator


async def summarize_chapter_content(chapter_id: str, db: AsyncSession) -> dict[str, str]:
    """Generate chapter summary from all scenes and persist it."""
    result = await db.execute(select(Chapter).where(Chapter.id == chapter_id))
    chapter = result.scalar_one_or_none()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    result = await db.execute(
        select(Scene).where(Scene.chapter_id == chapter_id).order_by(Scene.order_index)
    )
    scenes = result.scalars().all()
    if not scenes:
        raise HTTPException(status_code=400, detail="Chapter has no scenes")

    scene_texts = []
    for scene in scenes:
        text = ""
        if scene.summary:
            text = f"场景{scene.order_index}摘要：{scene.summary}"
        elif scene.content:
            text = f"场景{scene.order_index}正文片段：{scene.content[:500]}..."
        elif scene.beat_description:
            text = f"场景{scene.order_index}细纲：{scene.beat_description}"
        if text:
            scene_texts.append(text)

    if not scene_texts:
        raise HTTPException(status_code=400, detail="Scenes have no content to summarize")

    combined_text = "\n\n".join(scene_texts)
    prompt = f"""请根据以下章节内的场景信息，生成该章节的完整摘要（300-500字）。
    
章节标题：{chapter.title}

{combined_text}

请输出摘要内容（不要包含思考过程）："""

    try:
        summary = await scene_generator.llm.generate(prompt)
        summary = re.sub(r"<think>.*?</think>", "", summary, flags=re.DOTALL).strip()
        chapter.summary = summary
        await db.commit()
        return {"id": chapter.id, "summary": summary}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
