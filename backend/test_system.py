"""测试脚本 - 验证 StoryWeaver 系统功能"""
import asyncio
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import init_db, get_db, AsyncSessionLocal
from app.models import Novel, Character, Chapter, Scene
from app.services import llm_client, outline_generator, scene_generator, summarizer


async def test_database():
    """测试数据库连接和 CRUD"""
    print("\n=== 测试 1: 数据库连接 ===")

    # 初始化数据库
    await init_db()
    print("✓ 数据库初始化成功")

    # 测试创建小说
    async with AsyncSessionLocal() as session:
        novel = Novel(
            title="测试小说",
            premise="一个关于成长的奇幻故事",
            genre="玄幻",
            tone="严肃"
        )
        session.add(novel)
        await session.commit()
        await session.refresh(novel)
        print(f"✓ 创建小说成功: {novel.id} - {novel.title}")

        # 测试创建角色
        character = Character(
            novel_id=novel.id,
            name="林轩",
            bio="主角，出身山村的天才少年",
            personality="坚毅、果敢、重情重义",
            appearance="剑眉星目，身形挺拔",
            role="主角"
        )
        session.add(character)
        await session.commit()
        await session.refresh(character)
        print(f"✓ 创建角色成功: {character.id} - {character.name}")

        # 测试创建章节
        chapter = Chapter(
            novel_id=novel.id,
            order_index=1,
            title="第1章 少年出山",
            summary="主角离开山村，开始闯荡江湖"
        )
        session.add(chapter)
        await session.commit()
        await session.refresh(chapter)
        print(f"✓ 创建章节成功: {chapter.id} - {chapter.title}")

        # 测试创建场景
        scene = Scene(
            chapter_id=chapter.id,
            order_index=1,
            location="山村外",
            characters_present=[character.id],
            beat_description="清晨，主角站在山村的石板路上，回头望了一眼生活了十六年的小屋。他深吸一口气，转身沿着唯一的一条山路走去。",
            status="draft"
        )
        session.add(scene)
        await session.commit()
        await session.refresh(scene)
        print(f"✓ 创建场景成功: {scene.id} - {scene.location}")

    return novel.id


async def test_llm_client():
    """测试 LLM 客户端"""
    print("\n=== 测试 2: LLM 客户端 ===")

    # 测试大纲生成
    prompt = "生成10章的玄幻小说大纲"
    response = await llm_client.generate(prompt)
    print(f"✓ 大纲生成响应:\n{response[:200]}...")

    return True


async def test_outline_generator(novel_id: str):
    """测试大纲生成器"""
    print("\n=== 测试 3: 大纲生成 ===")

    chapters = await outline_generator.generate_outline(
        novel_id=novel_id,
        premise="一个关于成长的奇幻故事",
        genre="玄幻",
        tone="严肃",
        num_chapters=5
    )

    print(f"✓ 生成 {len(chapters)} 个章节")
    for ch in chapters:
        print(f"  - {ch['title']}: {ch['summary'][:30]}...")

    return True


async def test_summarizer():
    """测试摘要生成器"""
    print("\n=== 测试 4: 摘要生成 ===")

    content = """
    林轩背着行囊，沿着蜿蜒的山路前行。这是他第一次离开山村，独自面对未知的世界。
    清晨的阳光洒落在山林间，鸟鸣声在耳边回荡。他回头望了一眼身后的山村，
    那里有他的母亲和熟悉的邻居。虽然心中不舍，但他知道，只有外出闯荡，
    才能找到传说中的修仙之法，成为真正的强者。
    """

    summary = await summarizer.generate_summary(content)
    print(f"✓ 生成摘要: {summary}")

    return True


async def test_rag_service():
    """测试 RAG 服务"""
    print("\n=== 测试 5: RAG 向量检索 ===")

    from app.rag import rag_service

    # 添加测试知识
    rag_service.add_knowledge(
        text="林轩是本书主角，出身青云村，性格坚毅果敢",
        doc_id="test_char_1",
        type="character",
        metadata={"novel_id": "test", "name": "林轩"}
    )

    rag_service.add_knowledge(
        text="玄元大陆是一个修仙世界，灵气充沛，万物可修",
        doc_id="test_lore_1",
        type="lore",
        metadata={"novel_id": "test"}
    )

    print("✓ 添加知识到向量数据库")

    # 检索测试
    results = rag_service.retrieve_context(
        query="主角的性格是怎样的",
        type="character",
        top_k=1
    )
    print(f"✓ 检索角色信息: {len(results)} 条结果")

    results = rag_service.retrieve_context(
        query="修仙世界设定",
        type="lore",
        top_k=1
    )
    print(f"✓ 检索世界观: {len(results)} 条结果")

    return True


async def run_all_tests():
    """运行所有测试"""
    print("=" * 50)
    print("StoryWeaver 系统测试")
    print("=" * 50)

    try:
        # 测试数据库
        novel_id = await test_database()

        # 测试 LLM
        await test_llm_client()

        # 测试大纲生成
        await test_outline_generator(novel_id)

        # 测试摘要
        await test_summarizer()

        # 测试 RAG
        await test_rag_service()

        print("\n" + "=" * 50)
        print("🎉 所有测试通过！")
        print("=" * 50)
        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
