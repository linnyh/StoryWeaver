# Backend RAG 模块

> [根目录](../../CLAUDE.md) > [backend](../) > **app/rag**

---

## 模块职责

RAG (Retrieval-Augmented Generation) 向量检索服务，基于 **ChromaDB** 实现长期记忆存储与检索。

**核心功能**:
- 存储角色设定、世界观、场景摘要为向量
- 按 `novel_id` 隔离检索，避免跨书混用
- 为场景生成提供上下文增强

---

## 数据集合

| 集合名 | 类型 | 说明 |
|-------|------|------|
| `characters` | character | 角色信息向量 |
| `lore` | lore | 世界观设定向量 |
| `scene_summaries` | summary | 场景摘要向量 |

---

## RAG 服务类

```python
class RAGService:
    def __init__(self, persist_directory: Optional[str] = None):
        """初始化 ChromaDB 客户端"""
        self.client = chromadb.PersistentClient(path=persist_directory)
        self._init_collections()

    def add_knowledge(
        self,
        text: str,           # 待向量化的文本
        doc_id: str,         # 文档 ID
        type: str,           # character/lore/summary
        metadata: Dict       # 附加元数据 (含 novel_id)
    ):
        """添加知识到向量数据库 (Upsert)"""

    def retrieve_context(
        self,
        query: str,          # 查询文本
        type: str,           # 检索类型
        top_k: int = 3,      # 返回数量
        novel_id: Optional[str] = None,  # 小说 ID 隔离
    ) -> List[Dict]:
        """检索相关上下文"""

    def retrieve_all_by_novel(
        self,
        novel_id: str,
        type: str,
        top_k: int = 10
    ) -> List[Dict]:
        """获取某小说的所有相关知识"""

    def delete_knowledge(doc_id: str, type: str):
        """删除知识"""

    def clear_collection(type: str):
        """清空集合"""
```

---

## 数据模型

### 向量元数据结构

```json
{
  "id": "scene_summary_xxx",
  "text": "场景摘要内容...",
  "metadata": {
    "type": "scene_summary",
    "novel_id": "xxx",
    "chapter_id": "xxx",
    "scene_id": "xxx"
  }
}
```

### 检索结果格式

```json
{
  "id": "doc_id",
  "text": "检索到的文本",
  "distance": 0.123,  // 向量距离
  "metadata": {}
}
```

---

## novel_id 隔离机制

**重要**: 所有检索接口均支持 `novel_id` 参数，确保知识隔离。

```python
# 检索时按 novel_id 过滤
kwargs["where"] = {"novel_id": novel_id}
results = collection.query(**kwargs)
```

**测试覆盖**: `test_rag_novel_isolation.py` 验证隔离正确性。

---

## 与场景生成的集成

```python
# scene_generator.py 中构建上下文
async def _build_context(scene, db):
    # 1. 获取角色向量
    char_contexts = rag_service.retrieve_context(
        query=f"{character.name} {character.bio}",
        type="character",
        top_k=1,
        novel_id=novel_id
    )

    # 2. 获取世界观向量
    lore_contexts = rag_service.retrieve_context(
        query=scene.beat_description,
        type="lore",
        top_k=3,
        novel_id=novel_id
    )

    # 3. 注入到 Prompt
```

---

## 配置

```python
# app/config.py
chromadb_persist_directory: str = "./chroma_data"
embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
```

---

## 全局单例

```python
# app/rag/__init__.py
rag_service = RAGService()
```

---

## 相关文件

| 文件 | 说明 |
|------|------|
| `service.py` | RAGService 实现 (~174 行) |
| `__init__.py` | 单例导出 |
| `scene_postprocess.py` | RAG 同步调用方 |
| `generator.py` | RAG 检索调用方 |

---

## 变更记录

- **2026-03-24**: 初始化文档，补充 novel_id 隔离说明
