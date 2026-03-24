"""Scene 模型 - 生成的最小单位"""
import uuid
from sqlalchemy import Column, String, Text, Integer, ForeignKey, JSON
from app.database import Base


class Scene(Base):
    """场景/细纲表"""
    __tablename__ = "scenes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    chapter_id = Column(String(36), ForeignKey("chapters.id"), nullable=False)
    order_index = Column(Integer, nullable=False, default=0)
    location = Column(String(255), nullable=True)  # 场景地点
    characters_present = Column(JSON, nullable=True)  # 当前场景在场人员列表
    beat_description = Column(Text, nullable=True)  # 详细的动作指令
    content = Column(Text, nullable=True)  # AI 生成的最终正文
    summary = Column(Text, nullable=True)  # 场景摘要（用于后续上下文）
    status = Column(String(20), nullable=False, default="draft")  # draft/approved
    tension_level = Column(Integer, nullable=True)  # 情绪张力 (1-10)
    emotional_target = Column(String(255), nullable=True)  # 情绪传达目标
    image_url = Column(String(500), nullable=True)  # 场景分镜配图
    image_prompts = Column(JSON, nullable=True)  # 场景分镜配图及Prompt列表 [{'url': '', 'prompt': ''}, ...]
    video_task_id = Column(String(128), nullable=True)  # MiniMax 视频生成任务 ID（轮询用）
    video_url = Column(String(512), nullable=True)  # 生成完成后的视频播放/下载地址
    video_prompt = Column(Text, nullable=True)  # 生成该视频时使用的提示词，可编辑后重新生成

    def __repr__(self):
        return f"<Scene {self.id} - {self.location}>"
