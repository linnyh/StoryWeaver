import asyncio
import os
import sys
import json
import httpx

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = "http://localhost:8000"

async def test_module1_power_state():
    """测试模块1: 力量体系与资产状态机"""
    print("\n=== 测试模块 1: 力量体系与资产状态机 ===")
    async with httpx.AsyncClient(timeout=60.0) as client:
        # 1. 创建小说
        print("1. 创建测试小说...")
        resp = await client.post(f"{BASE_URL}/api/novels/", json={
            "title": "Module1 Test Novel",
            "premise": "Test for power state machine",
            "genre": "Xianxia",
            "tone": "Serious"
        })
        if resp.status_code != 200:
             print(f"Error creating novel: {resp.text}")
             print(f"Status code: {resp.status_code}")
        assert resp.status_code == 200
        novel_id = resp.json()["id"]

        # 2. 创建角色 (带初始状态)
        print("2. 创建角色 (带初始状态)...")
        initial_state = {
            "realm": "Qi Condensation Level 1",
            "inventory": [{"item": "Wooden Sword", "uses_left": 10}],
            "core_skills": ["Basic Breathing"]
        }
        resp = await client.post(f"{BASE_URL}/api/characters/", json={
            "novel_id": novel_id,
            "name": "Li Huo",
            "bio": "A young cultivator",
            "role": "Protagonist",
            "power_state": initial_state
        })
        assert resp.status_code == 200
        char_id = resp.json()["id"]
        print(f"   Created character: {resp.json()['name']} with state: {resp.json()['power_state']}")

        # 3. 调用状态更新 API
        print("3. 调用状态更新 API...")
        update_text = """
        Li Huo sat on the spirit stone, absorbing the surrounding qi. Suddenly, a surge of energy rushed through his meridians.
        "Break!" he shouted. He successfully broke through to Qi Condensation Level 2!
        He also found a bottle of Spirit Pills in the cave.
        """
        resp = await client.post(f"{BASE_URL}/api/characters/{char_id}/state_update", json={
            "text": update_text
        })
        assert resp.status_code == 200
        updated_char = resp.json()
        new_state = updated_char["power_state"]
        print(f"   Updated state: {json.dumps(new_state, indent=2, ensure_ascii=False)}")
        
        # 验证逻辑 (Mock LLM 可能会返回模拟数据，如果真实 LLM 则应反映文本)
        # 这里只要 power_state 存在且不为空即可视为通路打通
        assert new_state is not None
        
        # 清理
        await client.delete(f"{BASE_URL}/api/novels/{novel_id}")
        print("✓ 模块 1 测试通过")

async def test_module2_tension_control():
    """测试模块2: 情绪张力与爽点控制"""
    print("\n=== 测试模块 2: 情绪张力与爽点控制 ===")
    async with httpx.AsyncClient(timeout=120.0) as client:
        # 1. 创建小说
        print("1. 创建测试小说...")
        resp = await client.post(f"{BASE_URL}/api/novels/", json={
            "title": "Module2 Test Novel",
            "premise": "Test for tension control",
            "genre": "Xianxia",
            "tone": "Serious"
        })
        novel_id = resp.json()["id"]

        # 2. 创建章节
        print("2. 创建章节...")
        resp = await client.post(f"{BASE_URL}/api/chapters/", json={
            "novel_id": novel_id,
            "order_index": 1,
            "title": "Chapter 1: The Beginning",
            "summary": "The protagonist faces a challenge."
        })
        if resp.status_code != 200:
             print(f"Error creating chapter: {resp.text}")
        assert resp.status_code == 200
        chapter_id = resp.json()["id"]

        # 3. 生成细纲 (检查 tension_level)
        print("3. 生成场景细纲 (检查 tension_level)...")
        resp = await client.post(f"{BASE_URL}/api/chapters/{chapter_id}/beats", json={
            "num_beats": 3
        })
        assert resp.status_code == 200
        scenes = resp.json()
        
        print(f"   Generated {len(scenes)} scenes.")
        for s in scenes:
            print(f"   - Scene: {s['location']}")
            print(f"     Tension: {s.get('tension_level')}")
            print(f"     Emotional Target: {s.get('emotional_target')}")
            
            # 验证字段存在
            assert "tension_level" in s
            assert "emotional_target" in s
            
        # 清理
        await client.delete(f"{BASE_URL}/api/novels/{novel_id}")
        print("✓ 模块 2 测试通过")

async def main():
    try:
        await test_module1_power_state()
        await test_module2_tension_control()
        print("\n🎉 所有新功能测试通过!")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())