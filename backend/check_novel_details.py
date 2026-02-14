import asyncio
from app.database import get_db
from app.models import Novel, Chapter, Character, Lore
from sqlalchemy import select
from uuid import UUID

async def check_novel_details():
    db_gen = get_db()
    db = await anext(db_gen)
    try:
        novel_id_str = "902b171e-a5d0-4e7d-a916-428d86721aa0"
        
        # Check Novel
        result = await db.execute(select(Novel).where(Novel.id == novel_id_str))
        novel = result.scalar_one_or_none()
        
        if novel:
            print(f"Novel found: {novel.title}")
            print(f"ID: {novel.id}")
            
            # Check Chapters
            chapters_res = await db.execute(select(Chapter).where(Chapter.novel_id == novel_id_str))
            chapters = chapters_res.scalars().all()
            print(f"Chapters count: {len(chapters)}")
            for ch in chapters:
                print(f"  - {ch.title} (Index: {ch.order_index})")
                
            # Check Characters
            chars_res = await db.execute(select(Character).where(Character.novel_id == novel_id_str))
            chars = chars_res.scalars().all()
            print(f"Characters count: {len(chars)}")
            
            # Check Lore
            lore_res = await db.execute(select(Lore).where(Lore.novel_id == novel_id_str))
            lores = lore_res.scalars().all()
            print(f"Lore count: {len(lores)}")
            
        else:
            print("Novel not found in database.")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(check_novel_details())
