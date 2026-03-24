"""场景版本表 - 用于历史与回滚"""
import uuid
from sqlalchemy import Column, String, Text, Integer, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.database import Base


class SceneVersion(Base):
    """场景内容历史版本，每场景最多保留 20 条"""
    __tablename__ = "scene_versions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scene_id = Column(String(36), ForeignKey("scenes.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<SceneVersion {self.id} scene={self.scene_id}>"
