# Backend Models 模块

> [根目录](../../CLAUDE.md) > [backend](../) > **app/models**

---

## 模块职责

SQLAlchemy 数据模型定义，建立数据库表结构与 Python 对象之间的映射。

**设计原则**: 每个模型对应一个数据库表，使用 `declarative_base()` 声明式定义。

---

## 数据模型列表

| 模型文件 | 表名 | 核心字段 |
|---------|------|---------|
| `novel.py` | `novels` | id, title, premise, genre, tone, philosophical_theme, worldbuilding |
| `character.py` | `characters` | id, novel_id, name, bio, personality, appearance, role, power_state, portrait_url |
| `chapter.py` | `chapters` | id, novel_id, order_index, title, summary |
| `scene.py` | `scenes` | id, chapter_id, order_index, location, characters_present, beat_description, content, summary, status, tension_level, emotional_target, image_url, image_prompts, video_task_id, video_url, video_prompt |
| `scene_version.py` | `scene_versions` | id, scene_id, content, created_at |
| `lore.py` | `lore` | id, novel_id, title, content, category |
| `system.py` | `system_config` | id, key, value |
| `relationship.py` | `relationships` | id, novel_id, character_a_id, character_b_id, affinity_score, core_conflict |

---

## 核心模型详解

### Novel (小说)

```python
class Novel(Base):
    __tablename__ = "novels"
    id = Column(String(36), primary_key=True)
    title = Column(String(255), nullable=False)
    premise = Column(Text)  # 一句话故事核
    genre = Column(String(50))  # 玄幻/科幻/言情等
    tone = Column(String(50))  # 幽默/严肃/黑暗
    philosophical_theme = Column(Text)  # 哲学思想内核
    worldbuilding = Column(Text)  # 世界观设定
```

### Scene (场景)

```python
class Scene(Base):
    __tablename__ = "scenes"
    id = Column(String(36), primary_key=True)
    chapter_id = Column(String(36), ForeignKey("chapters.id"))
    order_index = Column(Integer, default=0)  # 场景顺序
    location = Column(String(255))  # 场景地点
    characters_present = Column(JSON)  # 在场角色 ID 列表
    beat_description = Column(Text)  # 动作指令 (Beat)
    content = Column(Text)  # AI 生成的正文
    summary = Column(Text)  # 场景摘要
    status = Column(String(20), default="draft")  # draft/approved
    tension_level = Column(Integer)  # 情绪张力 1-10
    emotional_target = Column(String(255))  # 情绪传达目标
    image_url = Column(String(500))  # 分镜配图
    image_prompts = Column(JSON)  # 分镜 prompt 列表
    video_task_id = Column(String(128))  # 视频任务 ID
    video_url = Column(String(512))  # 视频地址
    video_prompt = Column(Text)  # 视频提示词
```

### SceneVersion (场景版本)

```python
class SceneVersion(Base):
    __tablename__ = "scene_versions"
    id = Column(String(36), primary_key=True)
    scene_id = Column(String(36), ForeignKey("scenes.id", ondelete="CASCADE"))
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # 每场景最多保留 20 条
```

### Character (角色)

```python
class Character(Base):
    __tablename__ = "characters"
    id = Column(String(36), primary_key=True)
    novel_id = Column(String(36), ForeignKey("novels.id"))
    name = Column(String(100), nullable=False)
    bio = Column(Text)  # 详细传记
    personality = Column(Text)  # 性格特征
    appearance = Column(Text)  # 外貌描写
    role = Column(String(50))  # 主角/配角/反派
    power_state = Column(JSON)  # 力量体系状态机
    portrait_url = Column(String(512))  # AI 肖像图
```

### Relationship (角色关系)

```python
class Relationship(Base):
    __tablename__ = "relationships"
    id = Column(String(36), primary_key=True)
    novel_id = Column(String(36), ForeignKey("novels.id"))
    character_a_id = Column(String(36), ForeignKey("characters.id"))
    character_b_id = Column(String(36), ForeignKey("characters.id"))
    affinity_score = Column(Integer, default=0)  # 好感度 -100~100
    core_conflict = Column(Text)  # 核心矛盾/心结
```

---

## 数据库配置

- **数据库**: SQLite (开发) / PostgreSQL (生产)
- **ORM**: SQLAlchemy 2.0+ 异步模式
- **连接**: `aiosqlite` 异步驱动
- **初始化**: `app/database.py` 的 `init_db()` 函数

```python
# 关键配置
DATABASE_URL = "sqlite+aiosqlite:///./storyweaver.db"
# WAL 模式优化并发
await conn.execute(sqlalchemy.text("PRAGMA journal_mode=WAL;"))
```

---

## 相关文件

| 文件 | 说明 |
|------|------|
| `__init__.py` | 模型导出汇总 |
| `database.py` | 数据库连接配置 |
| `scene.py` | 场景模型（含配图/视频字段） |
| `scene_version.py` | 场景历史版本模型 |

---

## 变更记录

- **2026-03-24**: 初始化文档，补充 SceneVersion 模型说明
