# Backend API 模块

> [根目录](../../CLAUDE.md) > [backend](../) > **app/api**

---

## 模块职责

RESTful API 路由定义层，负责接收 HTTP 请求、参数校验、响应组装，并调用下层 `services` 完成业务逻辑。

**设计原则**: 薄路由 - API 层仅做接口适配，不含复杂业务逻辑。

---

## 路由列表

| 路由文件 | 前缀 | 核心接口 |
|---------|------|---------|
| `novel.py` | `/api/novels` | 创建/查询/更新/删除小说，生成大纲，导出，RAG 摘要管理 |
| `character.py` | `/api/characters` | 角色 CRUD，肖像生成 |
| `chapter.py` | `/api/chapters` | 章节 CRUD，生成节拍 (Beats)，章节摘要 |
| `scene.py` | `/api/scenes` | 场景 CRUD，SSE 流式生成，配图/视频生成，版本管理 |
| `lore.py` | `/api/lore` | 世界观设定 CRUD |
| `settings.py` | `/api/settings` | 系统配置读写 |
| `relationship.py` | `/api/relationships` | 角色关系查询 |
| `scene_chat.py` | `/api/scenes/{id}/chat` | 场景级 AI 对话 |

---

## 核心 API 端点

### Novel API

```
POST   /api/novels/                    # 创建小说
GET    /api/novels/                    # 列出小说
GET    /api/novels/{id}                # 获取小说详情
PUT    /api/novels/{id}                # 更新小说
DELETE /api/novels/{id}                # 删除小说
POST   /api/novels/{id}/outline        # AI 生成大纲
GET    /api/novels/stats               # 统计信息
GET    /api/novels/{id}/export         # 导出全文 (TXT)
GET    /api/novels/{id}/rag/summaries  # 获取 RAG 摘要
PUT    /api/novels/{id}/rag/summaries/{doc_id}  # 更新 RAG 摘要
DELETE /api/novels/{id}/rag/summaries/{doc_id}  # 删除 RAG 摘要
```

### Scene API (核心)

```
POST   /api/scenes/                              # 创建场景
GET    /api/scenes/?chapter_id=xxx               # 列出场景
GET    /api/scenes/{id}                          # 获取场景
PUT    /api/scenes/{id}                          # 更新场景
DELETE /api/scenes/{id}                          # 删除场景
POST   /api/scenes/{id}/generate                 # SSE 流式生成正文
POST   /api/scenes/{id}/generate_image           # 生成分镜配图
POST   /api/scenes/{id}/generate_video          # 创建视频任务
GET    /api/scenes/{id}/video_status            # 轮询视频状态
POST   /api/scenes/{id}/summarize               # 生成场景摘要
GET    /api/scenes/{id}/versions                # 获取历史版本
POST   /api/scenes/{id}/restore_version         # 恢复历史版本
POST   /api/scenes/{id}/chat                    # AI 对话 (SSE)
```

---

## 入口与启动

- **主入口**: `backend/app/main.py`
- **启动命令**: `uvicorn app.main:app --reload`
- **API 文档**: `http://localhost:8000/docs` (Swagger UI)

---

## 关键依赖

- **FastAPI** - Web 框架
- **SQLAlchemy Async** - 异步 ORM
- **Pydantic** - 请求/响应数据验证
- **aiohttp** - 异步 HTTP 客户端

---

## 中间件配置

```python
# 请求 ID 中间件 - 注入 X-Request-ID header
# CORS 中间件 - 允许 localhost:5173, localhost:3000
# 全局异常处理器 - 统一错误响应格式
```

---

## 错误响应格式

```json
{
  "detail": "错误描述",
  "request_id": "uuid",
  "error": {
    "type": "NotFoundError",
    "message": "Scene not found"
  }
}
```

---

## 相关文件

| 文件 | 说明 |
|------|------|
| `main.py` | FastAPI 应用入口，路由注册 |
| `scene.py` | 场景 API（含 SSE 流式生成核心逻辑） |
| `novel.py` | 小说 API（含 RAG 摘要管理） |
| `errors.py` | 全局异常处理器 |
| `logging.py` | 请求 ID 日志追踪 |

---

## 变更记录

- **2026-03-24**: 初始化文档
