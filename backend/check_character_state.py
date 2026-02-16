import asyncio
from app.database import get_db
from app.models import Character
from sqlalchemy import select

async def check_character_state():
    db_gen = get_db()
    db = await anext(db_gen)
    try:
        # Check Characters
        chars_res = await db.execute(select(Character))
        chars = chars_res.scalars().all()
        print(f"Characters count: {len(chars)}")
        for char in chars:
            print(f"  - {char.name}")
            print(f"    Power State: {char.power_state}")
            if char.power_state:
                print(f"    Realm: {char.power_state.get('realm')}")
            print("-" * 20)
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(check_character_state())