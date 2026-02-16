import asyncio
import random
from app.database import AsyncSessionLocal
from sqlalchemy import select
from app.models import Relationship, Character, Novel

async def populate_dummy_relationships(novel_id):
    async with AsyncSessionLocal() as db:
        print(f"Checking characters for novel {novel_id}...")
        
        # 1. Get Characters
        stmt = select(Character).where(Character.novel_id == novel_id)
        chars = (await db.execute(stmt)).scalars().all()
        
        if len(chars) < 2:
            print("Not enough characters to create relationships.")
            return

        print(f"Found {len(chars)} characters. Creating relationships...")
        
        relationships_created = 0
        
        # 2. Create Random Relationships
        # Create a connected graph (cycle) + some random edges
        char_ids = [c.id for c in chars]
        
        pairs = []
        # Cycle
        for i in range(len(char_ids)):
            pairs.append((char_ids[i], char_ids[(i + 1) % len(char_ids)]))
            
        # Random extra edges
        for _ in range(len(char_ids)): # Add N more random edges
            a = random.choice(char_ids)
            b = random.choice(char_ids)
            if a != b and (a, b) not in pairs and (b, a) not in pairs:
                pairs.append((a, b))
                
        for id_a, id_b in pairs:
            # Check existing
            # Ensure order
            id_a, id_b = sorted([id_a, id_b])
            
            stmt = select(Relationship).where(
                Relationship.character_a_id == id_a, 
                Relationship.character_b_id == id_b
            )
            existing = (await db.execute(stmt)).scalar_one_or_none()
            
            if not existing:
                affinity = random.randint(-80, 80)
                conflict = None
                
                if affinity > 60:
                    conflict = random.choice(["生死之交", "青梅竹马", "并肩作战的战友", "互相暗恋"])
                elif affinity > 20:
                    conflict = random.choice(["互相欣赏", "利益共同体", "点头之交"])
                elif affinity < -60:
                    conflict = random.choice(["杀父之仇", "夺妻之恨", "宿命之敌", "理念不合"])
                elif affinity < -20:
                    conflict = random.choice(["互相看不顺眼", "竞争对手", "曾经的盟友"])
                else:
                    conflict = "萍水相逢"

                rel = Relationship(
                    novel_id=novel_id,
                    character_a_id=id_a,
                    character_b_id=id_b,
                    affinity_score=affinity,
                    core_conflict=conflict
                )
                db.add(rel)
                relationships_created += 1
                
        await db.commit()
        print(f"Successfully created {relationships_created} relationships.")

if __name__ == "__main__":
    # Novel ID for "Module2 Test Novel" (from previous debug output)
    target_novel_id = "2faf31d7-a564-44bc-acaa-8f5209b72ad9" 
    asyncio.run(populate_dummy_relationships(target_novel_id))