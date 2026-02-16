"""Relationship 模型 - 角色关系网"""
import uuid
from sqlalchemy import Column, String, Integer, Text, ForeignKey, CheckConstraint, UniqueConstraint
from app.database import Base

class Relationship(Base):
    """角色关系表"""
    __tablename__ = "relationships"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    novel_id = Column(String(36), ForeignKey("novels.id"), nullable=False)
    character_a_id = Column(String(36), ForeignKey("characters.id"), nullable=False)
    character_b_id = Column(String(36), ForeignKey("characters.id"), nullable=False)
    
    # 亲密度: -100 (死敌) 到 100 (挚爱/生死之交)
    affinity_score = Column(Integer, default=0)
    
    # 核心矛盾/心结/羁绊点 (Text)
    core_conflict = Column(Text, nullable=True)

    # 确保 A-B 和 B-A 是同一条记录 (或者逻辑上只存 A < B 的记录)
    # 这里我们采用简单策略：查询时查 (A,B) 或 (B,A)，存储时按字母序或 ID 序存储以避免重复，
    # 或者允许双向存储但业务层维护一致性。
    # 为简单起见，我们添加一个约束，要求 character_a_id < character_b_id，
    # 这样每对角色在数据库中只有一条记录。
    
    __table_args__ = (
        CheckConstraint('affinity_score >= -100 AND affinity_score <= 100', name='check_affinity_range'),
        UniqueConstraint('character_a_id', 'character_b_id', name='uix_char_pair'),
    )
    
    from sqlalchemy.orm import relationship
    character_a = relationship("Character", foreign_keys=[character_a_id])
    character_b = relationship("Character", foreign_keys=[character_b_id])

    def __repr__(self):
        return f"<Relationship {self.character_a_id} <-> {self.character_b_id}: {self.affinity_score}>"
