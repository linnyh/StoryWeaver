<template>
  <div class="tiptap-editor">
    <div v-if="editor" class="toolbar">
      <button
        @click="editor.chain().focus().toggleBold().run()"
        :class="{ 'is-active': editor.isActive('bold') }"
      >
        B
      </button>
      <button
        @click="editor.chain().focus().toggleItalic().run()"
        :class="{ 'is-active': editor.isActive('italic') }"
      >
        I
      </button>
      <button
        @click="editor.chain().focus().toggleHeading({ level: 1 }).run()"
        :class="{ 'is-active': editor.isActive('heading', { level: 1 }) }"
      >
        H1
      </button>
      <button
        @click="editor.chain().focus().toggleHeading({ level: 2 }).run()"
        :class="{ 'is-active': editor.isActive('heading', { level: 2 }) }"
      >
        H2
      </button>
      <button
        @click="editor.chain().focus().toggleBulletList().run()"
        :class="{ 'is-active': editor.isActive('bulletList') }"
      >
        列表
      </button>
    </div>
    <editor-content :editor="editor" class="editor-content" />
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import { useEditor, EditorContent } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import Placeholder from '@tiptap/extension-placeholder'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  editable: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['update:modelValue'])

const editor = useEditor({
  content: props.modelValue,
  editable: props.editable,
  extensions: [
    StarterKit,
    Placeholder.configure({
      placeholder: '开始写作...'
    })
  ],
  onUpdate: ({ editor }) => {
    emit('update:modelValue', editor.getHTML())
  }
})

watch(() => props.modelValue, (newValue) => {
  if (editor.value && newValue !== editor.value.getHTML()) {
    editor.value.commands.setContent(newValue, false)
  }
})

watch(() => props.editable, (newValue) => {
  if (editor.value) {
    editor.value.setEditable(newValue)
  }
})

onBeforeUnmount(() => {
  if (editor.value) {
    editor.value.destroy()
  }
})
</script>

<style lang="scss">
.tiptap-editor {
  display: flex;
  flex-direction: column;
  height: 100%;

  .toolbar {
    padding: 8px;
    border-bottom: 1px solid #eee;
    display: flex;
    gap: 4px;

    button {
      padding: 6px 12px;
      border: 1px solid #ddd;
      background: white;
      border-radius: 4px;
      cursor: pointer;
      font-size: 14px;

      &:hover {
        background: #f5f5f5;
      }

      &.is-active {
        background: #e6f7ff;
        border-color: #1890ff;
        color: #1890ff;
      }
    }
  }

  .editor-content {
    flex: 1;
    padding: 20px;
    overflow-y: auto;

    .ProseMirror {
      outline: none;
      min-height: 100%;
      font-size: 16px;
      line-height: 1.8;
      font-family: 'Georgia', serif;

      p {
        margin-bottom: 1em;
      }

      h1, h2, h3 {
        margin: 1em 0 0.5em;
      }

      ul, ol {
        padding-left: 1.5em;
        margin-bottom: 1em;
      }

      &.is-editor-empty:before {
        color: #adb5bd;
        content: attr(data-placeholder);
        float: left;
        height: 0;
        pointer-events: none;
      }
    }
  }
}
</style>
