<template>
  <div class="tiptap-editor flex flex-col h-full">
    <div v-if="editor" class="flex items-center gap-1 p-2 border-b border-white/5 bg-space-900/30">
      <button
        @click="editor.chain().focus().toggleBold().run()"
        class="editor-btn"
        :class="{ 'is-active': editor.isActive('bold') }"
        title="Bold"
      >
        B
      </button>
      <button
        @click="editor.chain().focus().toggleItalic().run()"
        class="editor-btn italic"
        :class="{ 'is-active': editor.isActive('italic') }"
        title="Italic"
      >
        I
      </button>
      <div class="w-px h-4 bg-white/10 mx-1"></div>
      <button
        @click="editor.chain().focus().toggleHeading({ level: 1 }).run()"
        class="editor-btn"
        :class="{ 'is-active': editor.isActive('heading', { level: 1 }) }"
        title="Heading 1"
      >
        H1
      </button>
      <button
        @click="editor.chain().focus().toggleHeading({ level: 2 }).run()"
        class="editor-btn"
        :class="{ 'is-active': editor.isActive('heading', { level: 2 }) }"
        title="Heading 2"
      >
        H2
      </button>
      <div class="w-px h-4 bg-white/10 mx-1"></div>
      <button
        @click="editor.chain().focus().toggleBulletList().run()"
        class="editor-btn"
        :class="{ 'is-active': editor.isActive('bulletList') }"
        title="Bullet List"
      >
        • List
      </button>
    </div>
    <editor-content :editor="editor" class="editor-content flex-1 overflow-y-auto custom-scrollbar" />
  </div>
</template>

<script setup>
import { watch, onBeforeUnmount } from 'vue'
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
  editorProps: {
    attributes: {
      class: 'prose prose-invert max-w-none focus:outline-none p-6 text-gray-200 leading-relaxed min-h-full',
    },
  },
  extensions: [
    StarterKit,
    Placeholder.configure({
      placeholder: 'Start writing your masterpiece...',
      emptyEditorClass: 'is-editor-empty',
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

<style scoped>
/* Remove @apply from here since it's not supported in scoped styles with standard CSS processors 
   without PostCSS configured specifically for it in Vue SFCs in this way.
   Instead, we'll use regular CSS classes in the template or inline styles here. 
   However, since we have Tailwind, we can just use the classes directly in the template
   or use standard CSS syntax here.
*/

.editor-btn {
  /* Using Tailwind utility classes in template is safer, but if we want to keep this class: */
  padding: 0.375rem 0.75rem;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  font-weight: 500;
  color: #9ca3af;
  transition-property: color, background-color, border-color, text-decoration-color, fill, stroke;
  transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
  transition-duration: 150ms;
  border: 1px solid transparent;
}

.editor-btn:hover {
  color: white;
  background-color: rgba(255, 255, 255, 0.1);
}

.editor-btn.is-active {
  background-color: rgba(0, 240, 255, 0.1);
  color: #00F0FF;
  border-color: rgba(0, 240, 255, 0.2);
}

:deep(.is-editor-empty:first-child::before) {
  color: #6b7280;
  content: attr(data-placeholder);
  float: left;
  height: 0;
  pointer-events: none;
}

/* Typography Overrides for Dark Mode - using standard CSS to be safe */
:deep(.prose h1) {
  color: white;
  font-family: 'Orbitron', sans-serif;
  font-weight: 700;
  margin-top: 1.5rem;
  margin-bottom: 1rem;
  font-size: 2.25em;
}
:deep(.prose h2) {
  color: white;
  font-family: 'Orbitron', sans-serif;
  font-weight: 700;
  margin-top: 1.25rem;
  margin-bottom: 0.75rem;
  font-size: 1.5em;
}
:deep(.prose p) {
  margin-bottom: 1rem;
  color: #d1d5db;
}
:deep(.prose strong) {
  color: white;
  font-weight: 700;
}
:deep(.prose ul) {
  list-style-type: disc;
  list-style-position: inside;
  color: #d1d5db;
  margin-bottom: 1rem;
}
:deep(.prose blockquote) {
  border-left-width: 4px;
  border-left-color: #00F0FF;
  padding-left: 1rem;
  font-style: italic;
  color: #9ca3af;
  margin-top: 1rem;
  margin-bottom: 1rem;
}
</style>
