"""MiniMax 分镜视频生成：主体参考模式，保证人物与角色肖像一致。"""
import asyncio
import json
from typing import Any, Optional

import aiohttp

from app.config import settings
from app.logging import get_logger

logger = get_logger(__name__)

MINIMAX_VIDEO_CREATE_URL = "https://api.minimaxi.com/v1/video_generation"
MINIMAX_VIDEO_QUERY_URL = "https://api.minimaxi.com/v1/query/video_generation"
MINIMAX_FILES_RETRIEVE_URL = "https://api.minimaxi.com/v1/files/retrieve"

# 主体参考模型，人物与肖像一致；6 秒 1080P
DEFAULT_VIDEO_MODEL = "S2V-01"
DEFAULT_DURATION = 6
DEFAULT_RESOLUTION = "1080P"


def _build_video_prompt(
    location: Optional[str],
    beat_description: Optional[str],
    first_prompt: Optional[str],
) -> str:
    """根据场景地点、节拍描述、首张分镜 prompt 拼出视频动作描述（中文，保证连贯性）。"""
    parts = []
    if location:
        parts.append(f"场景地点：{location}。")
    if beat_description:
        parts.append(beat_description.strip())
    if first_prompt and first_prompt.strip():
        parts.append(first_prompt.strip())
    text = " ".join(parts).strip() or "镜头缓慢推进，画面氛围与场景一致。"
    # 限制长度，并强调运镜与连贯
    if len(text) > 500:
        text = text[:497] + "..."
    return text


async def create_scene_video_task(
    prompt: str,
    subject_image_urls: list[str],
    duration: int = DEFAULT_DURATION,
    resolution: str = DEFAULT_RESOLUTION,
    model: str = DEFAULT_VIDEO_MODEL,
) -> tuple[Optional[str], Optional[str]]:
    """
    创建 MiniMax 主体参考视频任务。返回 (task_id, error_message)。
    S2V-01 仅支持单张主体参考图，且不需要 duration/resolution 参数。
    """
    if not settings.minimax_api_key:
        return None, "MiniMax API Key 未配置"
    if not subject_image_urls:
        return None, "缺少角色肖像图"

    # S2V-01 仅支持单张参考图，且接口不需要 duration/resolution
    first_image = subject_image_urls[0].strip()
    payload: dict[str, Any] = {
        "model": model,
        "prompt": prompt[:2000] if prompt else "镜头缓慢推进。",
        "subject_reference": [
            {"type": "character", "image": [first_image]}
        ],
    }
    headers = {
        "Authorization": f"Bearer {settings.minimax_api_key}",
        "Content-Type": "application/json",
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                MINIMAX_VIDEO_CREATE_URL, headers=headers, json=payload
            ) as resp:
                raw = await resp.text()
                if resp.status != 200:
                    logger.warning("MiniMax video create status=%s body=%s", resp.status, raw[:400])
                    return None, f"MiniMax 接口异常: {raw[:200]}"
                try:
                    data = json.loads(raw)
                except Exception:
                    data = {}
                if not isinstance(data, dict):
                    data = {}
                base = data.get("base_resp") or {}
                code = base.get("status_code", -1)
                msg = base.get("status_msg") or ""
                if code != 0:
                    err = msg or str(data)
                    logger.warning("MiniMax video create base_resp code=%s msg=%s", code, msg)
                    return None, err or f"状态码 {code}"
                task_id = data.get("task_id")
                if task_id:
                    return str(task_id), None
                return None, "响应中无 task_id"
    except Exception as e:
        logger.exception("MiniMax video create exception")
        return None, str(e)


async def query_video_task_status(task_id: str) -> tuple[str, Optional[str]]:
    """
    轮询视频任务状态。返回 (status, file_id)。
    status 为 "Success" 时 file_id 有值；"Fail" 时 file_id 为 None。
    """
    headers = {"Authorization": f"Bearer {settings.minimax_api_key}"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                MINIMAX_VIDEO_QUERY_URL, headers=headers, params={"task_id": task_id}
            ) as resp:
                if resp.status != 200:
                    return "Error", None
                data = await resp.json()
                status = data.get("status", "")
                file_id = data.get("file_id") if status == "Success" else None
                return status, file_id
    except Exception:
        logger.exception("Query video task exception task_id=%s", task_id)
        return "Error", None


async def fetch_video_download_url(file_id: str) -> Optional[str]:
    """根据 file_id 获取视频下载/播放 URL。"""
    headers = {"Authorization": f"Bearer {settings.minimax_api_key}"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                MINIMAX_FILES_RETRIEVE_URL, headers=headers, params={"file_id": file_id}
            ) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                file_obj = data.get("file") or data.get("data")
                if isinstance(file_obj, dict):
                    return file_obj.get("download_url") or file_obj.get("url")
                return None
    except Exception:
        logger.exception("Fetch video URL exception file_id=%s", file_id)
        return None
