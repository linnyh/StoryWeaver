<template>
  <div class="writer-page">
    <el-row :gutter="20">
      <!-- 左侧：上下文 -->
      <el-col :span="4">
        <el-card class="context-card">
          <template #header>
            <span>上下文</span>
          </template>

          <div class="context-section">
            <h4>前情提要</h4>
            <div class="context-content">
              {{ prevSummary || '暂无前情提要' }}
            </div>
          </div>

          <div class="context-section">
            <h4>场景指令</h4>
            <div class="context-content">
              <div class="location">
                <el-icon><Location /></el-icon>
                {{ currentScene?.location || '未指定' }}
              </div>
              <div class="beat">
                {{ currentScene?.beat_description || '暂无指令' }}
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 中间：编辑器 -->
      <el-col :span="14">
        <el-card class="editor-card">
          <template #header>
            <div class="editor-header">
              <div class="header-left">
                 <el-button link @click="goBack">
                   <el-icon><ArrowLeft /></el-icon>
                   返回
                 </el-button>
                 <span class="scene-title">{{ currentScene?.location || '写作模式' }}</span>
              </div>
              <div class="header-actions">
                <el-button
                  type="primary"
                  @click="handleGenerate"
                  :loading="generating"
                  :disabled="!currentScene"
                >
                  <el-icon><MagicStick /></el-icon>
                  AI 续写
                </el-button>
                <el-button @click="handleSave" :loading="saving">
                  保存
                </el-button>
                <el-button type="success" @click="handleApprove">
                  确认
                </el-button>
              </div>
            </div>
          </template>

          <div class="editor-container">
            <TiptapEditor
              v-model="content"
              :editable="true"
              @update:modelValue="handleContentChange"
            />
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：助手 -->
      <el-col :span="6">
        <el-card class="assistant-card">
          <template #header>
            <span>AI 助手</span>
          </template>

          <div class="chat-container">
            <div class="chat-messages" ref="chatContainer">
              <div
                v-for="(msg, index) in chatMessages"
                :key="index"
                class="chat-message"
                :class="msg.role"
              >
                <div class="message-content">{{ msg.content }}</div>
              </div>
            </div>

            <div class="chat-input">
              <el-input
                v-model="chatInput"
                type="textarea"
                :rows="2"
                placeholder="输入修改指令，如：把这段改得更悲伤一点"
                @keydown.enter.ctrl="handleSendChat"
              />
              <el-button type="primary" @click="handleSendChat">
                发送
              </el-button>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { sceneApi } from '@/api'
import { ElMessage } from 'element-plus'
import { Location, MagicStick, ArrowLeft } from '@element-plus/icons-vue'
import TiptapEditor from '@/components/TiptapEditor.vue'

const route = useRoute()
const router = useRouter()

const currentScene = ref(null)
const content = ref('')
const prevSummary = ref('')
const generating = ref(false)
const saving = ref(false)

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
    // 加载前情提要：优先使用后端动态计算的 context_summary，如果没有则使用 '暂无前情提要'
    // 注意：data.summary 是本场景的摘要，不是前情提要，千万别用错了！
    prevSummary.value = data.context_summary || '暂无前情提要'
  } catch (error) {
    ElMessage.error('加载场景失败')
  }
}

async function handleGenerate() {
  if (!currentScene.value) return

  // 清空旧内容
  content.value = ''
  generating.value = true

  try {
    // 使用 SSE 流式获取
    const eventSource = new EventSource(`/api/scenes/${currentScene.value.id}/generate`)

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data)

      if (data.chunk) {
        content.value += data.chunk
      } else if (data.done) {
        eventSource.close()
        generating.value = false
        ElMessage.success('生成完成')
        // 自动保存生成的内容
        handleSave()
      } else if (data.error) {
        eventSource.close()
        generating.value = false
        ElMessage.error(data.error)
      }
    }

    eventSource.onerror = () => {
      eventSource.close()
      generating.value = false
      ElMessage.error('生成中断')
    }
  } catch (error) {
    generating.value = false
    ElMessage.error('生成失败')
  }
}

async function handleSave() {
  if (!currentScene.value) return

  saving.value = true
  try {
    await sceneApi.update(currentScene.value.id, {
      content: content.value
    })
    ElMessage.success('保存成功')
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

async function handleApprove() {
  if (!currentScene.value) return

  // 先保存内容，确保最新内容被提交
  await handleSave()

  try {
    await sceneApi.update(currentScene.value.id, {
      status: 'approved'
    })
    ElMessage.success('已确认')
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

function handleContentChange(newContent) {
  content.value = newContent
}

async function handleSendChat() {
  if (!chatInput.value.trim()) return

  // 添加用户消息
  chatMessages.value.push({
    role: 'user',
    content: chatInput.value
  })

  const userInput = chatInput.value
  chatInput.value = ''

  // 滚动到底部
  await nextTick()
  scrollToBottom()

  // TODO: 调用 AI 修改接口
  // 模拟 AI 响应
  setTimeout(() => {
    chatMessages.value.push({
      role: 'assistant',
      content: '收到你的修改指令，正在处理...'
    })
    nextTick(() => scrollToBottom())
  }, 500)
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

<style lang="scss" scoped>
.writer-page {
  height: calc(100vh - 100px);
}

.context-card, .assistant-card {
  height: 100%;
  overflow-y: auto;
}

.context-section {
  margin-bottom: 20px;

  h4 {
    margin: 0 0 8px;
    font-size: 14px;
    color: #666;
  }

  .context-content {
    font-size: 13px;
    color: #333;
    line-height: 1.6;

    .location {
      display: flex;
      align-items: center;
      gap: 4px;
      font-weight: 500;
      margin-bottom: 8px;
    }

    .beat {
      color: #666;
    }
  }
}

.editor-card {
  height: 100%;
  display: flex;
  flex-direction: column;

  .editor-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .header-left {
      display: flex;
      align-items: center;
      gap: 12px;

      .scene-title {
        font-weight: bold;
      }
    }
  }

  .editor-container {
    flex: 1;
    overflow-y: auto;
  }
}

.assistant-card {
  display: flex;
  flex-direction: column;

  .chat-container {
    flex: 1;
    display: flex;
    flex-direction: column;
  }

  .chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: 10px 0;

    .chat-message {
      margin-bottom: 12px;

      .message-content {
        padding: 10px 14px;
        border-radius: 8px;
        font-size: 14px;
        line-height: 1.5;
      }

      &.user {
        text-align: right;

        .message-content {
          background: #e6f7ff;
          display: inline-block;
        }
      }

      &.assistant {
        .message-content {
          background: #f5f5f5;
          text-align: left;
        }
      }
    }
  }

  .chat-input {
    display: flex;
    flex-direction: column;
    gap: 8px;

    .el-button {
      align-self: flex-end;
    }
  }
}
</style>
