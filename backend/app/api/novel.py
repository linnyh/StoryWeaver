"""Novel API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from typing import Optional, List
from app.database import get_db
from app.models import Novel, Chapter, Character, Lore, Scene, Relationship
from app.services import outline_generator
from app.api.relationship import RelationshipResponse

router = APIRouter()


class NovelCreate(BaseModel):
    title: str
    premise: Optional[str] = None
    genre: Optional[str] = None
    tone: Optional[str] = None
    worldbuilding: Optional[str] = None


class NovelUpdate(BaseModel):
    title: Optional[str] = None
    premise: Optional[str] = None
    genre: Optional[str] = None
    tone: Optional[str] = None
    worldbuilding: Optional[str] = None


class NovelResponse(BaseModel):
    id: str
    title: str
    premise: Optional[str]
    genre: Optional[str]
    tone: Optional[str]
    worldbuilding: Optional[str]

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


from app.rag import rag_service

@router.get("/{novel_id}/rag/summaries")
async def get_rag_summaries(novel_id: str, db: AsyncSession = Depends(get_db)):
    """获取小说在 RAG 中的所有摘要"""
    # 验证小说存在
    result = await db.execute(select(Novel).where(Novel.id == novel_id))
    novel = result.scalar_one_or_none()
    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")
        
    # 从 RAG 检索所有摘要
    summaries = rag_service.retrieve_all_by_novel(
        novel_id=novel_id,
        type="scene_summary",
        top_k=100
    )
    
    # 补充场景信息
    for item in summaries:
        scene_id = item.get("metadata", {}).get("scene_id")
        if scene_id:
            # 尝试查询场景信息（可选）
            # 这里为了性能我们直接返回，前端可以根据 scene_id 再去查或者后端做个 join
            # 为了方便展示，我们加上一些基本元数据
            pass
            
    return summaries


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
    # 1. 验证小说是否存在 (虽然 RAG 不直接依赖 SQL 数据库，但做个权限校验也好)
    result = await db.execute(select(Novel).where(Novel.id == novel_id))
    novel = result.scalar_one_or_none()
    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")

    # 2. 调用 RAG 服务更新
    # 注意：ChromaDB 的 update/upsert 需要完整的 document 和 metadata。
    # 如果只更新 text，我们需要先获取原有的 metadata。
    # 这里为了简化，我们假设 metadata 不变，或者 RAGService 内部处理。
    # 但 RAGService.add_knowledge 是 upsert，我们需要传入 metadata。
    
    # 先查一下原数据以保留 metadata
    existing = rag_service.retrieve_context(query="", type="scene_summary", top_k=1) # 这里的 retrieve_context 只能按 query 查，不太好用。
    # 我们需要一个 get_by_id 的方法。目前 retrieve_all_by_novel 可以查，但效率低。
    # 既然 doc_id 是唯一的，我们假设前端传来的 doc_id 是对的。
    # 实际上，add_knowledge 会覆盖 metadata。如果我们不传 metadata，它可能会丢失。
    # 让我们修改 RAGService 或在这里变通一下。
    # 更好的做法是：RAGService 提供一个 update_text_by_id 方法。
    # 暂时我们在 RAGService 层面没有 update_text，只有 add_knowledge (upsert)。
    # 我们先尝试获取旧数据。
    
    # 由于 RAGService 没有暴露 get_by_id，我们暂时只能重新构造 metadata。
    # 这是一个潜在风险点：如果更新了摘要，metadata 里的 scene_id 丢了怎么办？
    # 解决方案：前端在调用 update 时，应该把 metadata 也传回来，或者我们只允许更新 text，并在后端尽可能保留 metadata。
    # 鉴于 RAGService 的现状，我们先假设这是一个简单的文本更新，且我们信任前端传来的 doc_id。
    # 但为了安全，我们最好在 RAGService 里加一个 get_document(doc_id, type) 方法。
    
    # 既然不能改 RAGService (尽量少改)，我们先用 retrieve_all_by_novel 过滤出这个 doc_id
    all_summaries = rag_service.retrieve_all_by_novel(novel_id, "scene_summary", top_k=1000)
    target_doc = next((item for item in all_summaries if item["id"] == doc_id), None)
    
    if not target_doc:
        raise HTTPException(status_code=404, detail="Summary not found")
        
    # 保留原有 metadata
    metadata = target_doc.get("metadata", {})
    
    rag_service.add_knowledge(
        text=update.text,
        doc_id=doc_id,
        type="scene_summary",
        metadata=metadata
    )
    
    return {"message": "Summary updated", "id": doc_id}


@router.delete("/{novel_id}/rag/summaries/{doc_id}")
async def delete_rag_summary(
    novel_id: str,
    doc_id: str,
    db: AsyncSession = Depends(get_db)
):
    """删除 RAG 摘要"""
    result = await db.execute(select(Novel).where(Novel.id == novel_id))
    novel = result.scalar_one_or_none()
    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")

    rag_service.delete_knowledge(doc_id, "scene_summary")
    return {"message": "Summary deleted"}


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
    from sqlalchemy import select

    # 1. Fetch novel
    result = await db.execute(select(Novel).where(Novel.id == novel_id))
    novel = result.scalar_one_or_none()
    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")

    # 2. Fetch chapters
    chapters_result = await db.execute(
        select(Chapter).where(Chapter.novel_id == novel_id).order_by(Chapter.order_index)
    )
    chapters = chapters_result.scalars().all()
    
    full_text = f"《{novel.title}》\n\n"
    if novel.premise:
        full_text += f"简介：\n{novel.premise}\n\n"
    full_text += "=" * 30 + "\n\n"
    
    for chapter in chapters:
        full_text += f"第{chapter.order_index}章 {chapter.title}\n"
        full_text += "-" * 20 + "\n\n"
            
        # Fetch scenes for this chapter
        scenes_result = await db.execute(
            select(Scene).where(Scene.chapter_id == chapter.id).order_by(Scene.order_index)
        )
        scenes = scenes_result.scalars().all()
        
        for scene in scenes:
            if scene.content:
                full_text += f"{scene.content}\n\n"
            elif scene.beat_description:
                 full_text += f"【场景细纲（未生成正文）】\n{scene.beat_description}\n\n"
        
        full_text += "\n" # Extra newline between chapters

    # URL encode filename to handle Chinese characters
    from urllib.parse import quote
    filename = quote(f"{novel.title}.txt")
    
    return Response(
        content=full_text,
        media_type="text/plain",
        headers={
            "Content-Disposition": f"attachment; filename*=utf-8''{filename}"
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
    # 验证小说存在
    result = await db.execute(select(Novel).where(Novel.id == novel_id))
    novel = result.scalar_one_or_none()
    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")

    # 更新小说信息
    novel.premise = request.premise
    novel.genre = request.genre
    novel.tone = request.tone
    await db.commit()

    # 先删除该小说已有的章节、角色和世界观（如果重复生成）
    # 查询现有数据
    existing_chapters = await db.execute(
        select(Chapter).where(Chapter.novel_id == novel_id)
    )
    for ch in existing_chapters.scalars().all():
        await db.delete(ch)

    existing_characters = await db.execute(
        select(Character).where(Character.novel_id == novel_id)
    )
    for ch in existing_characters.scalars().all():
        await db.delete(ch)

    existing_lore = await db.execute(
        select(Lore).where(Lore.novel_id == novel_id)
    )
    for l in existing_lore.scalars().all():
        await db.delete(l)

    await db.commit()

    # 调用大纲生成器 (返回 chapters, characters, lore)
    try:
        outline_data = await outline_generator.generate_outline(
            novel_id=novel_id,
            premise=request.premise,
            genre=request.genre,
            tone=request.tone,
            num_chapters=request.num_chapters
        )
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

    # 解构响应数据
    chapters_data = outline_data.get("chapters", [])
    characters_data = outline_data.get("characters", [])
    lore_data = outline_data.get("lore", [])

    # 保存章节到数据库
    created_chapters = []
    for chapter_data in chapters_data:
        chapter = Chapter(**chapter_data)
        db.add(chapter)
        created_chapters.append(chapter)

    # 保存角色到数据库
    created_characters = []
    for char_data in characters_data:
        char_data["novel_id"] = novel_id
        character = Character(**char_data)
        db.add(character)
        created_characters.append(character)

    # 保存世界观到数据库
    created_lore = []
    for lore_item in lore_data:
        lore_item["novel_id"] = novel_id
        lore = Lore(**lore_item)
        db.add(lore)
        created_lore.append(lore)

    await db.commit()
    for chapter in created_chapters:
        await db.refresh(chapter)
    for character in created_characters:
        await db.refresh(character)
    for lore in created_lore:
        await db.refresh(lore)

    return created_chapters


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
