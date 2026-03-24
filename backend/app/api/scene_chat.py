import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import Scene, Chapter
from app.services.generator import assistant
from app.rag import rag_service

router = APIRouter()


def _build_chat_context(scene, prev_summaries: list[str], beat_desc: str, rag_snippets: list[str]) -> str:
    """组装对话上下文，控制总长度。"""
    parts = []
    if scene and scene.content:
        content = scene.content[:2200] + ("..." if len(scene.content) > 2200 else "")
        parts.append(f"【当前场景正文】\n{content}")
    if beat_desc:
        parts.append(f"【本场景细纲/目标】\n{beat_desc[:400]}")
    if prev_summaries:
        parts.append("【前情摘要】\n" + "\n".join(prev_summaries[-3:]))
    if rag_snippets:
        parts.append("【相关设定/前文】\n" + "\n".join(rag_snippets[:2]))
    return "\n\n".join(parts) if parts else ""


@router.post("/{scene_id}/chat")
async def chat_with_assistant(
    scene_id: str,
    message: dict,
    db: AsyncSession = Depends(get_db)
):
    """与 AI 助手对话 (SSE 流式)，上下文包含当前场景、细纲、前情与少量 RAG。"""
    user_msg = message.get("message", "")
    if not user_msg:
        raise HTTPException(status_code=400, detail="Message is required")

    result = await db.execute(select(Scene).where(Scene.id == scene_id))
    scene = result.scalar_one_or_none()
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    prev_summaries = []
    novel_id = None
    try:
        ch_result = await db.execute(select(Chapter).where(Chapter.id == scene.chapter_id))
        ch = ch_result.scalar_one_or_none()
        if ch:
            novel_id = ch.novel_id
            prev_result = await db.execute(
                select(Scene)
                .where(Scene.chapter_id == ch.id, Scene.order_index < scene.order_index)
                .order_by(Scene.order_index.desc())
                .limit(3)
            )
            for s in prev_result.scalars().all():
                if s.summary:
                    prev_summaries.append(s.summary[:300])
    except Exception:
        pass

    rag_snippets = []
    if novel_id:
        try:
            for item in rag_service.retrieve_all_by_novel(novel_id, "scene_summary", top_k=2):
                rag_snippets.append((item.get("text") or "")[:250])
        except Exception:
            pass

    context = _build_chat_context(
        scene,
        prev_summaries,
        (scene.beat_description or "")[:400],
        rag_snippets,
    )

    async def event_generator():
        try:
            full_response = ""
            async for chunk in assistant.chat_stream(user_msg, context):
                full_response += chunk
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
            
            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
