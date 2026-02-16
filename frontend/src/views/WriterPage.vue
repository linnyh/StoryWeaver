<template>
  <div class="h-full p-4 grid grid-cols-12 gap-4">
    <!-- Left: Context -->
    <div class="col-span-3 flex flex-col glass-panel rounded-2xl overflow-hidden">
      <div class="p-4 border-b border-white/5 bg-space-900/50 backdrop-blur-xl">
        <h3 class="font-display text-white font-medium tracking-wide flex items-center gap-2">
          <el-icon class="text-neon-blue"><Document /></el-icon>
          Context
        </h3>
      </div>

      <div class="flex-1 overflow-y-auto p-4 custom-scrollbar space-y-6">
        <div class="space-y-2">
          <h4 class="text-xs uppercase tracking-wider text-gray-500 font-bold">Previous Summary</h4>
          <div class="text-sm text-gray-300 leading-relaxed bg-white/5 p-3 rounded-xl border border-white/5">
            {{ prevSummary || 'No summary available' }}
          </div>
        </div>

        <div class="space-y-2">
          <h4 class="text-xs uppercase tracking-wider text-gray-500 font-bold">Scene Directives</h4>
          <div class="bg-white/5 p-3 rounded-xl border border-white/5 space-y-3">
            <div class="flex items-center gap-2 text-neon-blue text-sm font-medium">
              <el-icon><Location /></el-icon>
              <span>{{ currentScene?.location || 'Unspecified Location' }}</span>
            </div>
            <div class="text-sm text-gray-300 leading-relaxed">
              {{ currentScene?.beat_description || 'No directives' }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Center: Editor -->
    <div class="col-span-6 flex flex-col glass-panel rounded-2xl overflow-hidden relative">
      <div class="p-4 border-b border-white/5 flex justify-between items-center bg-space-900/50 backdrop-blur-xl z-10">
        <div class="flex items-center gap-3">
          <button @click="goBack" class="p-1.5 rounded-lg hover:bg-white/10 text-gray-400 hover:text-white transition-colors">
            <el-icon><ArrowLeft /></el-icon>
          </button>
          <span class="font-display text-white font-bold truncate max-w-[200px]">
            {{ currentScene?.location || 'Writing Mode' }}
          </span>
          <div v-if="saving" class="text-xs text-gray-500 flex items-center gap-1 animate-pulse">
            <el-icon><Loading /></el-icon> Saving...
          </div>
        </div>
        
        <div class="flex items-center gap-2">
          <button 
            @click="handleGenerate" 
            :disabled="!currentScene || generating"
            class="px-3 py-1.5 rounded-lg bg-neon-purple/10 hover:bg-neon-purple/20 border border-neon-purple/20 text-xs font-medium text-neon-purple transition-colors disabled:opacity-50 flex items-center gap-1"
          >
            <el-icon :class="{ 'animate-spin': generating }"><MagicStick /></el-icon>
            {{ generating ? 'Writing...' : 'AI Continue' }}
          </button>
          
          <!-- Editorial Toggle -->
          <el-tooltip content="Toggle Editorial Committee Review" placement="bottom">
             <button
                @click="enableEditorial = !enableEditorial"
                class="px-2 py-1.5 rounded-lg border transition-colors flex items-center gap-1"
                :class="enableEditorial ? 'bg-neon-blue/10 border-neon-blue/20 text-neon-blue' : 'bg-white/5 border-white/5 text-gray-400 hover:text-gray-200'"
             >
               <el-icon><DataAnalysis /></el-icon>
               <span class="text-[10px] font-medium">{{ enableEditorial ? 'Review: ON' : 'Review: OFF' }}</span>
             </button>
          </el-tooltip>
          
          <button 
            @click="handleSave" 
            :disabled="saving"
            class="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 border border-white/5 text-xs font-medium text-gray-300 transition-colors disabled:opacity-50"
          >
            Save
          </button>
          
          <button 
            v-if="editorialLogs.length > 0"
            @click="showLogs = true"
            class="px-3 py-1.5 rounded-lg bg-neon-blue/10 hover:bg-neon-blue/20 border border-neon-blue/20 text-xs font-medium text-neon-blue transition-colors flex items-center gap-1"
          >
            <el-icon><DataAnalysis /></el-icon>
            Logs
          </button>
          
          <button 
            @click="handleApprove"
            class="px-3 py-1.5 rounded-lg bg-neon-green/10 hover:bg-neon-green/20 border border-neon-green/20 text-xs font-medium text-neon-green transition-colors"
          >
            Approve
          </button>
        </div>
      </div>

      <div class="flex-1 overflow-hidden bg-space-950/30 relative">
        <!-- System Status Animation -->
        <transition
          enter-active-class="transition ease-out duration-300"
          enter-from-class="opacity-0 -translate-y-2"
          enter-to-class="opacity-100 translate-y-0"
          leave-active-class="transition ease-in duration-200"
          leave-from-class="opacity-100 translate-y-0"
          leave-to-class="opacity-0 -translate-y-2"
        >
          <div v-if="systemStatus" class="absolute top-6 left-1/2 -translate-x-1/2 z-30 pointer-events-none">
             <div class="px-5 py-2.5 rounded-full bg-space-900/80 border border-neon-purple/30 backdrop-blur-xl text-white text-xs font-medium shadow-[0_0_15px_rgba(176,38,255,0.2)] flex items-center gap-3">
               <span class="relative flex h-2 w-2">
                  <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-neon-purple opacity-75"></span>
                  <span class="relative inline-flex rounded-full h-2 w-2 bg-neon-purple"></span>
                </span>
               <span class="tracking-wide">{{ systemStatus }}</span>
             </div>
          </div>
        </transition>

        <TiptapEditor
          v-model="content"
          :editable="true"
          @update:modelValue="handleContentChange"
          class="h-full"
        />
      </div>
    </div>

    <!-- Right: Assistant -->
    <div class="col-span-3 flex flex-col glass-panel rounded-2xl overflow-hidden">
      <div class="p-4 border-b border-white/5 bg-space-900/50 backdrop-blur-xl">
        <h3 class="font-display text-white font-medium tracking-wide flex items-center gap-2">
          <el-icon class="text-neon-pink"><ChatDotRound /></el-icon>
          AI Assistant
        </h3>
      </div>

      <div class="flex-1 flex flex-col overflow-hidden relative">
        <div class="flex-1 overflow-y-auto p-4 custom-scrollbar space-y-4" ref="chatContainer">
          <div v-if="chatMessages.length === 0" class="text-center py-8 text-gray-500 text-xs">
            Ask me to refine text, suggest ideas, or check consistency.
          </div>
          
          <div
            v-for="(msg, index) in chatMessages"
            :key="index"
            class="flex flex-col max-w-[90%]"
            :class="msg.role === 'user' ? 'self-end items-end' : 'self-start items-start'"
          >
            <div 
              class="px-3 py-2 rounded-xl text-sm leading-relaxed"
              :class="msg.role === 'user' ? 'bg-neon-blue/20 text-white rounded-br-none border border-neon-blue/20' : 'bg-white/10 text-gray-200 rounded-bl-none border border-white/5'"
            >
              {{ msg.content }}
            </div>
            <span class="text-[10px] text-gray-600 mt-1 px-1">
              {{ msg.role === 'user' ? 'You' : 'AI' }}
            </span>
          </div>
        </div>

        <div class="p-3 border-t border-white/5 bg-space-900/30">
          <div class="relative">
            <el-input
              v-model="chatInput"
              type="textarea"
              :rows="2"
              placeholder="Type instructions..."
              @keydown.enter.ctrl.prevent="handleSendChat"
              class="glass-input-override mb-2"
              resize="none"
            />
            <button 
              @click="handleSendChat"
              class="absolute bottom-3 right-2 p-1.5 rounded-lg bg-neon-blue/20 text-neon-blue hover:bg-neon-blue/30 transition-colors"
            >
              <el-icon><Position /></el-icon>
            </button>
          </div>
          <div class="text-[10px] text-gray-600 text-center mt-1">
            Ctrl + Enter to send
          </div>
        </div>
      </div>
    </div>
    <!-- Editorial Logs Dialog -->
    <el-dialog
      v-model="showLogs"
      title="Editorial Committee Logs"
      width="600px"
      :modal-class="'glass-dialog'"
    >
      <div class="space-y-4 max-h-[60vh] overflow-y-auto custom-scrollbar p-2">
        <div 
          v-for="(log, index) in editorialLogs" 
          :key="index"
          class="p-4 rounded-xl bg-white/5 border border-white/5 text-sm leading-relaxed text-gray-300"
        >
          <div class="flex items-start gap-3">
            <span class="mt-1.5 w-2 h-2 rounded-full flex-shrink-0" 
              :class="{
                'bg-neon-blue shadow-[0_0_8px_rgba(0,240,255,0.5)]': log.includes('Agent A'),
                'bg-neon-pink shadow-[0_0_8px_rgba(255,0,128,0.5)]': log.includes('Agent B'),
                'bg-neon-purple shadow-[0_0_8px_rgba(176,38,255,0.5)]': log.includes('Agent C'),
                'bg-gray-500': !log.includes('Agent')
              }"
            ></span>
            <span class="whitespace-pre-wrap">{{ log }}</span>
          </div>
        </div>
        <div v-if="editorialLogs.length === 0" class="text-center text-gray-500 py-8">
          No logs available yet.
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<style>
/* Global style for glass dialog */
.glass-dialog .el-dialog {
  background: rgba(17, 24, 39, 0.95);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
}
.glass-dialog .el-dialog__title {
  color: white;
  font-family: 'Space Grotesk', sans-serif;
}
.glass-dialog .el-dialog__headerbtn .el-dialog__close {
  color: #9ca3af;
}
.glass-dialog .el-dialog__body {
  padding: 20px;
}
</style>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { sceneApi } from '@/api'
import { ElMessage } from 'element-plus'
import { Location, MagicStick, ArrowLeft, Document, ChatDotRound, Position, Loading, DataAnalysis } from '@element-plus/icons-vue'
import TiptapEditor from '@/components/TiptapEditor.vue'

import { fetchEventSource } from '@microsoft/fetch-event-source'

const route = useRoute()
const router = useRouter()

const currentScene = ref(null)
const content = ref('')
const prevSummary = ref('')
const generating = ref(false)
const saving = ref(false)
const systemStatus = ref('')
const showLogs = ref(false)
const editorialLogs = ref([])
const enableEditorial = ref(true) // 默认开启审稿

const chatMessages = ref([])
const chatInput = ref('')
const chatContainer = ref(null)

function goBack() {
  router.back()
}

async function loadScene() {
  const sceneId = route.params.sceneId
  try {
    const { data } = await sceneApi.get(sceneId)
    currentScene.value = data
    content.value = data.content || ''
    prevSummary.value = data.context_summary || 'No context summary available'
  } catch (error) {
    ElMessage.error('Failed to load scene')
  }
}

async function handleGenerate() {
  if (!currentScene.value) return

  content.value = ''
  generating.value = true
  systemStatus.value = 'Initializing AI...'
  editorialLogs.value = []

  try {
    const url = `/api/scenes/${currentScene.value.id}/generate?enable_editorial=${enableEditorial.value}`
    const eventSource = new EventSource(url)

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data)

      if (data.chunk) {
        // Content streaming started, clear system status
        if (systemStatus.value) {
          systemStatus.value = ''
        }
        content.value += data.chunk
      } else if (data.system) {
        systemStatus.value = data.system
      } else if (data.log) {
        editorialLogs.value.push(data.log)
        // Auto-show logs if not already shown? Maybe better to just show a notification or update counter
        // Let's just update the array for now.
      } else if (data.done) {
        eventSource.close()
        generating.value = false
        systemStatus.value = ''
        ElMessage.success('Generation complete')
        handleSave()
        
        if (editorialLogs.value.length > 0) {
           ElMessage.info({
             message: 'View editorial logs',
             type: 'info',
             showClose: true,
             onClick: () => { showLogs.value = true }
           })
        }
      } else if (data.error) {
        eventSource.close()
        generating.value = false
        systemStatus.value = ''
        ElMessage.error(data.error)
      }
    }

    eventSource.onerror = () => {
      eventSource.close()
      generating.value = false
      systemStatus.value = ''
      ElMessage.error('Generation interrupted')
    }
  } catch (error) {
    generating.value = false
    systemStatus.value = ''
    ElMessage.error('Generation failed')
  }
}

async function handleSave() {
  if (!currentScene.value) return

  saving.value = true
  try {
    await sceneApi.update(currentScene.value.id, {
      content: content.value
    })
    ElMessage.success('Saved')
  } catch (error) {
    ElMessage.error('Save failed')
  } finally {
    saving.value = false
  }
}

async function handleApprove() {
  if (!currentScene.value) return

  await handleSave()

  try {
    await sceneApi.update(currentScene.value.id, {
      status: 'approved'
    })
    ElMessage.success('Scene approved')
    router.back()
  } catch (error) {
    ElMessage.error('Operation failed')
  }
}

function handleContentChange(newContent) {
  content.value = newContent
}

async function handleSendChat() {
  if (!chatInput.value.trim()) return

  const userMessage = chatInput.value
  chatInput.value = ''
  
  chatMessages.value.push({
    role: 'user',
    content: userMessage
  })

  await nextTick()
  scrollToBottom()

  // Add a placeholder for AI response
  const assistantMsgIndex = chatMessages.value.push({
    role: 'assistant',
    content: ''
  }) - 1

  try {
    await fetchEventSource(`/api/scenes/${currentScene.value.id}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message: userMessage }),
      onmessage(msg) {
        try {
          const data = JSON.parse(msg.data)
          if (data.chunk) {
            chatMessages.value[assistantMsgIndex].content += data.chunk
            scrollToBottom()
          } else if (data.error) {
             chatMessages.value[assistantMsgIndex].content = `Error: ${data.error}`
          }
        } catch (e) {
          console.error(e)
        }
      },
      onerror(err) {
        console.error(err)
        chatMessages.value[assistantMsgIndex].content += '\n[Connection Error]'
      }
    })
  } catch (error) {
    console.error('Chat error:', error)
    chatMessages.value[assistantMsgIndex].content = 'Failed to send message.'
  }
}

function scrollToBottom() {
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}

onMounted(() => {
  loadScene()
})
</script>

<style scoped>
.glass-input-override :deep(.el-textarea__inner) {
  background-color: rgba(255, 255, 255, 0.05);
  box-shadow: none;
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: white;
  transition: all 0.3s;
  padding-right: 40px;
}

.glass-input-override :deep(.el-textarea__inner:hover),
.glass-input-override :deep(.el-textarea__inner:focus) {
  background-color: rgba(255, 255, 255, 0.1);
  border-color: rgba(0, 240, 255, 0.5);
}
</style>
