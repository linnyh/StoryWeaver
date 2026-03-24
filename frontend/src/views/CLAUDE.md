# Frontend Views 模块

> [根目录](../../../CLAUDE.md) > [frontend](../../) > **src/views**

---

## 模块职责

页面级 Vue 组件，定义应用的主要视图/路由页面。

---

## 页面列表

| 文件 | 路由 | 核心功能 |
|------|------|---------|
| `HomePage.vue` | `/` | 首页 - 小说列表、统计信息、帮助对话框 |
| `NovelPage.vue` | `/novel/:id` | 小说详情 - 章节管理、角色关系图谱 |
| `WriterPage.vue` | `/write/:id` | 写作界面 - Tiptap 编辑器、场景生成、AI 对话 |
| `RagPage.vue` | `/rag/:id` | RAG 管理 - 摘要列表、编辑、同步状态 |
| `SettingsPage.vue` | `/settings` | 设置页 - API 配置、模型配置 |

---

## 核心页面详解

### HomePage (首页)

```vue
<!-- 主要功能 -->
<template>
  <!-- 小说卡片列表 -->
  <!-- 统计信息 (字数/章节/角色) -->
  <!-- 帮助对话框 -->
</template>

<script setup>
// 导入 novelApi
import { novelApi } from '@/api'
// 状态管理
// 生命周期钩子
</script>
```

**核心功能**:
- 小说列表展示 (卡片形式)
- 小说统计 (字数/章节数/角色数)
- 帮助对话框 (功能介绍)
- 创建/删除小说

### NovelPage (小说详情)

**核心功能**:
- 章节列表管理
- 角色管理 (CRUD + 肖像生成)
- 关系图谱可视化 (@antv/g6)
- 大纲生成
- 导出设置

**依赖组件**:
- `RelationshipGraph.vue` - 角色关系图

### WriterPage (写作界面)

**核心功能**:
- Tiptap 富文本编辑器
- 场景选择与切换
- SSE 流式正文生成
- 分镜配图/视频生成
- AI 助手对话
- 版本历史与恢复

**依赖组件**:
- `TiptapEditor.vue` - 富文本编辑器

### RagPage (RAG 管理)

**核心功能**:
- 场景摘要列表
- RAG 摘要编辑
- 手动同步 RAG
- 查看向量检索状态

### SettingsPage (设置)

**核心功能**:
- API Key 配置
- 模型选择 (通用/写作/摘要/审稿)
- 主题切换 (亮/暗)

---

## 路由配置

```javascript
// router/index.js
routes: [
  { path: '/', component: HomePage },
  { path: '/novel/:id', component: NovelPage },
  { path: '/write/:id', component: WriterPage },
  { path: '/rag/:id', component: RagPage },
  { path: '/settings', component: SettingsPage },
]
```

---

## 状态管理

页面状态主要通过 **Pinia** 管理:

```javascript
// stores/novel.js
const useNovelStore = defineStore('novel', {
  state: () => ({
    currentNovel: null,
    chapters: [],
    characters: []
  }),
  actions: {
    async fetchNovel(id) { ... },
    async createChapter(data) { ... }
  }
})
```

---

## API 调用模式

```javascript
import { novelApi, sceneApi, characterApi } from '@/api'

// 获取小说
const novel = await novelApi.get(novelId)

// 创建章节
await chapterApi.create({ novel_id: novelId, title: '第一章' })

// SSE 流式生成
const eventSource = sceneApi.generate(sceneId)
eventSource.onmessage = (e) => {
  const data = JSON.parse(e.data)
  // 处理: { token, done, error }
}
```

---

## 相关文件

| 文件 | 说明 |
|------|------|
| `HomePage.vue` | 首页 (~500 行) |
| `NovelPage.vue` | 小说详情 |
| `WriterPage.vue` | 写作界面 |
| `RagPage.vue` | RAG 管理页 |
| `SettingsPage.vue` | 设置页 |
| `../router/index.js` | 路由配置 |
| `../stores/novel.js` | 状态管理 |

---

## 变更记录

- **2026-03-24**: 初始化文档
