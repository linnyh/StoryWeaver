"""Chapter 模型"""
import uuid
from sqlalchemy import Column, String, Text, Integer, ForeignKey
from app.database import Base


class Chapter(Base):
    """章节表"""
    __tablename__ = "chapters"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    novel_id = Column(String(36), ForeignKey("novels.id"), nullable=False)
    order_index = Column(Integer, nullable=False, default=0)
    title = Column(String(255), nullable=True)
    summary = Column(Text, nullable=True)  # 本章摘要

    def __repr__(self):
        return f"<Chapter {self.title}>"
