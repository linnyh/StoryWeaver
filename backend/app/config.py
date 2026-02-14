"""配置管理"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


def load_env():
    """手动加载 .env 文件"""
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key] = value


# 先加载环境变量
load_env()


class Settings(BaseSettings):
    """应用配置"""

    # 数据库
    database_url: str = "sqlite+aiosqlite:///./storyweaver.db"

    # LLM 配置 - 使用 env 关键字直接指定环境变量名
    openai_api_key: Optional[str] = None
    openai_base_url: Optional[str] = None
    openai_model: Optional[str] = None

    # MiniMax 配置 (可选)
    minimax_api_key: Optional[str] = None
    minimax_base_url: Optional[str] = None

    # Embedding 模型
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # ChromaDB 配置
    chromadb_persist_directory: str = "./chroma_data"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"

    def model_post_init(self, __context):
        # 手动从环境变量覆盖
        if os.getenv("MODEL"):
            self.openai_model = os.getenv("MODEL")
        if not self.openai_model:
            self.openai_model = "abab6.5s-chat"


settings = Settings()
