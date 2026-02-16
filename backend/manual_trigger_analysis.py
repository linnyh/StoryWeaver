import asyncio
from app.database import AsyncSessionLocal
from app.models import Scene, Character
from app.api.scene import background_analyze_state
from sqlalchemy import select

async def trigger_analysis(scene_id):
    print(f"Manually triggering analysis for scene {scene_id}...")
    await background_analyze_state(scene_id)
    print("Analysis complete.")

if __name__ == "__main__":
    # Use the scene ID from the debug output that has multiple characters
    # Scene ID: b2d110b1-849c-42a2-8a1f-0b607ca89e05
    # Characters Present (Raw): ['韩立', '小绿', '赵灵儿']
    # NOTE: The debug output showed "Character NOT Found" for these names because they are names, not IDs.
    # We need to fix the database to store IDs instead of names, or update the analysis logic to handle names.
    
    # BUT FIRST, let's try to fix the data in the database for this specific scene to use IDs.
    
    scene_id = "b2d110b1-849c-42a2-8a1f-0b607ca89e05"
    
    async def fix_and_trigger():
        async with AsyncSessionLocal() as db:
            # 1. Get the scene
            scene = await db.get(Scene, scene_id)
            if not scene:
                print("Scene not found!")
                return

            print(f"Original characters_present: {scene.characters_present}")
            
            # 2. Resolve names to IDs
            char_names = ['韩立', '小绿', '赵灵儿']
            char_ids = []
            
            # Need to get novel_id first
            from app.models import Chapter
            # scene.chapter might not be loaded if lazy loading is default, let's query it
            chapter_id = scene.chapter_id
            chapter = await db.get(Chapter, chapter_id)
            novel_id = chapter.novel_id
            
            print(f"Novel ID: {novel_id}")
            
            stmt = select(Character).where(Character.novel_id == novel_id).where(Character.name.in_(char_names))
            chars = (await db.execute(stmt)).scalars().all()
            
            found_names = []
            for char in chars:
                print(f"Resolved {char.name} -> {char.id}")
                char_ids.append(char.id)
                found_names.append(char.name)
            
            missing = set(char_names) - set(found_names)
            if missing:
                print(f"Warning: Could not find IDs for: {missing}")
            
            # 3. Update scene with IDs
            if char_ids:
                scene.characters_present = char_ids
                await db.commit()
                print(f"Updated scene characters_present to IDs: {char_ids}")
            else:
                print("No character IDs found, cannot update.")
                return

        # 4. Trigger analysis
        await background_analyze_state(scene_id)

    asyncio.run(fix_and_trigger())