"""Scene image generation service."""
import asyncio
import json
import re
from typing import Any, Optional

import aiohttp

from app.config import settings
from app.logging import get_logger
from app.services.generator import OpenAICompatClient

logger = get_logger(__name__)

MINIMAX_IMAGE_API_URL = "https://api.minimaxi.com/v1/image_generation"
DEFAULT_STYLE_PROMPT = "Cinematic lighting, detailed, photorealistic, 8k resolution, movie still."
PORTRAIT_STYLE = "Character portrait, head and shoulders, detailed face, cinematic lighting, high quality, 8k."


def _build_storyboard_prompt(scene_text: str) -> str:
    system_prompt = """You are a professional storyboard artist and director.
Based on the provided scene content, generate 3 to 4 distinct visual prompts for storyboard images.
Each prompt should focus on a key moment or visual detail of the scene.

CRITICAL: The prompts MUST be in Simplified Chinese (简体中文). Do NOT output English.

Output format: JSON array of strings.
Example: ["一个昏暗小巷的全景镜头，地面潮湿反射着霓虹灯光...", "角色手部的特写，紧紧握着一把生锈的钥匙...", "过肩镜头，展示主角面对巨大的神秘黑影..."]
Do not output anything else but the JSON array.
"""
    return f"{system_prompt}\n\nUser Input:\n{scene_text}"


def _parse_prompt_list(raw_response: str) -> list[str]:
    cleaned = raw_response.strip()
    cleaned = re.sub(r"<think>.*?</think>", "", cleaned, flags=re.DOTALL).strip()

    if "```json" in cleaned:
        cleaned = cleaned.split("```json")[1].split("```")[0].strip()
    elif "```" in cleaned:
        cleaned = cleaned.split("```")[1].split("```")[0].strip()

    prompts = json.loads(cleaned)
    if isinstance(prompts, list):
        return [str(item) for item in prompts if str(item).strip()]
    return []


async def _generate_storyboard_prompts(
    scene_location: Optional[str], scene_content: Optional[str], scene_beat_description: Optional[str]
) -> list[str]:
    client = OpenAICompatClient(
        api_key=settings.openai_api_key or settings.minimax_api_key,
        base_url=settings.openai_base_url or settings.minimax_base_url,
        model=settings.openai_model or "abab6.5s-chat",
    )
    scene_text = (
        f"Location: {scene_location or 'Unknown'}\n"
        f"Content: {scene_content or scene_beat_description or ''}"
    )
    prompt_text = _build_storyboard_prompt(scene_text)

    try:
        response = await client.generate(prompt_text)
        prompts = _parse_prompt_list(response)
        if prompts:
            return prompts
        logger.warning("LLM prompt parse returned empty list, falling back to base prompt")
    except Exception:
        logger.exception("Failed to generate storyboard prompts from LLM")

    return [f"{scene_location or ''}. {scene_beat_description or ''}".strip()]


def _extract_image_url(payload: dict[str, Any]) -> Optional[str]:
    if "data" in payload and isinstance(payload["data"], list) and payload["data"]:
        return payload["data"][0].get("url")
    if (
        "data" in payload
        and isinstance(payload["data"], dict)
        and isinstance(payload["data"].get("image_urls"), list)
        and payload["data"]["image_urls"]
    ):
        return payload["data"]["image_urls"][0]
    if "images" in payload and isinstance(payload["images"], list) and payload["images"]:
        return payload["images"][0].get("url")
    if "output" in payload and isinstance(payload["output"], dict):
        return payload["output"].get("url")
    return None


async def _generate_single_image(
    session: aiohttp.ClientSession,
    semaphore: asyncio.Semaphore,
    prompt_text: str,
    subject_reference_url: Optional[str] = None,
) -> Optional[dict[str, str]]:
    async with semaphore:
        payload = {
            "model": "image-01",
            "prompt": f"{prompt_text} {DEFAULT_STYLE_PROMPT}".strip(),
            "aspect_ratio": "16:9",
            "response_format": "url",
            "n": 1,
            "prompt_optimizer": True,
        }
        if subject_reference_url and subject_reference_url.strip():
            payload["subject_reference"] = [
                {"type": "character", "image_file": subject_reference_url.strip()}
            ]
        headers = {
            "Authorization": f"Bearer {settings.minimax_api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with session.post(MINIMAX_IMAGE_API_URL, headers=headers, json=payload) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    logger.warning(
                        "MiniMax image request failed status=%s prompt=%s err=%s",
                        resp.status,
                        prompt_text[:20],
                        error_text,
                    )
                    return None
                data = await resp.json()
                image_url = _extract_image_url(data)
                if image_url:
                    return {"url": image_url, "prompt": prompt_text}
                return None
        except Exception:
            logger.exception("MiniMax image request exception prompt=%s", prompt_text[:20])
            return None


async def generate_scene_images(
    scene_location: Optional[str],
    scene_content: Optional[str],
    scene_beat_description: Optional[str],
    subject_reference_url: Optional[str] = None,
) -> list[dict[str, str]]:
    """
    生成分镜图。若传入 subject_reference_url（角色肖像 URL），
    则使用 MiniMax 主体参考，使图中人物与肖像一致。
    """
    prompts = await _generate_storyboard_prompts(
        scene_location=scene_location,
        scene_content=scene_content,
        scene_beat_description=scene_beat_description,
    )

    semaphore = asyncio.Semaphore(5)
    async with aiohttp.ClientSession() as session:
        tasks = [
            _generate_single_image(session, semaphore, p, subject_reference_url)
            for p in prompts
        ]
        results = await asyncio.gather(*tasks)

    return [result for result in results if result is not None]


def _build_character_portrait_prompt(name: str, appearance: Optional[str], bio: Optional[str]) -> str:
    """根据角色名、外貌、简介拼出肖像图 prompt（中文）。"""
    parts = [f"角色肖像：{name}"]
    if appearance and appearance.strip():
        parts.append(appearance.strip())
    if bio and bio.strip():
        parts.append(bio.strip()[:200])
    return "，".join(parts)


async def generate_character_portrait(
    name: str,
    appearance: Optional[str] = None,
    bio: Optional[str] = None,
) -> Optional[str]:
    """生成单张角色肖像图，返回 URL，失败返回 None。"""
    if not settings.minimax_api_key:
        logger.warning("MiniMax API Key not configured, skip character portrait")
        return None
    prompt_text = _build_character_portrait_prompt(name, appearance, bio)
    prompt_text = f"{prompt_text}，{PORTRAIT_STYLE}".strip()
    payload = {
        "model": "image-01",
        "prompt": prompt_text,
        "aspect_ratio": "1:1",
        "response_format": "url",
        "n": 1,
        "prompt_optimizer": True,
    }
    headers = {
        "Authorization": f"Bearer {settings.minimax_api_key}",
        "Content-Type": "application/json",
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(MINIMAX_IMAGE_API_URL, headers=headers, json=payload) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    logger.warning(
                        "MiniMax character portrait failed status=%s err=%s",
                        resp.status,
                        error_text[:200],
                    )
                    return None
                data = await resp.json()
                return _extract_image_url(data)
    except Exception:
        logger.exception("Character portrait request exception")
        return None
