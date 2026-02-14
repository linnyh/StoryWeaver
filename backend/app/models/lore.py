"""Lore 模型 - 世界观设定"""
import uuid
from sqlalchemy import Column, String, Text, ForeignKey
from app.database import Base


class Lore(Base):
    """世界观设定表"""
    __tablename__ = "lores"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    novel_id = Column(String(36), ForeignKey("novels.id"), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)  # 力量体系/地点/物品等

    def __repr__(self):
        return f"<Lore {self.title}>"
