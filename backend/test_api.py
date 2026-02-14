"""API 测试脚本 - 使用 httpx 进行异步测试"""
import asyncio
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx


BASE_URL = "http://localhost:8000"


async def test_health():
    """测试健康检查"""
    print("\n=== 测试健康检查 ===")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        assert response.status_code == 200
    print("✓ 健康检查通过")


async def test_crud_apis():
    """测试 CRUD API"""
    print("\n=== 测试 CRUD API ===")
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. 创建小说
        response = await client.post(
            f"{BASE_URL}/api/novels/",
            json={
                "title": "测试小说API",
                "premise": "一个关于成长的奇幻故事",
                "genre": "玄幻",
                "tone": "严肃"
            }
        )
        print(f"创建小说状态码: {response.status_code}")
        print(f"响应内容: {response.text[:200]}")
        assert response.status_code == 200
        novel = response.json()
        novel_id = novel["id"]
        print(f"✓ 创建小说: {novel['title']} (ID: {novel_id})")

        # 2. 获取小说列表
        response = await client.get(f"{BASE_URL}/api/novels/")
        assert response.status_code == 200
        novels = response.json()
        print(f"✓ 小说列表: {len(novels)} 本")

        # 3. 获取单个小说
        response = await client.get(f"{BASE_URL}/api/novels/{novel_id}")
        assert response.status_code == 200
        print(f"✓ 获取小说详情成功")

        # 4. 创建角色
        response = await client.post(
            f"{BASE_URL}/api/characters/",
            json={
                "novel_id": novel_id,
                "name": "林轩",
                "bio": "主角，出身山村的天才少年",
                "personality": "坚毅、果敢",
                "appearance": "剑眉星目",
                "role": "主角"
            }
        )
        assert response.status_code == 200
        character = response.json()
        character_id = character["id"]
        print(f"✓ 创建角色: {character['name']} (ID: {character_id})")

        # 5. 获取角色列表
        response = await client.get(
            f"{BASE_URL}/api/characters/",
            params={"novel_id": novel_id}
        )
        assert response.status_code == 200
        characters = response.json()
        print(f"✓ 角色列表: {len(characters)} 个")

        # 6. 创建章节
        response = await client.post(
            f"{BASE_URL}/api/chapters/",
            json={
                "novel_id": novel_id,
                "order_index": 1,
                "title": "第1章 少年出山",
                "summary": "主角离开山村"
            }
        )
        assert response.status_code == 200
        chapter = response.json()
        chapter_id = chapter["id"]
        print(f"✓ 创建章节: {chapter['title']} (ID: {chapter_id})")

        # 7. 获取章节列表
        response = await client.get(
            f"{BASE_URL}/api/chapters/",
            params={"novel_id": novel_id}
        )
        assert response.status_code == 200
        chapters = response.json()
        print(f"✓ 章节列表: {len(chapters)} 章")

        # 8. 创建场景
        response = await client.post(
            f"{BASE_URL}/api/scenes/",
            json={
                "chapter_id": chapter_id,
                "order_index": 1,
                "location": "山村外",
                "characters_present": [character_id],
                "beat_description": "主角离开山村",
                "status": "draft"
            }
        )
        assert response.status_code == 200
        scene = response.json()
        scene_id = scene["id"]
        print(f"✓ 创建场景: {scene['location']} (ID: {scene_id})")

        # 9. 获取场景列表
        response = await client.get(
            f"{BASE_URL}/api/scenes/",
            params={"chapter_id": chapter_id}
        )
        assert response.status_code == 200
        scenes = response.json()
        print(f"✓ 场景列表: {len(scenes)} 个场景")

        # 10. 更新场景内容
        response = await client.put(
            f"{BASE_URL}/api/scenes/{scene_id}",
            json={
                "content": "这是测试生成的内容..."
            }
        )
        assert response.status_code == 200
        print("✓ 更新场景内容")

        # 11. 删除小说 (会级联删除)
        response = await client.delete(f"{BASE_URL}/api/novels/{novel_id}")
        assert response.status_code == 200
        print("✓ 删除小说")


async def test_outline_generation():
    """测试大纲生成 API"""
    print("\n=== 测试大纲生成 ===")
    async with httpx.AsyncClient(timeout=120.0) as client:
        # 创建小说
        response = await client.post(
            f"{BASE_URL}/api/novels/",
            json={
                "title": "大纲测试小说",
                "premise": "一个少年成为强者的故事",
                "genre": "玄幻",
                "tone": "热血"
            }
        )
        novel = response.json()
        novel_id = novel["id"]
        print(f"创建小说: {novel['title']}")

        # 生成大纲
        response = await client.post(
            f"{BASE_URL}/api/novels/{novel_id}/outline",
            json={
                "premise": "一个少年成为强者的故事",
                "genre": "玄幻",
                "tone": "热血",
                "num_chapters": 5
            }
        )
        assert response.status_code == 200
        chapters = response.json()
        print(f"✓ 生成大纲: {len(chapters)} 个章节")

        for ch in chapters[:3]:
            print(f"  - {ch['title']}")

        # 清理
        await client.delete(f"{BASE_URL}/api/novels/{novel_id}")


async def main():
    """运行所有 API 测试"""
    print("=" * 50)
    print("StoryWeaver API 测试")
    print("=" * 50)

    # 先启动服务器 (需要先运行 uvicorn app.main:app)

    try:
        await test_health()
        await test_crud_apis()
        await test_outline_generation()

        print("\n" + "=" * 50)
        print("🎉 所有 API 测试通过!")
        print("=" * 50)

    except httpx.ConnectError:
        print("\n❌ 无法连接到服务器")
        print("请先启动后端服务: uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
