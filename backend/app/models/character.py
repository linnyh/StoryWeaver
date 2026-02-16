"""Character 模型 - RAG 核心"""
import uuid
from sqlalchemy import Column, String, Text, ForeignKey, JSON
from app.database import Base


class Character(Base):
    """角色表"""
    __tablename__ = "characters"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    novel_id = Column(String(36), ForeignKey("novels.id"), nullable=False)
    name = Column(String(100), nullable=False)
    bio = Column(Text, nullable=True)  # 详细传记
    personality = Column(Text, nullable=True)  # 性格特征
    appearance = Column(Text, nullable=True)  # 外貌描写
    role = Column(String(50), nullable=True)  # 主角/配角/反派等
    power_state = Column(JSON, nullable=True)  # 力量体系与资产状态机

    def __repr__(self):
        return f"<Character {self.name}>"
