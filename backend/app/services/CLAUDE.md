# Backend Services 模块

> [根目录](../../CLAUDE.md) > [backend](../) > **app/services**

---

## 模块职责

业务逻辑层 (Business Logic Layer)，包含 **Usecase** (用例编排) 和 **AI 服务** (LLM 调用、图像生成、视频生成)。

**设计原则**:
- `*_usecases.py` - 业务用例编排，事务边界
- `*_service.py` - 外部 API 调用服务
- `analyzer.py` - AI 分析服务

---

## 服务列表

### Usecase 层

| 文件 | 职责 |
|------|------|
| `novel_usecases.py` | 小说业务：创建/大纲生成/导出 |
| `chapter_usecases.py` | 章节业务：CRUD/节拍生成/摘要 |
| `scene_usecases.py` | 场景业务：SSE 生成/版本管理/摘要/RAG 更新 |

### AI 服务层

| 文件 | 职责 |
|------|------|
| `generator.py` | LLM 客户端、大纲生成器、场景生成器、摘要生成器、AI 助手 |
| `scene_image_service.py` | MiniMax 分镜配图生成 |
| `scene_video_service.py` | MiniMax 分镜视频生成 (S2V-01 主体参考) |

### 分析服务层

| 文件 | 职责 |
|------|------|
| `scene_postprocess.py` | 场景后处理：摘要生成/状态分析/关系更新/RAG 同步 |
| `state_analyzer.py` | 角色状态分析 (境界/物品/技能) |
| `relationship_analyzer.py` | 角色关系分析 (好感度/矛盾) |

---

## 核心服务详解

### Generator (LLM 客户端)

```python
class LLMClient:
    """支持 OpenAI 兼容 API + MiniMax"""
    api_key: str
    base_url: str
    model: str
    writing_model: str   # 写作专用模型
    summary_model: str   # 摘要专用模型
    editorial_model: str # 审稿专用模型

    async def generate(prompt, model_override=None) -> str
    async def generate_stream(prompt, model_override=None) -> AsyncGenerator[str]

class OutlineGenerator:
    async def generate_outline(novel_id, premise, genre, tone, num_chapters)
    async def generate_outline_stream(novel_id) -> AsyncGenerator[str]

class SceneGenerator:
    async def generate_scene_content(scene_id, db, enable_editorial=False) -> AsyncGenerator[Dict]
    # 返回: {"type": "system"|"content"|"log", "content": "..."}

class Summarizer:
    async def generate_summary(content, model_override=None) -> str
```

### Scene Usecases (场景用例)

```python
async def create_scene(db, chapter_id, data) -> Scene
async def update_scene_and_schedule_tasks(scene_id, scene_update_data, background_tasks, db)
async def summarize_scene_content(scene_id, db) -> Dict
# 关键：场景更新后触发 BackgroundTasks:
#   1. analyze_state_and_relationships - 状态/关系分析
#   2. summarize_scene - 摘要生成 + RAG 同步
```

### Scene Postprocess (后处理)

```python
async def analyze_state_and_relationships(scene_id):
    """分析角色状态和关系更新"""
    # 1. 获取场景相关角色
    # 2. 调用 state_analyzer 分析每个角色
    # 3. 调用 relationship_analyzer 分析角色关系
    # 4. 更新数据库

async def summarize_scene(scene_id):
    """生成场景摘要并同步 RAG"""
    # 1. 调用 LLM 生成 200 字摘要
    # 2. 更新 scene.summary
    # 3. 调用 rag_service.add_knowledge
```

---

## 外部 API 集成

### MiniMax API

**图像生成** (`scene_image_service.py`):
- 端点: `https://api.minimaxi.com/v1/images_generation`
- 模型: `image-01`
- 支持主体参考 (角色肖像一致性)

**视频生成** (`scene_video_service.py`):
- 端点: `https://api.minimaxi.com/vv1/video_generation`
- 模型: `S2V-01` (主体参考，6秒 1080P)
- 流程: 创建任务 -> 轮询状态 -> 获取下载 URL

---

## 全局单例

```python
# 在 generator.py 末尾
llm_client = LLMClient()
outline_generator = OutlineGenerator(llm_client)
scene_generator = SceneGenerator(llm_client)
summarizer = Summarizer(llm_client)
assistant = Assistant(llm_client)
```

---

## 相关文件

| 文件 | 说明 |
|------|------|
| `generator.py` | LLM 核心，~840 行 |
| `scene_usecases.py` | 场景用例，~422 行 |
| `scene_postprocess.py` | 后处理编排 |
| `config.py` | 配置管理 |
| `rag/service.py` | RAG 服务 (向量检索) |

---

## 变更记录

- **2026-03-24**: 初始化文档，补充 MiniMax API 集成说明
