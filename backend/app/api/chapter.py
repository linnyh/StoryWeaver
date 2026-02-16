import json
import re
from typing import Any, AsyncGenerator, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Chapter, Novel, Scene
from app.services import outline_generator, scene_generator

from pydantic import BaseModel

router = APIRouter()


class ChapterResponse(BaseModel):
    id: str
    novel_id: str
    order_index: int
    title: Optional[str]
    summary: Optional[str]
    scene_count: Optional[int] = 0

    class Config:
        from_attributes = True


class ChapterCreate(BaseModel):
    novel_id: str
    order_index: int
    title: str
    summary: Optional[str] = None

@router.post("/", response_model=ChapterResponse)
async def create_chapter(
    chapter: ChapterCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建章节"""
    # 验证小说存在
    result = await db.execute(select(Novel).where(Novel.id == chapter.novel_id))
    novel = result.scalar_one_or_none()
    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")

    db_chapter = Chapter(**chapter.model_dump())
    db.add(db_chapter)
    await db.commit()
    await db.refresh(db_chapter)
    return db_chapter


@router.get("/")
async def get_chapters(novel_id: str, db: AsyncSession = Depends(get_db)):
    """获取小说的所有章节"""
    stmt = (
        select(Chapter, func.count(Scene.id).label("scene_count"))
        .outerjoin(Scene, Scene.chapter_id == Chapter.id)
        .where(Chapter.novel_id == novel_id)
        .group_by(Chapter.id)
        .order_by(Chapter.order_index)
    )
    result = await db.execute(stmt)
    
    chapters_data = []
    for chapter, count in result.all():
        chapters_data.append({
            "id": chapter.id,
            "novel_id": chapter.novel_id,
            "order_index": chapter.order_index,
            "title": chapter.title,
            "summary": chapter.summary,
            "scene_count": count
        })
        
    return chapters_data


@router.post("/{chapter_id}/beats")
async def generate_beats(
    chapter_id: str,
    request: dict,
    db: AsyncSession = Depends(get_db)
):
    """生成场景细纲"""
    # 验证章节存在
    result = await db.execute(select(Chapter).where(Chapter.id == chapter_id))
    chapter = result.scalar_one_or_none()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    # 获取前文摘要
    prev_summary = ""
    if chapter.order_index > 1:
        prev_chapter_result = await db.execute(
            select(Chapter)
            .where(Chapter.novel_id == chapter.novel_id)
            .where(Chapter.order_index == chapter.order_index - 1)
        )
        prev_chapter = prev_chapter_result.scalar_one_or_none()
        if prev_chapter:
            prev_summary = prev_chapter.summary

    # 调用 AI 生成场景
    prompt = f"""请将小说章节拆分为具体的场景细纲。

【当前任务】
根据本章概要，将其拆解为 4-6 个具体的场景（Scene）。

【本章信息】
章节标题：{chapter.title}
章节概要：{chapter.summary}

【前情提要】（仅供上下文参考，已发生剧情，请勿重复）
{prev_summary}

【生成要求】
1. 严格基于“本章概要”进行拆解，确保剧情向前推进。
2. 绝对不要重复“前情提要”中的剧情。
3. 每个场景包含：地点、出场人物、动作指令（Beat）。
4. 动作指令要具体，包含冲突和推进。
5. **张力与情绪控制**：请为每个场景规划“张力等级”（tension_level，1-10）和“情绪目标”（emotional_target）。
   - 张力曲线应有起伏，例如：平缓铺垫(3) -> 遭遇打压(8) -> 绝地反击(10)。

请直接输出 JSON 格式的数组，不要包含任何 markdown 格式标记或其他文字。
格式示例：
[
  {{
    "location": "青云门广场",
    "characters_present": ["林昊", "秦霜"],
    "beat_description": "林昊在擂台上与秦霜对峙，周围弟子议论纷纷，气氛紧张。",
    "tension_level": 7,
    "emotional_target": "展示主角被轻视后的压抑怒火"
  }}
]
"""
    try:
        response = await scene_generator.llm.generate(prompt)
        scenes_data = parse_beats_response(response, request.get("num_beats", 5))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # 保存场景到数据库
    # 先删除旧场景
    await db.execute(
        delete(Scene).where(Scene.chapter_id == chapter_id)
    )

    created_scenes = []
    for i, scene_data in enumerate(scenes_data):
        scene = Scene(
            chapter_id=chapter_id,
            order_index=i + 1,
            location=scene_data["location"],
            characters_present=scene_data.get("characters_present", []),
            beat_description=scene_data["beat_description"],
            tension_level=scene_data.get("tension_level", 5),
            emotional_target=scene_data.get("emotional_target", ""),
            status="draft"
        )
        db.add(scene)
        created_scenes.append(scene)

    await db.commit()
    for scene in created_scenes:
        await db.refresh(scene)

    return created_scenes


@router.get("/{chapter_id}")
async def get_chapter(chapter_id: str, db: AsyncSession = Depends(get_db)):
    """获取章节详情"""
    result = await db.execute(select(Chapter).where(Chapter.id == chapter_id))
    chapter = result.scalar_one_or_none()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return chapter


@router.get("/{chapter_id}/scenes")
async def get_chapter_scenes(chapter_id: str, db: AsyncSession = Depends(get_db)):
    """获取章节下的所有场景"""
    result = await db.execute(
        select(Scene).where(Scene.chapter_id == chapter_id).order_by(Scene.order_index)
    )
    scenes = result.scalars().all()
    return scenes


@router.put("/{chapter_id}")
async def update_chapter(
    chapter_id: str,
    title: Optional[str] = None,
    summary: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """更新章节"""
    result = await db.execute(select(Chapter).where(Chapter.id == chapter_id))
    chapter = result.scalar_one_or_none()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    if title is not None:
        chapter.title = title
    if summary is not None:
        chapter.summary = summary

    await db.commit()
    return chapter


@router.post("/{chapter_id}/summarize")
async def generate_chapter_summary(
    chapter_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    根据章节下的所有场景生成章节摘要，并更新到数据库
    """
    # 1. 验证章节存在
    result = await db.execute(select(Chapter).where(Chapter.id == chapter_id))
    chapter = result.scalar_one_or_none()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    # 2. 获取所有场景
    result = await db.execute(
        select(Scene).where(Scene.chapter_id == chapter_id).order_by(Scene.order_index)
    )
    scenes = result.scalars().all()
    
    if not scenes:
        raise HTTPException(status_code=400, detail="Chapter has no scenes")

    # 3. 收集场景内容
    scene_texts = []
    for scene in scenes:
        text = ""
        if scene.summary:
            text = f"场景{scene.order_index}摘要：{scene.summary}"
        elif scene.content:
            # 如果有正文但没有摘要，取前500字
            text = f"场景{scene.order_index}正文片段：{scene.content[:500]}..." 
        elif scene.beat_description:
            text = f"场景{scene.order_index}细纲：{scene.beat_description}"
        
        if text:
            scene_texts.append(text)
            
    if not scene_texts:
         raise HTTPException(status_code=400, detail="Scenes have no content to summarize")
         
    combined_text = "\n\n".join(scene_texts)
    
    # 4. 调用 LLM 生成摘要
    prompt = f"""请根据以下章节内的场景信息，生成该章节的完整摘要（300-500字）。
    
章节标题：{chapter.title}

{combined_text}

请输出摘要内容（不要包含思考过程）："""

    try:
        summary = await scene_generator.llm.generate(prompt)
        
        # 清理
        summary = re.sub(r'<think>.*?</think>', '', summary, flags=re.DOTALL)
        summary = summary.strip()
        
        # 5. 更新章节
        chapter.summary = summary
        await db.commit()
        
        return {"id": chapter.id, "summary": summary}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



def parse_beats_response(response: str, num_beats: int = 5) -> List[Dict[str, Any]]:
    """解析节奏点响应"""
    scenes = []

    # 清理响应 (支持多行思考内容)
    response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
    response = re.sub(r'章：[^\n]*', '', response)
    response = re.sub(r'节：[^\n]*', '', response)
    response = re.sub(r'分\d+个场景[^\n]*', '', response)
    response = re.sub(r'\*\*', '', response)

    if not response or len(response.strip()) < 10:
        raise ValueError("生成内容为空，生成失败")

    # 移除首尾的 ```json 和 ``` 标记（如果存在）
    response = re.sub(r'^```json\s*', '', response.strip())
    response = re.sub(r'\s*```$', '', response)

    # 尝试解析 JSON 格式
    try:
        json_data = json.loads(response)
        if isinstance(json_data, list):
            return [
                {
                    "location": item.get("location", ""),
                    "characters_present": item.get("characters_present", []),
                    "beat_description": item.get("beat_description", ""),
                    "tension_level": item.get("tension_level", 5),
                    "emotional_target": item.get("emotional_target", ""),
                    "status": "draft"
                }
                for item in json_data
                if item.get("location") and item.get("beat_description")
            ]
        elif isinstance(json_data, dict) and "scenes" in json_data:
             return [
                {
                    "location": item.get("location", ""),
                    "characters_present": item.get("characters_present", []),
                    "beat_description": item.get("beat_description", ""),
                    "tension_level": item.get("tension_level", 5),
                    "emotional_target": item.get("emotional_target", ""),
                    "status": "draft"
                }
                for item in json_data["scenes"]
                if item.get("location") and item.get("beat_description")
            ]
    except json.JSONDecodeError:
        pass # 继续使用原有文本解析逻辑

    # 按行解析 (Fallback, usually simpler, ignoring tension for now if json fails)
    lines = response.strip().split('\n')
    
    # ... (Keep existing line parsing as fallback, but it won't extract tension/emotion well)
    # Given we enforce JSON in prompt, JSON failure usually means bad output.
    # We'll just return what we can from line parsing.
    
    for line in lines:
        line = line.strip()
        if not line or len(line) < 4:
            continue

        # 必须包含中文
        if not re.search(r'[\u4e00-\u9fff]', line):
            continue

        # 跳过提示词
        if any(x in line for x in ['章', '节', '请', '以下', '格式', '例子', '输出']):
            continue

        # 移除行首数字
        line = re.sub(r'^\d+[.、\s\-–—]+', '', line)

        # 必须有分隔符
        if '-' not in line:
            continue

        # 分割
        parts = [p.strip() for p in line.split('-')]
        if len(parts) >= 2 and parts[0]:
            location = parts[0]
            beat_desc = '-'.join(parts[1:]) if len(parts) > 1 else ""
            characters = []

            # 尝试提取角色
            if len(parts) > 1:
                char_match = re.match(r'^([^,，]+)', parts[1])
                if char_match:
                    characters = [char_match.group(1)]

            # 验证
            if location and len(location) > 1 and len(beat_desc) > 2:
                scenes.append({
                    "location": location,
                    "characters_present": characters,
                    "beat_description": beat_desc,
                    "tension_level": 5, # Default
                    "emotional_target": "", # Default
                    "status": "draft"
                })

        if len(scenes) >= num_beats:
            break

    if not scenes:
        raise ValueError(f"无法解析生成结果，原始响应: {response[:200]}")

    return scenes
