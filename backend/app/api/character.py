"""Character API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from app.database import get_db
from app.models import Character
from app.services import state_analyzer

router = APIRouter()


class CharacterCreate(BaseModel):
    novel_id: str
    name: str
    bio: Optional[str] = None
    personality: Optional[str] = None
    appearance: Optional[str] = None
    role: Optional[str] = None
    power_state: Optional[Dict[str, Any]] = None


class CharacterUpdate(BaseModel):
    name: Optional[str] = None
    bio: Optional[str] = None
    personality: Optional[str] = None
    appearance: Optional[str] = None
    role: Optional[str] = None
    power_state: Optional[Dict[str, Any]] = None


class CharacterResponse(BaseModel):
    id: str
    novel_id: str
    name: str
    bio: Optional[str]
    personality: Optional[str]
    appearance: Optional[str]
    role: Optional[str]
    power_state: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True


class StateUpdateRequest(BaseModel):
    text: str


@router.post("/{character_id}/state_update", response_model=CharacterResponse)
async def update_character_state(
    character_id: str,
    request: StateUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """根据文本内容自动更新角色状态"""
    result = await db.execute(select(Character).where(Character.id == character_id))
    character = result.scalar_one_or_none()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    # 调用 LLM 分析状态
    new_state = await state_analyzer.analyze_state(character, request.text)
    
    # 更新数据库
    # 注意：这里我们做的是增量更新还是全量覆盖？
    # 假设 LLM 返回的是完整的 state，或者我们需要合并。
    # 简单起见，假设 LLM 返回完整的 updated state。
    
    if new_state:
        character.power_state = new_state
        await db.commit()
        await db.refresh(character)
        
    return character



@router.post("/", response_model=CharacterResponse)
async def create_character(
    character: CharacterCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建角色"""
    db_character = Character(**character.model_dump())
    db.add(db_character)
    await db.commit()
    await db.refresh(db_character)
    return db_character


@router.get("/", response_model=list[CharacterResponse])
async def list_characters(
    novel_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """列出角色"""
    query = select(Character)
    if novel_id:
        query = query.where(Character.novel_id == novel_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{character_id}", response_model=CharacterResponse)
async def get_character(character_id: str, db: AsyncSession = Depends(get_db)):
    """获取角色详情"""
    result = await db.execute(select(Character).where(Character.id == character_id))
    character = result.scalar_one_or_none()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return character


@router.put("/{character_id}", response_model=CharacterResponse)
async def update_character(
    character_id: str,
    character: CharacterUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新角色"""
    result = await db.execute(select(Character).where(Character.id == character_id))
    db_character = result.scalar_one_or_none()
    if not db_character:
        raise HTTPException(status_code=404, detail="Character not found")

    for key, value in character.model_dump(exclude_unset=True).items():
        setattr(db_character, key, value)

    await db.commit()
    await db.refresh(db_character)
    return db_character


@router.delete("/{character_id}")
async def delete_character(character_id: str, db: AsyncSession = Depends(get_db)):
    """删除角色"""
    result = await db.execute(select(Character).where(Character.id == character_id))
    character = result.scalar_one_or_none()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    await db.delete(character)
    await db.commit()
    return {"message": "Character deleted"}
