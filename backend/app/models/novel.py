"""Novel 模型"""
import uuid
from sqlalchemy import Column, String, Text, Integer
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from app.database import Base


class Novel(Base):
    """小说表"""
    __tablename__ = "novels"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    premise = Column(Text, nullable=True)  # 一句话故事核
    genre = Column(String(50), nullable=True)  # 玄幻/科幻/言情等
    tone = Column(String(50), nullable=True)  # 幽默/严肃/黑暗
    philosophical_theme = Column(Text, nullable=True)  # 哲学思想内核
    worldbuilding = Column(Text, nullable=True)  # 世界观设定

    def __repr__(self):
        return f"<Novel {self.title}>"
