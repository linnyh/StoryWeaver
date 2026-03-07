"""Novel-oriented usecases to keep router thin."""
from urllib.parse import quote

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Chapter, Character, Lore, Novel, Scene
from app.rag import rag_service
from app.services import outline_generator


async def _get_novel_or_404(novel_id: str, db: AsyncSession) -> Novel:
    result = await db.execute(select(Novel).where(Novel.id == novel_id))
    novel = result.scalar_one_or_none()
    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")
    return novel


async def get_rag_summaries_for_novel(novel_id: str, db: AsyncSession) -> list[dict]:
    """Return all RAG scene summaries for a novel."""
    await _get_novel_or_404(novel_id, db)
    return rag_service.retrieve_all_by_novel(
        novel_id=novel_id,
        type="scene_summary",
        top_k=100,
    )


async def update_rag_summary_for_novel(
    novel_id: str,
    doc_id: str,
    text: str,
    db: AsyncSession,
) -> dict[str, str]:
    """Update one RAG summary while preserving metadata."""
    await _get_novel_or_404(novel_id, db)

    all_summaries = rag_service.retrieve_all_by_novel(novel_id, "scene_summary", top_k=1000)
    target_doc = next((item for item in all_summaries if item["id"] == doc_id), None)
    if not target_doc:
        raise HTTPException(status_code=404, detail="Summary not found")

    metadata = target_doc.get("metadata", {})
    rag_service.add_knowledge(
        text=text,
        doc_id=doc_id,
        type="scene_summary",
        metadata=metadata,
    )
    return {"message": "Summary updated", "id": doc_id}


async def delete_rag_summary_for_novel(
    novel_id: str,
    doc_id: str,
    db: AsyncSession,
) -> dict[str, str]:
    """Delete one RAG summary for a novel."""
    await _get_novel_or_404(novel_id, db)
    rag_service.delete_knowledge(doc_id, "scene_summary")
    return {"message": "Summary deleted"}


async def build_novel_export_payload(novel_id: str, db: AsyncSession) -> dict[str, str]:
    """Build plain-text export payload for a novel."""
    novel = await _get_novel_or_404(novel_id, db)

    chapters_result = await db.execute(
        select(Chapter).where(Chapter.novel_id == novel_id).order_by(Chapter.order_index)
    )
    chapters = chapters_result.scalars().all()

    full_text = f"《{novel.title}》\n\n"
    if novel.premise:
        full_text += f"简介：\n{novel.premise}\n\n"
    full_text += "=" * 30 + "\n\n"

    for chapter in chapters:
        full_text += f"第{chapter.order_index}章 {chapter.title}\n"
        full_text += "-" * 20 + "\n\n"

        scenes_result = await db.execute(
            select(Scene).where(Scene.chapter_id == chapter.id).order_by(Scene.order_index)
        )
        scenes = scenes_result.scalars().all()

        for scene in scenes:
            if scene.content:
                full_text += f"{scene.content}\n\n"
            elif scene.beat_description:
                full_text += f"【场景细纲（未生成正文）】\n{scene.beat_description}\n\n"

        full_text += "\n"

    filename = quote(f"{novel.title}.txt")
    return {"content": full_text, "filename": filename}


async def generate_novel_outline_for_novel(
    novel_id: str,
    premise: str,
    genre: str,
    tone: str,
    num_chapters: int,
    db: AsyncSession,
) -> list[Chapter]:
    """Generate and persist chapters/characters/lore for a novel."""
    novel = await _get_novel_or_404(novel_id, db)

    novel.premise = premise
    novel.genre = genre
    novel.tone = tone
    await db.commit()

    existing_chapters = await db.execute(select(Chapter).where(Chapter.novel_id == novel_id))
    for chapter in existing_chapters.scalars().all():
        await db.delete(chapter)

    existing_characters = await db.execute(select(Character).where(Character.novel_id == novel_id))
    for character in existing_characters.scalars().all():
        await db.delete(character)

    existing_lore = await db.execute(select(Lore).where(Lore.novel_id == novel_id))
    for lore in existing_lore.scalars().all():
        await db.delete(lore)

    await db.commit()

    try:
        outline_data = await outline_generator.generate_outline(
            novel_id=novel_id,
            premise=premise,
            genre=genre,
            tone=tone,
            num_chapters=num_chapters,
        )
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    chapters_data = outline_data.get("chapters", [])
    characters_data = outline_data.get("characters", [])
    lore_data = outline_data.get("lore", [])

    created_chapters = []
    created_characters = []
    created_lore = []

    for chapter_data in chapters_data:
        chapter = Chapter(**chapter_data)
        db.add(chapter)
        created_chapters.append(chapter)

    for char_data in characters_data:
        char_data["novel_id"] = novel_id
        character = Character(**char_data)
        db.add(character)
        created_characters.append(character)

    for lore_item in lore_data:
        lore_item["novel_id"] = novel_id
        lore = Lore(**lore_item)
        db.add(lore)
        created_lore.append(lore)

    await db.commit()

    for chapter in created_chapters:
        await db.refresh(chapter)
    for character in created_characters:
        await db.refresh(character)
    for lore in created_lore:
        await db.refresh(lore)

    return created_chapters
