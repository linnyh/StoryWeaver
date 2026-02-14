import asyncio
from app.database import get_db
from app.models import Novel
from sqlalchemy import select
from uuid import UUID

async def check_novel():
    db_gen = get_db()
    db = await anext(db_gen)
    try:
        novel_id = UUID("902b171e-a5d0-4e7d-a916-428d86721aa0")
        result = await db.execute(select(Novel).where(Novel.id == novel_id))
        novel = result.scalar_one_or_none()
        
        if novel:
            print(f"Novel found: {novel.title}")
            print(f"ID: {novel.id}")
            print(f"Premise: {novel.premise}")
        else:
            print("Novel not found in database.")
            
        # Also list all novels to be sure
        result_all = await db.execute(select(Novel))
        novels = result_all.scalars().all()
        print(f"\nTotal novels in DB: {len(novels)}")
        for n in novels:
            print(f"- {n.title} ({n.id})")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(check_novel())
