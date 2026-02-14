**AI 长篇小说自动写作系统**的完整开发文档。

长篇小说的核心难点在于**上下文记忆（Context Memory）和逻辑一致性（Logical Consistency）**。普通的 AI 对话无法记住 10 万字前的内容。因此，这个系统必须采用 **"RAG (检索增强生成) + 分层大纲 (Hierarchical Outlining)"** 的架构。


---

# 开发文档：Project "StoryWeaver" (AI 长篇小说生成系统)

## 1. 项目概述 (Project Overview)

本项目旨在开发一个辅助用户创作长篇小说的 Web 系统。它不只是一次性生成文本，而是通过**结构化工程**的方法来写小说。

### 核心工作流 (The Workflow)

1. **世界观设定 (World Building)**: 用户定义世界背景、力量体系、核心冲突。
2. **角色设计 (Character Design)**: 创建角色卡片（外貌、性格、说话风格），并存入向量数据库。
3. **大纲生成 (Structure)**:
* Level 1: 全书大纲 (3-5 幕结构)。
* Level 2: 章节列表。
* Level 3: 场景细纲 (Scene Beats) —— 这是 AI 写作的直接指导指令。


4. **正文生成 (Drafting)**: AI 逐个场景写作。在写作时，系统会自动检索相关的角色设定和前文摘要，确保逻辑连贯。
5. **人工干预 (Human Loop)**: 用户可以在生成前修改细纲，或在生成后修改正文。

---

## 2. 技术栈 (Tech Stack)

### Frontend (前端)

* **Framework**: Vue 3 + Vite
* **UI Library**: Element Plus / Naive UI
* **Rich Text Editor**: **Tiptap** (必须支持 Markdown 和富文本混合，用于小说阅读/编辑)
* **State Management**: Pinia (管理当前书籍的上下文)

### Backend (后端)

* **Framework**: Python FastAPI
* **LLM Orchestration**: **LangChain** (用于管理提示词模板和链式调用)
* **Vector Database**: **ChromaDB** 或 **FAISS** (本地运行，用于存储角色详情、世界观、已写章节的摘要，实现长期记忆)
* **Database**: SQLite / PostgreSQL (存储书籍结构、章节内容)

---

## 3. 核心数据结构设计 (Data Architecture)

这部分对长篇小说至关重要，请严格定义。

### 1. `Novel` (小说表)

* `id`: UUID
* `title`: String
* `premise`: Text (一句话故事核)
* `genre`: String (玄幻/科幻/言情等)
* `tone`: String (幽默/严肃/黑暗)

### 2. `Character` (角色表 - RAG 核心)

* `id`: UUID
* `novel_id`: FK
* `name`: String
* `bio`: Text (详细传记)
* `personality`: Text (性格特征，用于指导 AI 语气)
* `appearance`: Text (外貌描写，用于保持一致性)
* *Note: 这些字段内容的 Vector Embeddings 需存入 ChromaDB。*

### 3. `Chapter` (章节表)

* `id`: UUID
* `novel_id`: FK
* `order_index`: Int
* `title`: String
* `summary`: Text (本章发生内容的摘要，用于后续章节的上下文)

### 4. `Scene` (场景/细纲表 - 生成的最小单位)

* `id`: UUID
* `chapter_id`: FK
* `order_index`: Int
* `location`: String
* `characters_present`: List[CharacterID] (当前场景在场人员)
* `beat_description`: Text (详细的动作指令，例如："主角走进酒馆，发现反派坐在角落，两人进行了眼神对峙。")
* `content`: Text (AI 生成的最终正文)
* `status`: Enum (Draft, Approved)

---

## 4. 后端核心逻辑 (Backend Logic)

### 模块 A: 上下文组装机 (The Context Assembler)

在生成任何一段文字前，必须构建 Prompt。不能只给 AI 看标题。

```python
# 伪代码示例
def build_writing_prompt(scene_id):
    scene = get_scene(scene_id)
    
    # 1. 获取前情提要 (Rolling Window)
    prev_summary = get_last_5_scenes_summary()
    
    # 2. RAG 检索：获取在场角色的详细设定
    active_characters = vector_db.query(scene.characters_present)
    
    # 3. RAG 检索：检索与当前场景描述相关的世界观 (例如：检索"酒馆"的设定)
    lore_context = vector_db.similarity_search(scene.beat_description)
    
    # 4. 组装 Prompt
    prompt = f"""
    你是一个畅销书作家。请根据以下信息写出一段精彩的小说正文。
    
    [风格]: {novel.tone}
    [前情提要]: {prev_summary}
    [在场角色]: {active_characters}
    [相关设定]: {lore_context}
    
    [当前指令]: {scene.beat_description}
    
    要求：多用通过动作描写表现心理，禁止流水账。写 800-1200 字。
    """
    return prompt

```

### 模块 B: 摘要生成器 (Auto-Summarizer)

每次生成完一个场景（Scene）的正文后，触发一个后台任务：

* **Input**: 新生成的正文 (2000字)。
* **Task**: "请将这段文字浓缩为 200 字的摘要，保留关键剧情点和物品获得情况。"
* **Output**: 存入 `Scene.summary` 和 向量数据库。
* *目的*: 随着小说变长，我们只给 AI 喂摘要，而不是全文，解决 Token 上限问题。

---

## 5. API 接口定义 (API Specification)

### Novel & Structure

* `POST /api/novels/init`: 创建小说，生成初始设定。
* `POST /api/novels/{id}/outline`: AI 根据故事核生成章节列表。
* `POST /api/chapters/{id}/beats`: AI 将一章拆解为 4-8 个具体的场景细纲 (Beats)。

### Knowledge Base (RAG)

* `POST /api/characters`: 创建角色（自动生成 Embedding）。
* `POST /api/lore`: 添加世界观设定（自动生成 Embedding）。

### Writing

* `POST /api/scenes/{id}/generate`: **核心接口**。
* 触发流式生成 (Server-Sent Events / SSE)，前端可以看到字一个个打出来。


* `PUT /api/scenes/{id}/content`: 用户手动修改生成的正文。

---

## 6. 前端界面设计 (UI Design)

### 界面 1: "上帝视角" (The Architect View)

* 左侧：树状目录（卷 -> 章 -> 场景）。
* 中间：思维导图或卡片流，显示每一章的简要梗概。
* 右侧：角色列表与世界观笔记。

### 界面 2: "专注写作模式" (The Writer View)

* **三栏布局**：
* **左栏 (Context)**: 显示当前场景的 "细纲指令" 和 "上一章摘要"。
* **中栏 (Editor)**: Tiptap 编辑器。AI 生成的内容流式填充在此。支持 Markdown。
* **右栏 (Assistant)**: 一个 Chat 窗口，可以对 AI 说 "把这段改得更悲伤一点" 或 "这里插入一段环境描写"。



---

## 7. 分步实施提示 (Roadmap)

请按以下步骤指示 Claude Code：

**Step 1: 后端基础与数据模型**

> "初始化 FastAPI 项目。安装 `langchain`, `chromadb`, `sqlalchemy`。定义 Novel, Character, Chapter, Scene 的 SQLAlchemy 模型。请特别注意 Character 和 Scene 表需要有存储文本摘要的字段。"

**Step 2: 向量数据库集成 (RAG)**

> "编写一个 `RAGService` 类。
> 1. 实现 `add_knowledge(text, type)` 方法：将文本向量化并存入 ChromaDB。
> 2. 实现 `retrieve_context(query)` 方法：根据 query 检索最相关的 3 条背景信息。"
> 
> 

**Step 3: 大纲生成逻辑**

> "实现 'IDE 到 大纲' 的逻辑。创建一个 API，接收 '故事想法'，调用 LLM 生成 10 个章节标题和简述，并存入数据库。"

**Step 4: 场景细化与正文生成 (核心)**

> "实现 `StoryGenerator` Service。
> 1. 编写 Prompt 模板，将 '上一幕摘要' + '角色卡' + '当前幕指令' 组合。
> 2. 创建生成接口，调用 LLM 并返回流式响应（Streaming Response）。"
> 
> 

**Step 5: 前端编辑器实现**

> "使用 Vue 3 和 Tiptap 搭建写作界面。左侧显示章节树，右侧是编辑器。实现与后端流式接口的对接，让文字像打字机一样出现。"

**Step 6: 自动摘要闭环**

> "添加一个 Celery 任务或后台函数。当用户点击 '保存' 或 '确认' 某一幕内容后，自动调用 LLM 将该幕正文压缩成 200 字摘要，并更新到向量数据库中，以便后续章节生成时调用。"

---

### 关键提示 (Pro Tips for the User)

模型建议：

* **Drafting (写正文)**: 使用 `MiniMax2.1`。
* **Summarizing (做摘要)**: 使用 `MiniMax2.1` (便宜、速度快，适合处理大量后台任务)。
* **Embedding**: 使用 `text-embedding-3-small` 或开源的 `HuggingFace` 模型 (本地运行)。