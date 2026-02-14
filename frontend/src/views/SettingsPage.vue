<template>
  <div class="h-full p-6 flex flex-col overflow-hidden">
    <div class="glass-panel flex flex-col h-full rounded-2xl overflow-hidden relative max-w-3xl mx-auto w-full">
      <!-- Header -->
      <div class="p-6 border-b border-white/5 bg-space-900/50 backdrop-blur-xl shrink-0 z-10">
        <h1 class="font-display text-2xl text-white font-bold tracking-wide flex items-center gap-3">
          <el-icon class="text-neon-blue"><Setting /></el-icon>
          Settings
        </h1>
        <p class="text-gray-400 mt-2 text-sm">Configure your AI model provider and system preferences.</p>
      </div>

      <!-- Content -->
      <div class="flex-1 overflow-y-auto p-8 custom-scrollbar">
        <div class="space-y-8">
          
          <!-- LLM Configuration -->
          <section>
            <h2 class="text-lg font-medium text-white mb-4 flex items-center gap-2">
              <span class="w-1 h-6 rounded-full bg-neon-purple"></span>
              LLM Configuration
            </h2>
            
            <div class="glass-card p-6 rounded-xl space-y-6">
              <el-form :model="form" label-position="top" class="glass-form">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <el-form-item label="Provider">
                    <el-select v-model="provider" placeholder="Select Provider" class="w-full">
                      <el-option label="Custom (OpenAI Compatible)" value="custom" />
                      <el-option label="DeepSeek" value="deepseek" />
                      <el-option label="Moonshot (Kimi)" value="moonshot" />
                    </el-select>
                  </el-form-item>
                  
                  <el-form-item label="Model Name">
                    <el-input v-model="form.openai_model" placeholder="e.g. gpt-4, deepseek-chat" />
                  </el-form-item>
                </div>

                <el-form-item label="Base URL">
                  <el-input v-model="form.openai_base_url" placeholder="https://api.openai.com/v1" />
                </el-form-item>

                <el-form-item label="API Key">
                  <el-input 
                    v-model="form.openai_api_key" 
                    type="password" 
                    placeholder="sk-..." 
                    show-password
                  />
                </el-form-item>

                <div class="pt-4 flex justify-end">
                  <el-button type="primary" @click="saveConfig" :loading="saving" class="!bg-neon-blue/10 !border-neon-blue/20 !text-neon-blue hover:!bg-neon-blue/20">
                    Save Changes
                  </el-button>
                </div>
              </el-form>
            </div>
          </section>

          <!-- System Info (Read Only) -->
          <section>
            <h2 class="text-lg font-medium text-white mb-4 flex items-center gap-2">
              <span class="w-1 h-6 rounded-full bg-gray-600"></span>
              About
            </h2>
            <div class="glass-card p-6 rounded-xl text-sm text-gray-400 space-y-2">
              <div class="flex justify-between">
                <span>Version</span>
                <span class="text-white">v0.1.0 (Alpha)</span>
              </div>
              <div class="flex justify-between">
                <span>Theme</span>
                <span class="text-white">Deep Space</span>
              </div>
            </div>
          </section>

        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { Setting } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import axios from '@/api'

const loading = ref(false)
const saving = ref(false)
const provider = ref('custom')

const form = ref({
  openai_api_key: '',
  openai_base_url: '',
  openai_model: ''
})

// 预设配置
const presets = {
  deepseek: {
    openai_base_url: 'https://api.deepseek.com',
    openai_model: 'deepseek-chat'
  },
  moonshot: {
    openai_base_url: 'https://api.moonshot.cn/v1',
    openai_model: 'moonshot-v1-8k'
  }
}

watch(provider, (newVal) => {
  if (presets[newVal]) {
    form.value.openai_base_url = presets[newVal].openai_base_url
    form.value.openai_model = presets[newVal].openai_model
  }
})

async function loadConfig() {
  loading.value = true
  try {
    const { data } = await axios.get('/settings/llm')
    form.value = data
    
    // 简单的反向匹配 provider
    if (data.openai_base_url?.includes('deepseek')) {
      provider.value = 'deepseek'
    } else if (data.openai_base_url?.includes('moonshot')) {
      provider.value = 'moonshot'
    } else {
      provider.value = 'custom'
    }
  } catch (error) {
    ElMessage.error('Failed to load settings')
  } finally {
    loading.value = false
  }
}

async function saveConfig() {
  saving.value = true
  try {
    await axios.post('/settings/llm', form.value)
    ElMessage.success('Settings saved successfully')
  } catch (error) {
    ElMessage.error('Failed to save settings')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadConfig()
})
</script>

<style scoped>
.glass-form :deep(.el-form-item__label) {
  color: #9ca3af;
}

.glass-form :deep(.el-input__wrapper),
.glass-form :deep(.el-select__wrapper) {
  background-color: rgba(255, 255, 255, 0.05);
  box-shadow: none;
  border: 1px solid rgba(255, 255, 255, 0.1);
  transition: all 0.3s;
}

.glass-form :deep(.el-input__wrapper:hover),
.glass-form :deep(.el-input__wrapper.is-focus),
.glass-form :deep(.el-select__wrapper:hover),
.glass-form :deep(.el-select__wrapper.is-focus) {
  background-color: rgba(255, 255, 255, 0.1);
  border-color: rgba(0, 240, 255, 0.5);
}

.glass-form :deep(.el-input__inner) {
  color: white;
}
</style>
