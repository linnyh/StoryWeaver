import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import Scene
from app.services.generator import assistant

router = APIRouter()

@router.post("/{scene_id}/chat")
async def chat_with_assistant(
    scene_id: str,
    message: dict,
    db: AsyncSession = Depends(get_db)
):
    """与 AI 助手对话 (SSE 流式)"""
    user_msg = message.get("message", "")
    if not user_msg:
        raise HTTPException(status_code=400, detail="Message is required")

    # 获取当前场景上下文
    result = await db.execute(select(Scene).where(Scene.id == scene_id))
    scene = result.scalar_one_or_none()
    
    context = ""
    if scene and scene.content:
        context = f"当前场景内容：\n{scene.content[:2000]}..." # 截取前2000字作为上下文

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
