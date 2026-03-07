"""Novel API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from typing import Optional, List
from app.database import get_db
from app.models import Novel, Relationship
from app.services.novel_usecases import (
    build_novel_export_payload,
    delete_rag_summary_for_novel,
    generate_novel_outline_for_novel,
    get_rag_summaries_for_novel,
    update_rag_summary_for_novel,
)
from app.api.relationship import RelationshipResponse

router = APIRouter()


class NovelCreate(BaseModel):
    title: str
    premise: Optional[str] = None
    genre: Optional[str] = None
    tone: Optional[str] = None
    worldbuilding: Optional[str] = None
    philosophical_theme: Optional[str] = None


class NovelUpdate(BaseModel):
    title: Optional[str] = None
    premise: Optional[str] = None
    genre: Optional[str] = None
    tone: Optional[str] = None
    worldbuilding: Optional[str] = None
    philosophical_theme: Optional[str] = None


class NovelResponse(BaseModel):
    id: str
    title: str
    premise: Optional[str]
    genre: Optional[str]
    tone: Optional[str]
    worldbuilding: Optional[str]
    philosophical_theme: Optional[str]

    class Config:
        from_attributes = True


@router.post("/", response_model=NovelResponse)
async def create_novel(novel: NovelCreate, db: AsyncSession = Depends(get_db)):
    """创建新小说"""
    db_novel = Novel(**novel.model_dump())
    db.add(db_novel)
    await db.commit()
    await db.refresh(db_novel)
    return db_novel


@router.get("/", response_model=list[NovelResponse])
async def list_novels(db: AsyncSession = Depends(get_db)):
    """列出所有小说"""
    result = await db.execute(select(Novel))
    novels = result.scalars().all()
    return novels


@router.get("/{novel_id}", response_model=NovelResponse)
async def get_novel(novel_id: str, db: AsyncSession = Depends(get_db)):
    """获取小说详情"""
    result = await db.execute(select(Novel).where(Novel.id == novel_id))
    novel = result.scalar_one_or_none()
    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")
    return novel


@router.put("/{novel_id}", response_model=NovelResponse)
async def update_novel(
    novel_id: str,
    novel: NovelUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新小说信息"""
    result = await db.execute(select(Novel).where(Novel.id == novel_id))
    db_novel = result.scalar_one_or_none()
    if not db_novel:
        raise HTTPException(status_code=404, detail="Novel not found")

    for key, value in novel.model_dump(exclude_unset=True).items():
        setattr(db_novel, key, value)

    await db.commit()
    await db.refresh(db_novel)
    return db_novel


@router.get("/{novel_id}/rag/summaries")
async def get_rag_summaries(novel_id: str, db: AsyncSession = Depends(get_db)):
    """获取小说在 RAG 中的所有摘要"""
    return await get_rag_summaries_for_novel(novel_id, db)


class RagSummaryUpdate(BaseModel):
    text: str


@router.put("/{novel_id}/rag/summaries/{doc_id}")
async def update_rag_summary(
    novel_id: str,
    doc_id: str,
    update: RagSummaryUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新 RAG 摘要内容"""
    return await update_rag_summary_for_novel(novel_id, doc_id, update.text, db)


@router.delete("/{novel_id}/rag/summaries/{doc_id}")
async def delete_rag_summary(
    novel_id: str,
    doc_id: str,
    db: AsyncSession = Depends(get_db)
):
    """删除 RAG 摘要"""
    return await delete_rag_summary_for_novel(novel_id, doc_id, db)


@router.delete("/{novel_id}")
async def delete_novel(novel_id: str, db: AsyncSession = Depends(get_db)):
    """删除小说"""
    result = await db.execute(select(Novel).where(Novel.id == novel_id))
    novel = result.scalar_one_or_none()
    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")

    await db.delete(novel)
    await db.commit()
    return {"message": "Novel deleted"}


@router.get("/{novel_id}/export")
async def export_novel(novel_id: str, db: AsyncSession = Depends(get_db)):
    """导出小说全文"""
    from fastapi.responses import Response
    payload = await build_novel_export_payload(novel_id, db)
    
    return Response(
        content=payload["content"],
        media_type="text/plain",
        headers={
            "Content-Disposition": f"attachment; filename*=utf-8''{payload['filename']}"
        }
    )


class OutlineGenerateRequest(BaseModel):
    premise: str
    genre: str = "玄幻"
    tone: str = "严肃"
    num_chapters: int = 10


class ChapterResponse(BaseModel):
    id: str
    novel_id: str
    order_index: int
    title: Optional[str]
    summary: Optional[str]

    class Config:
        from_attributes = True


@router.post("/{novel_id}/outline", response_model=List[ChapterResponse])
async def generate_outline(
    novel_id: str,
    request: OutlineGenerateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    AI 根据故事核生成章节列表、角色和世界观

    Args:
        novel_id: 小说 ID
        request: 大纲生成请求

    Returns:
        生成的章节列表
    """
    return await generate_novel_outline_for_novel(
        novel_id=novel_id,
        premise=request.premise,
        genre=request.genre,
        tone=request.tone,
        num_chapters=request.num_chapters,
        db=db,
    )


@router.get("/{novel_id}/relationships", response_model=List[RelationshipResponse])
async def list_relationships(novel_id: str, db: AsyncSession = Depends(get_db)):
    """获取小说的人际关系"""
    # Eager load characters to get names
    stmt = (
        select(Relationship)
        .where(Relationship.novel_id == novel_id)
        .options(
            selectinload(Relationship.character_a),
            selectinload(Relationship.character_b)
        )
    )
    result = await db.execute(stmt)
    rels = result.scalars().all()
    return rels
