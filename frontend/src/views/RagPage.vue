<template>
  <div class="h-full p-6 flex flex-col overflow-hidden">
    <div class="glass-panel flex flex-col h-full rounded-2xl overflow-hidden relative">
      <!-- Header -->
      <div class="p-4 border-b border-white/5 flex justify-between items-center bg-space-900/50 backdrop-blur-xl shrink-0 z-10">
        <div class="flex items-center gap-4">
          <button @click="goBack" class="p-2 rounded-lg hover:bg-white/10 text-gray-400 hover:text-white transition-colors flex items-center gap-2">
            <el-icon><ArrowLeft /></el-icon>
            <span class="text-sm font-medium">Back</span>
          </button>
          <div class="h-6 w-px bg-white/10"></div>
          <h1 class="font-display text-lg text-white font-bold tracking-wide">
            <span class="text-neon-blue">RAG</span> Knowledge Base
          </h1>
        </div>
        
        <div class="flex items-center gap-4">
          <div class="relative group">
            <el-input
              v-model="searchQuery"
              placeholder="Search knowledge base..."
              prefix-icon="Search"
              clearable
              class="w-80 glass-input-override"
            />
          </div>
          <div class="px-3 py-1 rounded-full bg-white/5 border border-white/5 text-xs text-gray-400">
            {{ filteredSummaries.length }} entries
          </div>
        </div>
      </div>

      <!-- Content -->
      <div v-loading="loading" class="flex-1 overflow-y-auto p-6 custom-scrollbar relative bg-space-950/30">
        <div v-if="!loading && filteredSummaries.length === 0" class="flex flex-col items-center justify-center h-full text-gray-500">
          <div class="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center mb-4">
            <el-icon size="24"><Search /></el-icon>
          </div>
          <span>No entries found</span>
        </div>
        
        <div v-else class="grid grid-cols-1 gap-6 max-w-5xl mx-auto">
          <div v-for="(item, index) in filteredSummaries" :key="item.id" 
               class="glass-card p-6 rounded-xl group relative hover:translate-y-[-2px] transition-transform duration-300">
            
            <div class="flex justify-between items-start mb-4 pb-4 border-b border-white/5">
              <div class="flex items-center gap-3">
                <div class="flex items-center gap-2 px-2 py-1 rounded bg-neon-blue/10 text-neon-blue text-xs font-medium border border-neon-blue/20">
                  <el-icon><Location /></el-icon> 
                  <span>Scene: {{ item.metadata?.scene_id ? item.metadata.scene_id.substring(0, 8) + '...' : 'Unknown' }}</span>
                </div>
                <div class="text-xs text-gray-500 font-mono bg-white/5 px-2 py-1 rounded">
                  Doc: {{ item.id.substring(0, 8) }}...
                </div>
              </div>
              
              <div class="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                <button @click="handleEdit(item)" class="p-1.5 rounded-lg hover:bg-white/10 text-gray-400 hover:text-neon-blue transition-colors">
                  <el-icon><Edit /></el-icon>
                </button>
                <button @click="handleDelete(item)" class="p-1.5 rounded-lg hover:bg-white/10 text-gray-400 hover:text-red-400 transition-colors">
                  <el-icon><Delete /></el-icon>
                </button>
              </div>
            </div>
            
            <div class="text-gray-300 text-sm leading-relaxed mb-4 whitespace-pre-wrap font-light">
              {{ item.text }}
            </div>
            
            <div v-if="item.metadata && Object.keys(item.metadata).length > 0" class="flex flex-wrap gap-2 pt-4 border-t border-white/5 border-dashed">
              <span v-for="(val, key) in item.metadata" :key="key" 
                    class="px-2 py-0.5 rounded text-[10px] bg-white/5 text-gray-500 border border-white/5">
                {{ key }}: {{ val }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Edit Dialog -->
    <el-dialog v-model="showEditDialog" title="Edit Summary" width="600px" class="glass-dialog-override" destroy-on-close>
      <el-form :model="editForm" label-position="top">
        <el-form-item label="Content">
          <el-input
            v-model="editForm.text"
            type="textarea"
            :rows="8"
            placeholder="Enter summary content..."
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="flex justify-end gap-3">
          <el-button @click="showEditDialog = false" class="!bg-transparent !border-white/10 !text-gray-400 hover:!text-white hover:!bg-white/5">Cancel</el-button>
          <el-button type="primary" @click="confirmEdit" :loading="saving" class="!bg-neon-blue/10 !border-neon-blue/20 !text-neon-blue hover:!bg-neon-blue/20">
            Save Changes
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { novelApi } from '@/api'
import { ArrowLeft, Edit, Delete, Location, Search } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const saving = ref(false)
const summaries = ref([])
const searchQuery = ref('')
const showEditDialog = ref(false)
const editForm = ref({
  id: '',
  text: ''
})

const filteredSummaries = computed(() => {
  if (!searchQuery.value) return summaries.value
  const query = searchQuery.value.toLowerCase()
  return summaries.value.filter(item => 
    item.text.toLowerCase().includes(query) || 
    item.id.toLowerCase().includes(query)
  )
})

function goBack() {
  router.back()
}

async function loadSummaries() {
  loading.value = true
  try {
    const { data } = await novelApi.getRagSummaries(route.params.id)
    summaries.value = data
  } catch (error) {
    ElMessage.error('Failed to load summaries')
  } finally {
    loading.value = false
  }
}

function handleEdit(item) {
  editForm.value = {
    id: item.id,
    text: item.text
  }
  showEditDialog.value = true
}

async function confirmEdit() {
  if (!editForm.value.text) return
  
  saving.value = true
  try {
    await novelApi.updateRagSummary(route.params.id, editForm.value.id, {
      text: editForm.value.text
    })
    ElMessage.success('Updated successfully')
    showEditDialog.value = false
    await loadSummaries()
  } catch (error) {
    ElMessage.error('Update failed')
  } finally {
    saving.value = false
  }
}

function handleDelete(item) {
  ElMessageBox.confirm(
    'Are you sure you want to delete this summary? This action cannot be undone.',
    'Warning',
    {
      confirmButtonText: 'Delete',
      cancelButtonText: 'Cancel',
      type: 'warning',
      customClass: 'glass-dialog-override'
    }
  ).then(async () => {
    try {
      await novelApi.deleteRagSummary(route.params.id, item.id)
      ElMessage.success('Deleted successfully')
      await loadSummaries()
    } catch (error) {
      ElMessage.error('Deletion failed')
    }
  })
}

onMounted(() => {
  loadSummaries()
})
</script>

<style scoped>
.glass-input-override :deep(.el-input__wrapper) {
  background-color: rgba(255, 255, 255, 0.05);
  box-shadow: none;
  border: 1px solid rgba(255, 255, 255, 0.1);
  transition: all 0.3s;
}

.glass-input-override :deep(.el-input__wrapper:hover),
.glass-input-override :deep(.el-input__wrapper.is-focus) {
  background-color: rgba(255, 255, 255, 0.1);
  border-color: rgba(0, 240, 255, 0.5);
}

.glass-input-override :deep(.el-input__inner) {
  color: white;
}
</style>
