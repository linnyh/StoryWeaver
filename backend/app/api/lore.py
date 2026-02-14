"""Lore API - 世界观设定"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.models import Lore

router = APIRouter()


class LoreBase(BaseModel):
    novel_id: str
    title: str
    content: str
    category: Optional[str] = None


class LoreCreate(LoreBase):
    pass


class LoreResponse(LoreBase):
    id: str

    class Config:
        from_attributes = True


@router.post("/", response_model=LoreResponse)
async def create_lore(lore: LoreCreate, db: AsyncSession = Depends(get_db)):
    """添加世界观设定"""
    db_lore = Lore(**lore.model_dump())
    db.add(db_lore)
    await db.commit()
    await db.refresh(db_lore)
    return db_lore


@router.get("/", response_model=list[LoreResponse])
async def list_lores(novel_id: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    """列出世界观设定"""
    query = select(Lore)
    if novel_id:
        query = query.where(Lore.novel_id == novel_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{lore_id}", response_model=LoreResponse)
async def get_lore(lore_id: str, db: AsyncSession = Depends(get_db)):
    """获取世界观设定详情"""
    result = await db.execute(select(Lore).where(Lore.id == lore_id))
    lore = result.scalar_one_or_none()
    if not lore:
        raise HTTPException(status_code=404, detail="Lore not found")
    return lore


@router.delete("/{lore_id}")
async def delete_lore(lore_id: str, db: AsyncSession = Depends(get_db)):
    """删除世界观设定"""
    result = await db.execute(select(Lore).where(Lore.id == lore_id))
    lore = result.scalar_one_or_none()
    if not lore:
        raise HTTPException(status_code=404, detail="Lore not found")
    await db.delete(lore)
    await db.commit()
    return {"message": "Lore deleted"}
