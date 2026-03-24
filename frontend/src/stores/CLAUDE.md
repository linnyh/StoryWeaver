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

  // 当前章节
  currentChapter: null,

  // 场景列表
  scenes: [],

  // 当前场景
  currentScene: null,

  // 加载状态
  loading: false,

  // 错误信息
  error: null
})
```

### Actions

```javascript
// 小说操作
async fetchNovel(id)
async createNovel(data)
async updateNovel(id, data)
async deleteNovel(id)

// 章节操作
async fetchChapters(novelId)
async createChapter(data)
async updateChapter(id, data)
async deleteChapter(id)

// 角色操作
async fetchCharacters(novelId)
async createCharacter(data)
async updateCharacter(id, data)
async deleteCharacter(id)
async generatePortrait(characterId)

// 场景操作
async fetchScenes(chapterId)
async createScene(data)
async updateScene(id, data)
async deleteScene(id)
async generateSceneContent(sceneId, onChunk, onDone)
async generateSceneImage(sceneId)

// 关系操作
async fetchRelationships(novelId)
```

### Getters

```javascript
// 按角色 ID 查找角色
getCharacterById: (state) => (id) => {
  return state.characters.find(c => c.id === id)
}

// 按章节 ID 查找章节
getChapterById: (state) => (id) => {
  return state.chapters.find(c => c.id === id)
}

// 小说统计
novelStats: (state) => {
  return {
    chapterCount: state.chapters.length,
    characterCount: state.characters.length,
    sceneCount: state.scenes.length
  }
}
```

---

## 使用示例

```javascript
import { useNovelStore } from '@/stores/novel'

const store = useNovelStore()

// 获取小说
await store.fetchNovel('xxx')

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
const { currentNovel, loading } = storeToRefs(store)
```

---

## 相关文件

| 文件 | 说明 |
|------|------|
| `novel.js` | 小说状态管理 (~300 行) |
| `../api/index.js` | API 调用封装 |
| `../views/WriterPage.vue` | 主要使用方 |

---

## 变更记录

- **2026-03-24**: 初始化文档
