"""应用入口"""
import os

# Workaround for PermissionError when SSLKEYLOGFILE is set but not writable
# This must be done before any network/SSL libraries are imported
if "SSLKEYLOGFILE" in os.environ:
    del os.environ["SSLKEYLOGFILE"]

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import novel, character, chapter, scene, lore, settings, relationship
from app.models import Lore, SystemConfig  # 导入模型以创建数据库表
from app.database import init_db

app = FastAPI(
    title="StoryWeaver API",
    description="AI 长篇小说生成系统",
    version="0.1.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(novel.router, prefix="/api/novels", tags=["Novel"])
app.include_router(character.router, prefix="/api/characters", tags=["Character"])
app.include_router(chapter.router, prefix="/api/chapters", tags=["Chapter"])
app.include_router(scene.router, prefix="/api/scenes", tags=["Scene"])
app.include_router(lore.router, prefix="/api/lore", tags=["Lore"])
app.include_router(settings.router, prefix="/api/settings", tags=["Settings"])
app.include_router(relationship.router, prefix="/api/relationships", tags=["Relationship"])


@app.get("/")
async def root():
    return {"message": "StoryWeaver API is running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.on_event("startup")
async def startup_event():
    """应用启动时初始化数据库"""
    await init_db()
