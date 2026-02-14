from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, Dict

from app.database import get_db
from app.models.system import SystemConfig
from app.config import settings as env_settings
from app.services.generator import llm_client

router = APIRouter()

class LLMConfig(BaseModel):
    openai_api_key: Optional[str] = None
    openai_base_url: Optional[str] = None
    openai_model: Optional[str] = None

@router.get("/llm", response_model=LLMConfig)
async def get_llm_config(db: AsyncSession = Depends(get_db)):
    """获取 LLM 配置"""
    # 优先从数据库读取
    stmt = select(SystemConfig).where(SystemConfig.key.in_([
        "openai_api_key", "openai_base_url", "openai_model"
    ]))
    result = await db.execute(stmt)
    configs = {row.key: row.value for row in result.scalars().all()}
    
    return LLMConfig(
        openai_api_key=configs.get("openai_api_key") or env_settings.openai_api_key,
        openai_base_url=configs.get("openai_base_url") or env_settings.openai_base_url,
        openai_model=configs.get("openai_model") or env_settings.openai_model
    )

@router.post("/llm")
async def update_llm_config(config: LLMConfig, db: AsyncSession = Depends(get_db)):
    """更新 LLM 配置"""
    keys = {
        "openai_api_key": config.openai_api_key,
        "openai_base_url": config.openai_base_url,
        "openai_model": config.openai_model
    }
    
    for key, value in keys.items():
        if value is not None:
            # 检查是否存在
            stmt = select(SystemConfig).where(SystemConfig.key == key)
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if existing:
                existing.value = value
            else:
                new_config = SystemConfig(key=key, value=value)
                db.add(new_config)
    
    await db.commit()
    
    # 触发 LLM Client 更新配置
    await llm_client.refresh_config(db)
    
    return {"status": "success"}
