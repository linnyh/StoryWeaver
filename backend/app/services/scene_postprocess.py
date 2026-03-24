"""Scene post-processing services."""
from sqlalchemy import and_, select

from app.database import AsyncSessionLocal
from app.logging import get_logger
from app.models import Chapter, Character, Novel, Relationship, Scene
from app.rag import rag_service
from app.services import relationship_analyzer, state_analyzer, summarizer

logger = get_logger(__name__)


async def analyze_state_and_relationships(scene_id: str) -> None:
    """Analyze character state and relationship updates for a scene."""
    logger.info("Start state/relationship analysis for scene=%s", scene_id)
    async with AsyncSessionLocal() as db:
        try:
            stmt = (
                select(Scene, Chapter, Novel)
                .join(Chapter, Scene.chapter_id == Chapter.id)
                .join(Novel, Chapter.novel_id == Novel.id)
                .where(Scene.id == scene_id)
            )
            result = await db.execute(stmt)
            row = result.first()
            if not row:
                logger.warning("Scene not found in postprocess scene=%s", scene_id)
                return

            scene, _, novel = row
            if not scene.content or not scene.characters_present:
                logger.info("Skip analysis due to missing content/characters scene=%s", scene_id)
                return

            characters = []
            for char_id in scene.characters_present:
                char_result = await db.execute(select(Character).where(Character.id == char_id))
                character = char_result.scalar_one_or_none()
                if not character:
                    continue

                characters.append(character)
                new_state = await state_analyzer.analyze_state(
                    character,
                    scene.content,
                    genre=novel.genre or "玄幻",
                )
                if new_state:
                    character.power_state = new_state
                    db.add(character)

            if len(characters) >= 2:
                char_ids = [c.id for c in characters]
                rel_stmt = select(Relationship).where(
                    and_(
                        Relationship.character_a_id.in_(char_ids),
                        Relationship.character_b_id.in_(char_ids),
                    )
                )
                rels_result = await db.execute(rel_stmt)
                existing_rels = rels_result.scalars().all()
                rels_map = {f"{rel.character_a_id}:{rel.character_b_id}": rel for rel in existing_rels}

                updates = await relationship_analyzer.analyze_relationships(
                    scene.content,
                    characters,
                    rels_map,
                )

                for update in updates:
                    id_a, id_b = sorted([update["char_a_id"], update["char_b_id"]])
                    key = f"{id_a}:{id_b}"
                    rel = rels_map.get(key)
                    if not rel:
                        rel = Relationship(
                            novel_id=novel.id,
                            character_a_id=id_a,
                            character_b_id=id_b,
                            affinity_score=0,
                        )
                        db.add(rel)

                    change = update.get("affinity_change", 0)
                    if change:
                        rel.affinity_score = max(-100, min(100, rel.affinity_score + change))
                    if update.get("new_conflict"):
                        rel.core_conflict = update["new_conflict"]

            await db.commit()
            logger.info("Finish state/relationship analysis scene=%s", scene_id)
        except Exception:
            logger.exception("State/relationship analysis failed scene=%s", scene_id)


async def summarize_scene(scene_id: str) -> None:
    """Generate a scene summary and sync it into RAG."""
    logger.info("Start summarize scene=%s", scene_id)
    async with AsyncSessionLocal() as db:
        try:
            stmt = (
                select(Scene, Chapter)
                .join(Chapter, Scene.chapter_id == Chapter.id)
                .where(Scene.id == scene_id)
            )
            result = await db.execute(stmt)
            row = result.first()
            if not row:
                logger.warning("Scene not found for summarize scene=%s", scene_id)
                return

            scene, chapter = row
            if not scene.content:
                logger.info("Skip summarize due to empty content scene=%s", scene_id)
                return

            summary = await summarizer.generate_summary(scene.content)
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
            logger.info("Finish summarize scene=%s", scene_id)
        except Exception:
            logger.exception("Summarize failed scene=%s", scene_id)


async def update_scene_summary_in_rag(scene_id: str, summary: str) -> None:
    """Update RAG summary for a scene with caller-provided summary text."""
    logger.info("Start RAG summary update scene=%s", scene_id)
    async with AsyncSessionLocal() as db:
        try:
            stmt = (
                select(Scene, Chapter)
                .join(Chapter, Scene.chapter_id == Chapter.id)
                .where(Scene.id == scene_id)
            )
            result = await db.execute(stmt)
            row = result.first()
            if not row:
                logger.warning("Scene not found for RAG update scene=%s", scene_id)
                return

            _, chapter = row
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
            logger.info("Finish RAG summary update scene=%s", scene_id)
        except Exception:
            logger.exception("RAG summary update failed scene=%s", scene_id)
