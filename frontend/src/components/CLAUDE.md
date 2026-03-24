# Frontend Components 模块

> [根目录](../../../CLAUDE.md) > [frontend](../../) > **src/components**

---

## 模块职责

通用 UI 组件库，供各页面复用。

---

## 组件列表

| 文件 | 类型 | 核心功能 |
|------|------|---------|
| `TiptapEditor.vue` | 编辑器 | Tiptap 富文本编辑器，支持 Markdown |
| `RelationshipGraph.vue` | 图表 | @antv/g6 角色关系图谱可视化 |

---

## TiptapEditor.vue

**功能**: 基于 Tiptap 的富文本编辑器，用于场景正文编辑。

```vue
<template>
  <div class="editor-container">
    <editor-content :editor="editor" />
  </div>
</template>

<script setup>
import { useEditor, EditorContent } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import Placeholder from '@tiptap/extension-placeholder'

const editor = useEditor({
  extensions: [
    StarterKit,
    Placeholder.configure({
      placeholder: '开始写作...'
    })
  ],
  content: props.modelValue,
  onUpdate: ({ editor }) => {
    emit('update:modelValue', editor.getHTML())
  }
})
</script>
```

**扩展**:
- `@tiptap/starter-kit` - 基础编辑功能
- `@tiptap/extension-placeholder` - 占位符提示

**Props**:
- `modelValue: String` - 绑定值 (HTML)
- `placeholder: String` - 占位符文本

**Events**:
- `update:modelValue` - 值变化时触发

---

## RelationshipGraph.vue

**功能**: 基于 @antv/g6 的角色关系图谱可视化。

```vue
<template>
  <div ref="graphContainer" class="graph-container"></div>
</template>

<script setup>
import { Graph } from '@antv/g6'

const graph = new Graph({
  container: graphContainer.value,
  data: { nodes: [], edges: [] },
  // 布局配置
  layout: { type: 'force' },
  // 节点/边样式
  node: { style: { size: 40, labelText: (d) => d.name } },
  edge: { style: { stroke: '#999', lineWidth: 2 } }
})
</script>
```

**数据格式**:

```javascript
// 节点
{
  id: 'char-1',
  data: { name: '张三', role: '主角' }
}

// 边
{
  source: 'char-1',
  target: 'char-2',
  data: {
    affinity: 80,       // 好感度
    conflict: '门派恩怨' // 核心矛盾
  }
}
```

**交互功能**:
- 拖拽节点
- 缩放/平移
- 点击查看详情
- 节点颜色区分 (主角/配角/反派)

---

## 组件开发规范

### 命名规范

- PascalCase 文件名: `MyComponent.vue`
- 简短描述性名称

### Props 定义

```javascript
// 使用 defineProps + 类型化
const props = defineProps({
  title: {
    type: String,
    required: true
  },
  loading: {
    type: Boolean,
    default: false
  }
})
```

### Emits 定义

```javascript
const emit = defineEmits(['submit', 'cancel'])

// 调用
emit('submit', payload)
```

---

## 相关文件

| 文件 | 说明 |
|------|------|
| `TiptapEditor.vue` | Tiptap 编辑器封装 |
| `RelationshipGraph.vue` | G6 关系图封装 |
| `../api/index.js` | API 调用封装 |
| `../stores/novel.js` | 状态管理 |

---

## 变更记录

- **2026-03-24**: 初始化文档
