import asyncio
import uuid
from app.database import get_db, init_db, engine
from app.models import Character, Novel, Relationship
from app.services import relationship_analyzer
from sqlalchemy import select, delete

async def test_relationship_flow():
    # 1. Init DB
    await init_db()
    
    async with engine.begin() as conn:
        # Clean up test data
        await conn.execute(delete(Relationship))
        await conn.execute(delete(Character).where(Character.name.in_(['TestCharA', 'TestCharB'])))
        await conn.execute(delete(Novel).where(Novel.title == 'Relationship Test Novel'))

    # 2. Create Test Data
    print("Creating test data...")
    db_gen = get_db()
    db = await anext(db_gen)
    
    try:
        novel = Novel(id=str(uuid.uuid4()), title="Relationship Test Novel", premise="Test Premise")
        db.add(novel)
        
        char_a = Character(id=str(uuid.uuid4()), novel_id=novel.id, name="TestCharA", bio="A brave warrior", personality="Brave")
        char_b = Character(id=str(uuid.uuid4()), novel_id=novel.id, name="TestCharB", bio="A cunning mage", personality="Cunning")
        db.add(char_a)
        db.add(char_b)
        await db.commit()
        
        # 3. Simulate Analysis (Scenario 1: Conflict)
        print("\n--- Scenario 1: Conflict ---")
        content_conflict = """
        TestCharA 愤怒地看着 TestCharB："你为什么要背叛我？"
        TestCharB 冷笑一声，手中的魔杖闪烁着危险的光芒："为了力量，这点牺牲算什么？"
        两人之间的气氛剑拔弩张，TestCharA 握紧了手中的剑，心中的信任瞬间崩塌。
        """
        
        updates = await relationship_analyzer.analyze_relationships(content_conflict, [char_a, char_b], {})
        print(f"Analysis Result: {updates}")
        
        # Apply updates manually to simulate background task
        if updates:
            for update in updates:
                # 确保顺序
                id_a = update["char_a_id"]
                id_b = update["char_b_id"]
                id_a, id_b = sorted([id_a, id_b])
                
                rel = Relationship(
                    novel_id=novel.id,
                    character_a_id=id_a, 
                    character_b_id=id_b,
                    affinity_score=update.get('affinity_change', 0),
                    core_conflict=update.get('new_conflict')
                )
                db.add(rel)
            await db.commit()
            
            # Check DB
            stmt = select(Relationship).where(Relationship.novel_id == novel.id)
            rel = (await db.execute(stmt)).scalar_one()
            print(f"DB State after conflict: Affinity={rel.affinity_score}, Conflict={rel.core_conflict}")
            
            # 4. Simulate Analysis (Scenario 2: Reconciliation)
            print("\n--- Scenario 2: Reconciliation ---")
            content_reconcile = """
            TestCharB 倒在地上，奄奄一息："其实...我是为了保护你才故意这么做的..."
            TestCharA 愣住了，眼中的怒火消散，取而代之的是震惊与愧疚。他连忙扶起 TestCharB，递上一瓶治疗药水。
            "对不起，我误会你了。" TestCharA 低声说道。
            """
            
            # Mock existing relationship map
            rels_map = {f"{min(char_a.id, char_b.id)}:{max(char_a.id, char_b.id)}": rel}
            
            updates_2 = await relationship_analyzer.analyze_relationships(content_reconcile, [char_a, char_b], rels_map)
            print(f"Analysis Result: {updates_2}")
            
            # Apply updates
            for update in updates_2:
                 change = update.get("affinity_change", 0)
                 rel.affinity_score += change
                 if update.get("new_conflict"):
                     rel.core_conflict = update["new_conflict"]
            await db.commit()
            
            print(f"DB State after reconcile: Affinity={rel.affinity_score}, Conflict={rel.core_conflict}")
        else:
             print("No updates generated, skipping DB check.")

    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(test_relationship_flow())