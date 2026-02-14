import asyncio
import json
import re
import os
from typing import Any, AsyncGenerator, Dict, List, Optional

import aiohttp
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Character, Scene
from app.rag import rag_service
from app.config import settings


class OpenAICompatClient:
    """OpenAI 兼容 API 客户端"""

    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model

    async def generate(self, prompt: str) -> str:
        """同步生成"""
        url = f"{self.base_url}/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 4096,
            "thinking": {"type": "off"}
        }

        # 设置超时时间为 300 秒
        timeout = aiohttp.ClientTimeout(total=300)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status != 200:
                    error = await response.text()
                    raise Exception(f"API error: {error}")

                data = await response.json()
                return data.get("choices", [{}])[0].get("message", {}).get("content", "")

    async def generate_stream(self, prompt: str) -> AsyncGenerator[str, None]:
        """流式生成"""
        url = f"{self.base_url}/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 4096,
            "thinking": {"type": "off"},
            "stream": True
        }

        # 设置超时时间为 300 秒
        timeout = aiohttp.ClientTimeout(total=300)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status != 200:
                    error = await response.text()
                    raise Exception(f"API error: {error}")

                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    if not line or not line.startswith('data:'):
                        continue

                    json_str = line[5:].strip()
                    if json_str == "[DONE]":
                        break

                    try:
                        data = json.loads(json_str)
                        delta = data.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        continue


class LLMClient:
    """LLM 客户端封装"""

    def __init__(self):
        self.api_key = settings.openai_api_key or settings.minimax_api_key
        self.base_url = settings.openai_base_url or settings.minimax_base_url
        self.model = settings.openai_model

        self.client = None

        if self.api_key and self.base_url:
            self.client = OpenAICompatClient(
                api_key=self.api_key,
                base_url=self.base_url,
                model=self.model
            )

    async def generate(self, prompt: str) -> str:
        """同步生成文本"""
        if not self.client:
            return self._mock_response(prompt)
        return await self.client.generate(prompt)

    async def generate_stream(self, prompt: str) -> AsyncGenerator[str, None]:
        """流式生成文本"""
        if not self.client:
            response = self._mock_response(prompt)
            for char in response:
                yield char
                await asyncio.sleep(0.02)
            return

        skip_content = False
        buffer = ""

        async for chunk in self.client.generate_stream(prompt):
            # 处理思考内容过滤逻辑
            # 将新 chunk 拼接到缓冲区
            buffer += chunk

            while True:
                # 如果处于跳过模式，寻找结束标签
                if skip_content:
                    if '</think>' in buffer:
                        end_idx = buffer.find('</think>') + 8  # 8 is len('</think>')
                        buffer = buffer[end_idx:]
                        skip_content = False
                        # 继续循环处理剩余的 buffer
                    else:
                        # 没找到结束标签，清空 buffer (因为都在思考内容里)，等待更多数据
                        buffer = ""
                        break
                
                # 如果不在跳过模式，寻找开始标签
                else:
                    if '<think>' in buffer:
                        start_idx = buffer.find('<think>')
                        # 输出开始标签前的内容
                        if start_idx > 0:
                            yield buffer[:start_idx]
                        
                        # 移除开始标签前的内容和开始标签本身
                        buffer = buffer[start_idx + 7:] # 7 is len('<think>')
                        skip_content = True
                        # 继续循环，处理可能在同一个 chunk 里的结束标签
                    else:
                        # 没找到开始标签，输出 buffer 并清空
                        if buffer:
                            yield buffer
                            buffer = ""
                        break

        # 循环结束后，如果还有剩余 buffer 且不在跳过模式，输出
        if not skip_content and buffer:
            yield buffer

    def _mock_response(self, prompt: str) -> str:
        return "模拟响应"


class OutlineGenerator:
    """大纲生成器"""

    def __init__(self, llm: LLMClient):
        self.llm = llm

    async def generate_outline(
        self,
        novel_id: str,
        premise: str,
        genre: str = "玄幻",
        tone: str = "严肃",
        num_chapters: int = 10
    ) -> Dict[str, Any]:
        prompt = self._build_outline_prompt(premise, genre, tone, num_chapters)
        response = await self.llm.generate(prompt)
        result = self._parse_outline_response(response, novel_id, num_chapters)
        return result

    async def generate_outline_stream(self, novel_id: str) -> AsyncGenerator[str, None]:
        from sqlalchemy import select
        from app.models import Novel
        from app.database import AsyncSessionLocal

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Novel).where(Novel.id == novel_id))
            novel = result.scalar_one_or_none()
            if not novel:
                return

            prompt = self._build_outline_prompt(
                novel.premise,
                novel.genre or "玄幻",
                novel.tone or "严肃",
                10
            )

            async for chunk in self.llm.generate_stream(prompt):
                yield chunk

    def _build_outline_prompt(self, premise: str, genre: str, tone: str, num_chapters: int) -> str:
        return f"""小说：{premise}
类型：{genre}
风格：{tone}
章节数：{num_chapters}

请按以下格式输出（不要有任何思考内容）：

【章节概要】
章节标题|章节概要
（共{num_chapters}个）

【角色】
角色名|角色设定|性格

【世界观】
条目名|内容
"""

    def _parse_outline_response(self, response: str, novel_id: str, num_chapters: int) -> Dict[str, Any]:
        chapters = []
        characters = []
        lore = []

        response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
        response = re.sub(r'\*\*', '', response)

        sections = response.split('【')

        for section in sections:
            if '章节概要' in section:
                chapters = self._parse_chapters(section, novel_id)
            elif '角色' in section:
                characters = self._parse_characters(section, novel_id)
            elif '世界观' in section:
                lore = self._parse_lore(section, novel_id)

        if not chapters:
            raise ValueError("无法解析大纲生成结果")

        return {"chapters": chapters, "characters": characters, "lore": lore}

    def _parse_chapters(self, text: str, novel_id: str) -> List[Dict]:
        chapters = []
        lines = text.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if any(x in line for x in ['章节概要', '共', '(如:', '请按', '请输出', '【', '】']):
                continue

            line = re.sub(r'^\d+[.、\s]+', '', line)
            line = line.strip()
            if not line or len(line) < 5:
                continue

            if '|' in line:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 2 and parts[0]:
                    title = parts[0].strip()
                    if any(x in title for x in ['章节', '标题', '示例']):
                        continue
                    summary = parts[1].strip() if len(parts) > 1 else ""
                    if title and summary and len(summary) > 10:
                        chapters.append({
                            "novel_id": novel_id,
                            "order_index": len(chapters) + 1,
                            "title": title,
                            "summary": summary
                        })

        return chapters

    def _parse_characters(self, text: str, novel_id: str) -> List[Dict]:
        characters = []
        lines = text.split('\n')

        for line in lines:
            line = line.strip()
            if not line or '角色' in line or '---' in line:
                continue

            line = line.strip('|').strip()
            if not line:
                continue

            parts = [p.strip() for p in line.split('|')]

            if len(parts) >= 2 and parts[0]:
                if any(x in parts[0] for x in ['角色', '角色名', '姓名', '名称']):
                    continue

                name = parts[0].strip()
                bio = parts[1].strip() if len(parts) > 1 else ""
                personality = parts[2].strip() if len(parts) > 2 else ""

                if name and len(name) > 0:
                    characters.append({
                        "novel_id": novel_id,
                        "name": name,
                        "bio": bio,
                        "personality": personality,
                        "role": "角色"
                    })

        return characters

    def _parse_lore(self, text: str, novel_id: str) -> List[Dict]:
        lore = []
        lines = text.split('\n')

        for line in lines:
            line = line.strip()
            if not line or '世界观' in line or '---' in line:
                continue

            line = line.strip('|').strip()
            if not line:
                continue

            parts = [p.strip() for p in line.split('|')]

            if len(parts) >= 2 and parts[0]:
                if any(x in parts[0] for x in ['设定', '名称', '项目', '世界观']):
                    continue

                title = parts[0].strip()
                content = parts[1].strip() if len(parts) > 1 else ""
                if len(parts) > 2:
                    content = ' | '.join([p.strip() for p in parts[1:]])

                if title and content:
                    lore.append({
                        "novel_id": novel_id,
                        "title": title,
                        "content": content,
                        "category": "世界观"
                    })
            else:
                for sep in ['：', ':', '——', '—', '-']:
                    if sep in line:
                        parts = [p.strip() for p in line.split(sep, 1)]
                        if len(parts) >= 2 and parts[0]:
                            lore.append({
                                "novel_id": novel_id,
                                "title": parts[0],
                                "content": parts[1],
                                "category": "世界观"
                            })
                        break

        return lore


class SceneGenerator:
    """场景生成器"""

    def __init__(self, llm: LLMClient):
        self.llm = llm

    async def generate_scene_content(
        self,
        scene_id: str,
        db: AsyncSession
    ) -> AsyncGenerator[str, None]:
        result = await db.execute(select(Scene).where(Scene.id == scene_id))
        scene = result.scalar_one_or_none()
        if not scene:
            return

        context = await self._build_context(scene, db)
        prompt = self._build_writing_prompt(scene, context)

        async for chunk in self.llm.generate_stream(prompt):
            yield chunk

    async def _build_context(self, scene: Scene, db: AsyncSession) -> Dict[str, Any]:
        context = {"prev_summaries": [], "character_contexts": [], "lore_contexts": []}

        print(f"DEBUG: Building context for scene {scene.id}, order_index={scene.order_index}, chapter_id={scene.chapter_id}")

        # 1. 尝试获取同章节的前序场景摘要
        stmt = (
            select(Scene)
            .where(Scene.chapter_id == scene.chapter_id)
            .where(Scene.order_index < scene.order_index) 
            .where(Scene.id != scene.id)
            .order_by(Scene.order_index.desc())
            .limit(5)
        )
        result = await db.execute(stmt)
        prev_scenes = result.scalars().all()
        
        print(f"DEBUG: Found {len(prev_scenes)} prev scenes in same chapter")
        for s in prev_scenes:
            print(f"DEBUG: - Scene {s.id}, order={s.order_index}, summary_len={len(s.summary) if s.summary else 0}")
        
        # 2. 如果同章节没有前序场景（即这是本章第一个场景），则尝试获取上一章的摘要
        if not prev_scenes:
            print("DEBUG: No prev scenes in chapter, looking for prev chapter...")
            # 获取当前场景所属章节
            from app.models import Chapter
            current_chapter_result = await db.execute(select(Chapter).where(Chapter.id == scene.chapter_id))
            current_chapter = current_chapter_result.scalar_one_or_none()
            
            if current_chapter:
                # 获取上一章
                prev_chapter_result = await db.execute(
                    select(Chapter)
                    .where(Chapter.novel_id == current_chapter.novel_id)
                    .where(Chapter.order_index < current_chapter.order_index)
                    .order_by(Chapter.order_index.desc())
                    .limit(1)
                )
                prev_chapter = prev_chapter_result.scalar_one_or_none()
                
                # 如果有上一章，获取上一章的最后几个场景摘要作为前情提要
                if prev_chapter:
                    print(f"DEBUG: Found prev chapter {prev_chapter.id}")
                    prev_scenes_result = await db.execute(
                        select(Scene)
                        .where(Scene.chapter_id == prev_chapter.id)
                        .order_by(Scene.order_index.desc())
                        .limit(3) # 取上一章最后3个场景
                    )
                    prev_scenes = prev_scenes_result.scalars().all()
            
            # 如果连上一章都没有（即全书第一章），或者上一章没有场景，尝试使用“小说故事核(Premise)”作为初始前情提要
            if not prev_scenes and current_chapter:
                print("DEBUG: No prev chapter or scenes, using premise")
                from app.models import Novel
                novel_result = await db.execute(select(Novel).where(Novel.id == current_chapter.novel_id))
                novel = novel_result.scalar_one_or_none()
                if novel and novel.premise:
                    # 构造一个伪场景对象来传递 premise
                    class MockScene:
                        summary = f"【故事背景】：{novel.premise}"
                    prev_scenes = [MockScene()]
        
        # 兼容处理：确保 prev_scenes 中的对象都有 summary 属性
        summaries = []
        for s in reversed(prev_scenes):
            if hasattr(s, 'summary') and s.summary:
                summaries.append(s.summary)
            elif isinstance(s, dict) and s.get('summary'):
                 summaries.append(s['summary'])
            # 针对 MockScene
            elif hasattr(s, 'summary'): 
                 summaries.append(s.summary)
        
        context["prev_summaries"] = summaries
        print(f"DEBUG: Final context summaries: {summaries}")


        if scene.characters_present:
            for char_id in scene.characters_present:
                result = await db.execute(select(Character).where(Character.id == char_id))
                character = result.scalar_one_or_none()
                if character:
                    char_contexts = rag_service.retrieve_context(
                        query=f"{character.name} {character.bio}",
                        type="character",
                        top_k=1
                    )
                    context["character_contexts"].append({
                        "name": character.name,
                        "bio": character.bio,
                        "personality": character.personality
                    })

        if scene.beat_description:
            lore_contexts = rag_service.retrieve_context(
                query=scene.beat_description,
                type="lore",
                top_k=3
            )
            context["lore_contexts"] = lore_contexts

        return context

    def _build_writing_prompt(self, scene: Scene, context: Dict) -> str:
        # 将摘要列表反转回来（因为查询时是倒序的），使其按时间正序排列
        # 注意：在 _build_context 里我们没有 reverse，而是在那里直接 append 了。
        # 让我们检查一下 _build_context 的逻辑。
        # _build_context 里： for s in reversed(prev_scenes): ...
        # prev_scenes 是倒序查出来的 (5, 4, 3...)
        # reversed 后变成 (3, 4, 5...) 即正序。
        # 所以 context["prev_summaries"] 已经是正序的了。
        
        # 为了避免摘要中混入当前场景的摘要（如果逻辑有误），我们在 prompt 里再次强调
        
        prev_summary = "\n".join(context["prev_summaries"]) or "无"

        character_info = ""
        for char in context["character_contexts"]:
            character_info += f"\n角色: {char['name']} - {char.get('personality', '')}"

        lore_info = ""
        for lore in context["lore_contexts"]:
            lore_info += f"- {lore['text']}\n"

        return f"""请根据以下信息写小说正文。注意：不要输出任何思考内容，只需要输出小说正文。

前情提要：{prev_summary}
出场角色：{character_info}
相关设定：{lore_info}
场景：{scene.location}
动作指令：{scene.beat_description}

要求：800-1200字，通过动作描写表现心理，禁止流水账。
"""


class Summarizer:
    """摘要生成器"""

    def __init__(self, llm: LLMClient):
        self.llm = llm

    async def generate_summary(self, content: str) -> str:
        prompt = f"请将以下小说片段浓缩为200字摘要，保留关键剧情：\n\n{content}\n\n注意：请直接输出摘要，不要输出任何思考过程。"
        summary = await self.llm.generate(prompt)
        
        # 再次过滤思考内容，以防万一
        summary = re.sub(r'<think>.*?</think>', '', summary, flags=re.DOTALL)
        summary = summary.strip()
        
        return summary


llm_client = LLMClient()
outline_generator = OutlineGenerator(llm_client)
scene_generator = SceneGenerator(llm_client)
summarizer = Summarizer(llm_client)
