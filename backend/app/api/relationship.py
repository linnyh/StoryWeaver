from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.models import Relationship, Character

router = APIRouter()

class CharacterSimple(BaseModel):
    id: str
    name: str
    role: Optional[str] = None
    
    class Config:
        from_attributes = True

class RelationshipResponse(BaseModel):
    id: str
    character_a_id: str
    character_b_id: str
    character_a: Optional[CharacterSimple] = None
    character_b: Optional[CharacterSimple] = None
    affinity_score: int
    core_conflict: Optional[str] = None

    class Config:
        from_attributes = True

@router.get("/", response_model=List[RelationshipResponse])
async def list_relationships(novel_id: str, db: AsyncSession = Depends(get_db)):
    """获取指定小说的所有角色关系"""
    from sqlalchemy.orm import selectinload
    # 查询关系并预加载角色
    stmt = (
        select(Relationship)
        .where(Relationship.novel_id == novel_id)
        .options(
            selectinload(Relationship.character_a),
            selectinload(Relationship.character_b)
        )
    )
    result = await db.execute(stmt)
    relationships = result.scalars().all()
    
    return relationships
