import asyncio
from app.database import get_db
from app.models import Novel, Chapter, Character, Lore
from sqlalchemy import select
from uuid import UUID

async def check_novel_details():
    db_gen = get_db()
    db = await anext(db_gen)
    try:
        result = await db.execute(select(Novel).where(Novel.id == "902b171e-a5d0-4e7d-a916-428d86721aa0"))
        novel = result.scalar_one_or_none()
        
        if novel:
            print(f"Novel found: {novel.title}")
            
            # Check Characters
            chars_res = await db.execute(select(Character).where(Character.novel_id == novel.id))
            chars = chars_res.scalars().all()
            print(f"Characters count: {len(chars)}")
            for char in chars:
                print(f"  - {char.name}")
                print(f"    Role: {char.role}")
                print(f"    Bio: {char.bio}")
                print(f"    Personality: {char.personality}")
                print(f"    Appearance: {char.appearance}")
                print("-" * 20)
            
        else:
            print("Novel not found in database.")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(check_novel_details())
