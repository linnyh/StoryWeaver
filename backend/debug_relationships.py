import asyncio
from app.database import AsyncSessionLocal
from sqlalchemy import select
from app.models import Relationship, Character, Novel

async def check_data():
    async with AsyncSessionLocal() as db:
        print("\n--- Novels ---")
        novels = (await db.execute(select(Novel))).scalars().all()
        for n in novels:
            print(f"ID: {n.id}, Title: {n.title}")
            
        print("\n--- Characters ---")
        chars = (await db.execute(select(Character))).scalars().all()
        for c in chars:
            print(f"ID: {c.id}, Name: {c.name}, Novel: {c.novel_id}")
            
        print("\n--- Relationships ---")
        rels = (await db.execute(select(Relationship))).scalars().all()
        for r in rels:
            print(f"ID: {r.id}, Novel: {r.novel_id}, A: {r.character_a_id}, B: {r.character_b_id}, Score: {r.affinity_score}")

if __name__ == "__main__":
    asyncio.run(check_data())