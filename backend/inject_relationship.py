import asyncio
from app.database import AsyncSessionLocal
from app.models import Relationship
from sqlalchemy import select

async def inject_relationship_change():
    async with AsyncSessionLocal() as db:
        # We know the IDs from previous debug output
        # 韩立 (7a9593dd...) <-> 赵灵儿 (bc9e3ec9...)
        # Current: No relationship or 0
        
        char_a = "7a9593dd-fa4b-4765-97cb-e1042c4817d2"
        char_b = "bc9e3ec9-fc31-4bfc-84cb-b6580238772b"
        
        # Sort IDs
        id_a, id_b = sorted([char_a, char_b])
        
        stmt = select(Relationship).where(
            Relationship.character_a_id == id_a,
            Relationship.character_b_id == id_b
        )
        rel = (await db.execute(stmt)).scalar_one_or_none()
        
        if rel:
            print(f"Found existing relationship. Score: {rel.affinity_score}")
            rel.affinity_score += 15
            rel.core_conflict = "因赠送桂花糕而心生好感，关系迅速升温"
        else:
            print("Creating new relationship...")
            # Need novel_id. Let's assume the one from debug output
            novel_id = "2faf31d7-a564-44bc-acaa-8f5209b72ad9"
            rel = Relationship(
                novel_id=novel_id,
                character_a_id=id_a,
                character_b_id=id_b,
                affinity_score=15,
                core_conflict="因赠送桂花糕而心生好感，关系迅速升温"
            )
            db.add(rel)
            
        await db.commit()
        print(f"Injected relationship update: 韩立 <-> 赵灵儿, Score set to {rel.affinity_score}, Conflict: {rel.core_conflict}")

if __name__ == "__main__":
    asyncio.run(inject_relationship_change())