<template>
  <div class="max-w-7xl mx-auto space-y-8 pb-12">
    <!-- Hero Section -->
    <div class="relative overflow-hidden rounded-3xl bg-gradient-to-r from-space-800 to-space-900 border border-white/10 shadow-2xl p-8 md:p-12 group">
      <div class="absolute top-0 right-0 -mt-20 -mr-20 w-80 h-80 bg-neon-purple/20 rounded-full blur-[80px] group-hover:bg-neon-purple/30 transition-colors duration-1000"></div>
      <div class="relative z-10">
        <h1 class="text-4xl md:text-5xl font-bold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-white via-blue-100 to-gray-400 font-display">
          Welcome back, Writer.
        </h1>
        <p class="text-gray-400 text-lg max-w-2xl mb-8 leading-relaxed">
          Your universe awaits. Continue weaving your stories or start a new journey into the unknown.
        </p>
        
        <div class="flex items-center gap-4">
          <button @click="showCreateDialog = true" class="btn-primary flex items-center gap-2 group">
            <el-icon class="text-lg group-hover:rotate-90 transition-transform duration-300"><Plus /></el-icon>
            <span>Create New Novel</span>
          </button>
          <button class="btn-ghost flex items-center gap-2">
            <el-icon><Document /></el-icon>
            <span>Documentation</span>
          </button>
        </div>
      </div>
      
      <!-- Stats -->
      <div class="mt-12 grid grid-cols-3 gap-8 border-t border-white/5 pt-8">
        <div>
          <div class="text-3xl font-bold text-white mb-1">{{ novels.length }}</div>
          <div class="text-sm text-gray-500 uppercase tracking-wider font-medium">Novels</div>
        </div>
        <div>
          <div class="text-3xl font-bold text-white mb-1">12</div>
          <div class="text-sm text-gray-500 uppercase tracking-wider font-medium">Chapters</div>
        </div>
        <div>
          <div class="text-3xl font-bold text-white mb-1">24k</div>
          <div class="text-sm text-gray-500 uppercase tracking-wider font-medium">Words</div>
        </div>
      </div>
    </div>

    <!-- Novels Grid -->
    <div>
      <div class="flex items-center justify-between mb-6">
        <h2 class="text-2xl font-bold text-white flex items-center gap-3 font-display">
          <span class="w-2 h-8 rounded-full bg-neon-blue shadow-[0_0_10px_rgba(0,240,255,0.5)]"></span>
          Your Novels
        </h2>
        
        <div class="flex items-center gap-2">
           <button 
              v-if="!isSelectionMode && novels.length > 0" 
              @click="isSelectionMode = true"
              class="text-sm text-gray-400 hover:text-white transition-colors px-3 py-1 rounded-lg hover:bg-white/5 flex items-center gap-1"
            >
              <el-icon><Setting /></el-icon>
              Manage
            </button>
            <template v-if="isSelectionMode">
               <span class="text-sm text-gray-400 mr-2">Selected: {{ selectedNovels.length }}</span>
               <button 
                  @click="handleBatchDelete"
                  :disabled="selectedNovels.length === 0"
                  class="text-sm text-red-400 hover:text-red-300 transition-colors px-3 py-1 rounded-lg hover:bg-red-500/10 disabled:opacity-50 flex items-center gap-1"
               >
                 <el-icon><Delete /></el-icon>
                 Delete
               </button>
               <button 
                  @click="cancelSelection"
                  class="text-sm text-gray-400 hover:text-white transition-colors px-3 py-1 rounded-lg hover:bg-white/5"
               >
                 Cancel
               </button>
            </template>
        </div>
      </div>

      <div v-if="loading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
         <div v-for="i in 3" :key="i" class="h-72 rounded-2xl bg-white/5 animate-pulse border border-white/5"></div>
      </div>

      <div v-else-if="novels.length === 0" class="flex flex-col items-center justify-center py-20 border-2 border-dashed border-white/5 rounded-3xl bg-white/[0.02]">
        <div class="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center mb-4 text-gray-600">
           <el-icon size="32"><Notebook /></el-icon>
        </div>
        <h3 class="text-xl font-medium text-white mb-2">No novels yet</h3>
        <p class="text-gray-500 mb-6">Start your first masterpiece today.</p>
        <button @click="showCreateDialog = true" class="btn-primary">Create Novel</button>
      </div>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div 
          v-for="novel in novels" 
          :key="novel.id"
          @click="handleNovelClick(novel)"
          class="glass-card group relative p-6 rounded-2xl flex flex-col h-[280px] cursor-pointer overflow-hidden"
          :class="{ 'ring-2 ring-neon-blue bg-space-800/50': selectedNovels.includes(novel.id) }"
        >
          <!-- Gradient overlay on hover -->
          <div class="absolute inset-0 bg-gradient-to-br from-neon-blue/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"></div>
          
          <div class="relative z-10 flex flex-col h-full">
            <div class="flex justify-between items-start mb-4">
              <div class="flex gap-2">
                 <span v-if="novel.genre" class="px-2 py-1 rounded-md bg-neon-blue/10 text-neon-blue text-xs font-medium border border-neon-blue/20 backdrop-blur-sm">
                   {{ novel.genre }}
                 </span>
                 <span v-if="novel.tone" class="px-2 py-1 rounded-md bg-purple-500/10 text-purple-400 text-xs font-medium border border-purple-500/20 backdrop-blur-sm">
                   {{ novel.tone }}
                 </span>
              </div>
              
              <!-- Selection Checkbox -->
              <div v-if="isSelectionMode" @click.stop class="bg-space-900 rounded-full p-1 z-20">
                <el-checkbox 
                  :model-value="selectedNovels.includes(novel.id)"
                  @change="toggleSelection(novel.id)"
                />
              </div>
              
               <!-- Delete button (hover) -->
              <button 
                v-if="!isSelectionMode"
                @click.stop="handleDeleteNovel(novel)"
                class="opacity-0 group-hover:opacity-100 transition-opacity p-2 text-gray-500 hover:text-red-400 hover:bg-white/5 rounded-lg z-20"
              >
                <el-icon><Delete /></el-icon>
              </button>
            </div>

            <h3 class="text-xl font-bold text-white mb-3 line-clamp-1 group-hover:text-neon-blue transition-colors font-display">
              {{ novel.title }}
            </h3>
            
            <p class="text-gray-400 text-sm leading-relaxed line-clamp-4 flex-1 mb-4 font-light">
              {{ novel.premise || 'No premise defined yet...' }}
            </p>

            <div class="flex items-center justify-between text-xs text-gray-500 border-t border-white/5 pt-4 mt-auto">
              <div class="flex items-center gap-1">
                <el-icon><Clock /></el-icon>
                <span>Updated recently</span>
              </div>
              <div class="flex items-center gap-1 group-hover:translate-x-1 transition-transform text-neon-blue/80">
                <span>Open</span>
                <el-icon><ArrowRight /></el-icon>
              </div>
            </div>
          </div>
        </div>

        <!-- Add Card -->
        <div 
          @click="showCreateDialog = true"
          class="rounded-2xl border-2 border-dashed border-white/10 flex flex-col items-center justify-center h-[280px] cursor-pointer hover:border-neon-blue/50 hover:bg-white/[0.02] transition-all group"
        >
          <div class="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center mb-4 text-gray-500 group-hover:text-neon-blue group-hover:scale-110 transition-all group-hover:shadow-[0_0_20px_rgba(0,240,255,0.2)]">
            <el-icon size="32"><Plus /></el-icon>
          </div>
          <span class="text-gray-400 font-medium group-hover:text-white transition-colors">Create New Novel</span>
        </div>
      </div>
    </div>

    <!-- Create Dialog -->
    <el-dialog v-model="showCreateDialog" title="Create New Novel" width="500px" class="glass-dialog-override" destroy-on-close>
      <el-form :model="newNovel" label-position="top" class="mt-2">
        <el-form-item label="Title">
          <el-input v-model="newNovel.title" placeholder="Enter novel title" />
        </el-form-item>
        <el-form-item label="Premise">
          <el-input
            v-model="newNovel.premise"
            type="textarea"
            :rows="4"
            placeholder="What is your story about?"
          />
        </el-form-item>
        <div class="grid grid-cols-2 gap-4">
           <el-form-item label="Genre">
            <el-select v-model="newNovel.genre" placeholder="Select Genre" class="w-full">
              <el-option label="玄幻 (Fantasy)" value="玄幻" />
              <el-option label="科幻 (Sci-Fi)" value="科幻" />
              <el-option label="言情 (Romance)" value="言情" />
              <el-option label="悬疑 (Mystery)" value="悬疑" />
              <el-option label="都市 (Urban)" value="都市" />
            </el-select>
          </el-form-item>
          <el-form-item label="Tone">
            <el-select v-model="newNovel.tone" placeholder="Select Tone" class="w-full">
              <el-option label="严肃 (Serious)" value="严肃" />
              <el-option label="幽默 (Humorous)" value="幽默" />
              <el-option label="黑暗 (Dark)" value="黑暗" />
              <el-option label="轻松 (Light)" value="轻松" />
            </el-select>
          </el-form-item>
        </div>
      </el-form>
      <template #footer>
        <div class="flex justify-end gap-3">
          <el-button @click="showCreateDialog = false">Cancel</el-button>
          <el-button type="primary" @click="handleCreateNovel" :loading="creating">
            Create Novel
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { novelApi } from '@/api'
import { useRouter } from 'vue-router'
import { Plus, Delete, Document, Notebook, Clock, ArrowRight, Setting } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()

const novels = ref([])
const loading = ref(true)
const showCreateDialog = ref(false)
const creating = ref(false)
const isSelectionMode = ref(false)
const selectedNovels = ref([])

const newNovel = ref({
  title: '',
  premise: '',
  genre: '',
  tone: ''
})

async function loadNovels() {
  loading.value = true
  try {
    const { data } = await novelApi.list()
    novels.value = data
  } catch (error) {
    ElMessage.error('加载小说列表失败')
  } finally {
    loading.value = false
  }
}

async function handleCreateNovel() {
  if (!newNovel.value.title) {
    ElMessage.warning('请输入小说标题')
    return
  }

  creating.value = true
  try {
    const { data } = await novelApi.create(newNovel.value)
    ElMessage.success('创建成功')
    showCreateDialog.value = false
    router.push(`/novel/${data.id}`)
  } catch (error) {
    ElMessage.error('创建失败')
  } finally {
    creating.value = false
  }
}

function handleNovelClick(novel) {
  if (isSelectionMode.value) {
    toggleSelection(novel.id)
  } else {
    router.push(`/novel/${novel.id}`)
  }
}

function toggleSelection(id) {
  const index = selectedNovels.value.indexOf(id)
  if (index === -1) {
    selectedNovels.value.push(id)
  } else {
    selectedNovels.value.splice(index, 1)
  }
}

function cancelSelection() {
  isSelectionMode.value = false
  selectedNovels.value = []
}

async function handleDeleteNovel(novel) {
  ElMessageBox.confirm(
    `确定要删除小说《${novel.title}》吗？所有章节和设定都将被永久删除。`,
    '删除警告',
    {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(async () => {
    try {
      await novelApi.delete(novel.id)
      ElMessage.success('删除成功')
      await loadNovels()
    } catch (error) {
      ElMessage.error('删除失败')
    }
  }).catch(() => {
    // 用户取消删除
  })
}

async function handleBatchDelete() {
  if (selectedNovels.value.length === 0) return

  ElMessageBox.confirm(
    `确定要删除选中的 ${selectedNovels.value.length} 本小说吗？操作不可恢复。`,
    '批量删除警告',
    {
      confirmButtonText: '确认删除',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(async () => {
    try {
      // 并行删除
      await Promise.all(selectedNovels.value.map(id => novelApi.delete(id)))
      ElMessage.success('批量删除成功')
      selectedNovels.value = []
      isSelectionMode.value = false
      await loadNovels()
    } catch (error) {
      ElMessage.error('部分小说删除失败')
      await loadNovels() // 刷新列表以显示最新状态
    }
  }).catch(() => {
    // 用户取消删除
  })
}

onMounted(() => {
  loadNovels()
})
</script>

<style scoped>
/* Scoped overrides if needed, but relying mostly on Tailwind global classes */
</style>
