# StoryWeaver - AI 长篇小说生成系统

一个基于 RAG + 分层大纲架构的 AI 小说创作系统。

## 功能特性

- 📚 **小说管理**：创建、编辑、删除小说
- 👥 **角色系统**：创建角色卡片，存入向量数据库
- 📖 **大纲生成**：AI 自动生成章节大纲
- ✍️ **场景拆分**：将章节拆解为具体的场景细纲
- 🤖 **AI 写作**：流式生成小说正文
- 🔄 **自动摘要**：生成场景摘要并存入向量库，供后续章节检索

## 快速开始

### 1. 安装依赖

```bash
# 后端依赖
cd backend
pip install -r requirements.txt

# 前端依赖
cd frontend
npm install
```

### 2. 配置环境变量

在 `backend/` 目录下创建 `.env` 文件：

```env
# MiniMax API (可选，使用模拟响应则不需要)
MINIMAX_API_KEY=your_api_key_here
MINIMAX_BASE_URL=https://api.minimax.chat/v1

# OpenAI API (可选)
OPENAI_API_KEY=your_api_key_here

# 数据库配置 (可选)
DATABASE_URL=sqlite+aiosqlite:///./storyweaver.db
```

### 3. 启动服务

```bash
# 启动后端 (在 backend 目录)
uvicorn app.main:app --reload --port 8000

# 启动前端 (在 frontend 目录)
npm run dev
```

### 4. 访问系统

- 前端：http://localhost:5173
- API 文档：http://localhost:8000/docs

## 测试

```bash
# 后端单元测试
cd backend
python test_system.py

# API 测试 (需要先启动服务器)
python test_api.py
```

## 项目结构

```
StoryWeaver/
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── api/            # REST API 路由
│   │   ├── models/         # SQLAlchemy 模型
│   │   ├── services/       # 业务逻辑 (LLM/大纲/摘要)
│   │   └── rag/           # 向量数据库服务
│   └── test_*.py           # 测试脚本
│
├── frontend/               # Vue 3 前端
│   ├── src/
│   │   ├── views/         # 页面组件
│   │   ├── components/    # 通用组件
│   │   ├── stores/        # Pinia 状态管理
│   │   └── api/           # API 客户端
│   └── dist/              # 构建产物
│
└── DEV_DOC.md             # 开发文档
```

## API 接口

### 小说
- `POST /api/novels/` - 创建小说
- `GET /api/novels/` - 列出小说
- `GET /api/novels/{id}` - 获取小说详情
- `POST /api/novels/{id}/outline` - 生成大纲

### 章节
- `POST /api/chapters/` - 创建章节
- `POST /api/chapters/{id}/beats` - 生成场景细纲

### 场景
- `POST /api/scenes/{id}/generate` - 流式生成正文 (SSE)
- `POST /api/scenes/{id}/summarize` - 生成摘要

### 角色
- `POST /api/characters/` - 创建角色

## 技术栈

- **后端**：FastAPI + SQLAlchemy + ChromaDB + LangChain
- **前端**：Vue 3 + Vite + Pinia + Tiptap
- **LLM**：支持 OpenAI / MiniMax

## 许可证

MIT
