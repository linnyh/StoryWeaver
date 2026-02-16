import asyncio
from app.database import AsyncSessionLocal
from app.models import Scene, Character, Relationship
from sqlalchemy import select, desc
from app.services.relationship_analyzer import analyze_relationships

async def debug_latest_scene():
    async with AsyncSessionLocal() as db:
        # 1. Find the target scene directly
        target_scene_id = "b2d110b1-849c-42a2-8a1f-0b607ca89e05"
        scene = await db.get(Scene, target_scene_id)
        
        if not scene:
            print("Target scene not found.")
            return
            
        print(f"\n=== Latest Scene Debug ===")
        print(f"ID: {scene.id}")
        # print(f"Updated At: {scene.updated_at}") # Field does not exist
        print(f"Characters Present (DB): {scene.characters_present}")
        
        if not scene.content:
            print("No content in scene.")
            return

        print(f"Content Preview: {scene.content[:100]}...")
        
        # 2. Check Characters
        characters = []
        if scene.characters_present:
            for char_id in scene.characters_present:
                char = await db.get(Character, char_id)
                if char:
                    characters.append(char)
                    print(f"  - Found Character: {char.name} ({char.id})")
                else:
                    print(f"  - ERROR: Character ID {char_id} not found in DB")
        else:
            print("  - NO characters_present set!")
            
        if len(characters) < 2:
            print("  -> Insufficient characters for relationship analysis.")
            return

        # 3. Check Existing Relationships
        print("\n=== Existing Relationships ===")
        existing_relationships = {}
        # Get all relationships for this novel
        from app.models import Chapter
        chapter = await db.get(Chapter, scene.chapter_id)
        novel_id = chapter.novel_id
        
        stmt = select(Relationship).where(Relationship.novel_id == novel_id)
        rels = (await db.execute(stmt)).scalars().all()
        
        for r in rels:
             key = f"{min(r.character_a_id, r.character_b_id)}:{max(r.character_a_id, r.character_b_id)}"
             existing_relationships[key] = r
             print(f"  - {key}: Score {r.affinity_score}")

        # 4. Run Analyzer Manually
        print("\n=== Running Analyzer ===")
        try:
            updates = await analyze_relationships(scene.content, characters, existing_relationships)
            print(f"Analysis Result (Updates): {updates}")
        except Exception as e:
            print(f"Analyzer Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_latest_scene())