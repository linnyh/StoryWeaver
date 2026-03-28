# Frontend Stores 模块

> [根目录](../../../CLAUDE.md) > [frontend](../../) > **src/stores**

---

## 模块职责

Pinia 状态管理 - 管理前端应用的可复用状态。

---

## Store 列表

| 文件 | 名称 | 核心职责 |
|------|------|---------|
| `novel.js` | `useNovelStore` | 小说、章节、角色、场景状态管理 |

---

## useNovelStore

### State

```javascript
state: () => ({
  // 当前小说
  currentNovel: null,

  // 章节列表
  chapters: [],

  // 角色列表
  characters: [],

  // 关系列表
  relationships: [],

  // 世界观列表
  lores: [],

  // 当前章节
  currentChapter: null,

  // 场景列表
  scenes: [],

  // 当前场景
  currentScene: null,
})
```

### Actions

```javascript
// 小说操作
async loadNovel(id)                    // 加载小说
async createNovel(data)                 // 创建小说

// 章节操作
async loadChapters(novelId)            // 加载章节列表

// 角色操作
async loadCharacters(novelId)          // 加载角色列表

// 关系操作
async loadRelationships(novelId)       // 加载关系列表

// 世界观操作
async loadLores(novelId)               // 加载世界观列表

// 场景操作
async loadScenes(chapterId)            // 加载场景列表
async updateScene(sceneId, data)       // 更新场景内容

// 生成操作
async generateOutline(novelId, data)   // 生成大纲
async generateBeats(chapterId, data)   // 生成场景细纲
async summarizeChapter(chapterId)       // 生成章节摘要

// 导出
async exportNovel(novelId)             // 导出小说

// 状态管理
function reset()                        // 重置所有状态
```

### 使用示例

```javascript
import { useNovelStore } from '@/stores/novel'

const store = useNovelStore()

// 加载小说
await store.loadNovel('xxx')

// 创建章节
await store.createChapter({
  novel_id: store.currentNovel.id,
  title: '第一章：开端'
})

// SSE 流式生成场景
store.generateSceneContent(
  sceneId,
  (chunk) => {
    // 处理每个 token
    console.log('token:', chunk)
  },
  () => {
    // 完成
    console.log('done')
  }
)
```

---

## 最佳实践

1. **组件中使用**: 在 `setup()` 中通过 `useNovelStore()` 调用
2. **响应式**: 直接解构 state，需使用 `storeToRefs` 保持响应式
3. **错误处理**: action 内部捕获错误并更新 `state.error`
4. **加载状态**: 长时间操作前设置 `state.loading = true`

```javascript
import { storeToRefs } from 'pinia'
import { useNovelStore } from '@/stores/novel'

const store = useNovelStore()
const { currentNovel, chapters } = storeToRefs(store)
```

---

## 相关文件

| 文件 | 说明 |
|------|------|
| `novel.js` | 小说状态管理 |
| `../api/index.js` | API 调用封装 |
| `../views/WriterPage.vue` | 主要使用方 |
| `../views/NovelPage.vue` | 小说详情页使用方 |

---

## 变更记录

- **2026-03-24**: 初始化文档
- **2026-03-28**: 修复文档与实现不一致问题（使用 load* 命名而非 fetch*）

---
