"""数据库连接配置"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
import sqlalchemy
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///./storyweaver.db"
)

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()


async def get_db():
    """获取数据库会话"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """初始化数据库表"""
    async with engine.begin() as conn:
        # Enable WAL mode for better concurrency
        await conn.execute(sqlalchemy.text("PRAGMA journal_mode=WAL;"))
        await conn.run_sync(Base.metadata.create_all)
        # 若使用 SQLite 且表已存在，补充新列（无则忽略）
        if "sqlite" in DATABASE_URL:
            for col_sql in (
                "ALTER TABLE characters ADD COLUMN portrait_url VARCHAR(512)",
                "ALTER TABLE scenes ADD COLUMN video_task_id VARCHAR(128)",
                "ALTER TABLE scenes ADD COLUMN video_url VARCHAR(512)",
                "ALTER TABLE scenes ADD COLUMN video_prompt TEXT",
            ):
                try:
                    await conn.execute(sqlalchemy.text(col_sql))
                except Exception:
                    pass
