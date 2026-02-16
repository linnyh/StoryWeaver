import asyncio
from app.database import AsyncSessionLocal
from sqlalchemy import select
from app.models import Scene, Character

async def check_scene_characters():
    async with AsyncSessionLocal() as db:
        # Find scenes with content but check their characters_present field
        stmt = select(Scene).where(Scene.content.is_not(None))
        scenes = (await db.execute(stmt)).scalars().all()
        
        print(f"Found {len(scenes)} scenes with content.")
        
        for scene in scenes:
            print(f"\nScene ID: {scene.id}")
            print(f"Content Preview: {scene.content[:50]}...")
            print(f"Characters Present (Raw): {scene.characters_present}")
            
            if scene.characters_present:
                # Verify these IDs exist
                for char_id in scene.characters_present:
                    char = await db.get(Character, char_id)
                    if char:
                        print(f"  - Character Found: {char.name} ({char.id})")
                    else:
                        print(f"  - Character NOT Found: {char_id}")
            else:
                print("  - NO characters_present set!")

if __name__ == "__main__":
    asyncio.run(check_scene_characters())