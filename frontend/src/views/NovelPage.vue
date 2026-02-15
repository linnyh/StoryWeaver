<template>
  <div class="h-full grid grid-cols-12 gap-6 p-1">
    <!-- Left: Chapter Tree -->
    <div class="col-span-3 flex flex-col glass-panel rounded-2xl overflow-hidden h-[calc(100vh-140px)]">
      <div class="p-4 border-b border-white/5 flex justify-between items-center bg-space-900/50">
        <span class="font-display text-white font-medium tracking-wide">Chapters</span>
        <div class="flex gap-2">
          <button 
            @click="handleExport" 
            :disabled="!currentNovel || exporting"
            class="p-1.5 rounded-lg hover:bg-white/10 text-gray-400 hover:text-neon-blue transition-colors disabled:opacity-50"
            title="Export Novel"
          >
            <el-icon><Download /></el-icon>
          </button>
          <button 
            @click="handleGenerateOutline" 
            :disabled="!currentNovel || generatingOutline"
            class="p-1.5 rounded-lg hover:bg-white/10 text-gray-400 hover:text-neon-purple transition-colors disabled:opacity-50"
            title="Generate Outline"
          >
            <el-icon><Operation /></el-icon>
          </button>
        </div>
      </div>

      <div class="flex-1 overflow-y-auto p-2 custom-scrollbar">
        <div v-if="!currentNovel" class="p-4 space-y-3">
          <div class="h-4 bg-white/5 rounded animate-pulse w-3/4"></div>
          <div class="h-4 bg-white/5 rounded animate-pulse w-1/2"></div>
        </div>

        <div v-else-if="chapters.length === 0" class="flex flex-col items-center justify-center h-full text-gray-500">
          <el-icon size="32" class="mb-2 opacity-50"><Document /></el-icon>
          <span class="text-sm">No chapters yet</span>
        </div>

        <div v-else class="space-y-1">
          <!-- Custom Tree Implementation for better styling control -->
           <div 
            v-for="chapter in chapters" 
            :key="chapter.id"
            @click="handleChapterClick(chapter)"
            class="group flex items-center justify-between p-3 rounded-xl cursor-pointer transition-all duration-200 border border-transparent"
            :class="currentChapter?.id === chapter.id ? 'bg-neon-blue/10 border-neon-blue/20 text-white shadow-[0_0_10px_rgba(0,240,255,0.1)]' : 'hover:bg-white/5 text-gray-400 hover:text-gray-200 hover:border-white/5'"
          >
            <div class="flex items-center gap-3 overflow-hidden">
              <div class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium"
                   :class="currentChapter?.id === chapter.id ? 'bg-neon-blue text-space-950' : 'bg-white/10 text-gray-500 group-hover:bg-white/20'">
                {{ chapter.order_index }}
              </div>
              <span class="truncate text-sm font-medium">{{ chapter.title || `Chapter ${chapter.order_index}` }}</span>
            </div>
            <span v-if="chapter.scene_count > 0" class="text-[10px] px-1.5 py-0.5 rounded bg-white/5 text-gray-500 group-hover:text-gray-300">
              {{ chapter.scene_count }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Center: Content -->
    <div class="col-span-6 flex flex-col glass-panel rounded-2xl overflow-hidden h-[calc(100vh-140px)]">
      <div class="p-4 border-b border-white/5 flex justify-between items-center bg-space-900/50 backdrop-blur-xl z-10">
        <h2 class="font-display text-lg text-white font-bold truncate pr-4">
          {{ currentChapter?.title || 'Select a Chapter' }}
        </h2>
        <div v-if="currentChapter" class="flex gap-2 shrink-0">
          <button 
            @click="handleUpdateSummary" 
            :disabled="scenes.length === 0 || summarizing"
            class="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 border border-white/5 text-xs font-medium text-gray-300 transition-colors disabled:opacity-50"
          >
            Update Summary
          </button>
          <button 
            @click="handleGenerateBeats" 
            :disabled="generatingBeats"
            class="px-3 py-1.5 rounded-lg bg-neon-blue/10 hover:bg-neon-blue/20 border border-neon-blue/20 text-xs font-medium text-neon-blue transition-colors disabled:opacity-50 flex items-center gap-1"
          >
            <el-icon><MagicStick /></el-icon>
            Split Scenes
          </button>
        </div>
      </div>

      <div class="flex-1 overflow-y-auto p-6 custom-scrollbar relative">
        <div v-if="!currentChapter" class="flex flex-col items-center justify-center h-full text-gray-500">
          <div class="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center mb-4">
            <el-icon size="24"><ArrowLeft /></el-icon>
          </div>
          <span>Select a chapter to start writing</span>
        </div>

        <div v-else class="space-y-6">
          <!-- Chapter Summary -->
          <div v-if="currentChapter.summary" class="p-4 rounded-xl bg-space-800/50 border border-white/5 text-sm leading-relaxed text-gray-300">
            <div class="text-xs uppercase tracking-wider text-gray-500 mb-2 font-bold">Summary</div>
            {{ currentChapter.summary }}
          </div>

          <!-- Scenes List -->
          <div v-if="scenes.length > 0" class="space-y-4">
            <div class="flex items-center gap-2 text-xs uppercase tracking-wider text-gray-500 font-bold mb-2">
              <span class="w-1.5 h-1.5 rounded-full bg-neon-purple"></span>
              Scenes Sequence
            </div>
            
            <div 
              v-for="(scene, index) in scenes" 
              :key="scene.id"
              @click="$router.push(`/write/${scene.id}`)"
              class="group relative p-4 rounded-xl border border-white/5 bg-white/[0.02] hover:bg-white/[0.05] hover:border-neon-purple/30 cursor-pointer transition-all duration-300 hover:transform hover:translate-x-1"
            >
              <!-- Connector Line -->
              <div v-if="index !== scenes.length - 1" class="absolute left-6 bottom-[-20px] w-0.5 h-[20px] bg-white/5 group-hover:bg-neon-purple/20 transition-colors"></div>

              <div class="flex justify-between items-start mb-2">
                <div class="flex items-center gap-2 text-neon-blue text-sm font-medium">
                  <el-icon><Location /></el-icon>
                  <span>{{ scene.location || 'Unknown Location' }}</span>
                </div>
                <div class="px-2 py-0.5 rounded text-[10px] uppercase font-bold tracking-wide"
                     :class="scene.status === 'approved' ? 'bg-green-500/10 text-green-400 border border-green-500/20' : 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/20'">
                  {{ scene.status === 'approved' ? 'Done' : 'Draft' }}
                </div>
              </div>
              
              <p class="text-gray-400 text-sm line-clamp-3 group-hover:text-gray-200 transition-colors">
                {{ scene.beat_description || 'No description available.' }}
              </p>
              
              <div class="mt-3 flex items-center text-xs text-gray-600 group-hover:text-neon-purple/70 transition-colors">
                 <span>Enter Scene</span>
                 <el-icon class="ml-1"><ArrowRight /></el-icon>
              </div>
            </div>
          </div>

          <div v-else class="flex flex-col items-center justify-center py-12 border-2 border-dashed border-white/5 rounded-xl">
            <p class="text-gray-500 mb-4">No scenes yet</p>
            <button @click="handleGenerateBeats" class="btn-ghost text-sm">
              Auto-Generate Scenes
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Right: Database Sidebar -->
    <div class="col-span-3 flex flex-col glass-panel rounded-2xl overflow-hidden h-[calc(100vh-140px)]">
      <div class="p-4 border-b border-white/5 flex justify-between items-center bg-space-900/50">
        <span class="font-display text-white font-medium tracking-wide">Database</span>
        <button @click="goToRag" class="p-1.5 rounded-lg hover:bg-white/10 text-gray-400 hover:text-white transition-colors" title="RAG Knowledge">
          <el-icon><Files /></el-icon>
        </button>
      </div>

      <div class="flex-1 flex flex-col overflow-hidden">
        <!-- Custom Tabs -->
        <div class="flex border-b border-white/5">
          <button 
            v-for="tab in ['characters', 'lore']" 
            :key="tab"
            @click="activeTab = tab"
            class="flex-1 py-3 text-xs font-bold uppercase tracking-wider transition-colors border-b-2"
            :class="activeTab === tab ? 'text-neon-blue border-neon-blue bg-white/5' : 'text-gray-500 border-transparent hover:text-gray-300 hover:bg-white/[0.02]'"
          >
            {{ tab }}
          </button>
        </div>

        <div class="flex-1 overflow-y-auto p-4 custom-scrollbar">
          <template v-if="activeTab === 'characters'">
            <div v-if="characters.length === 0" class="text-center py-8 text-gray-500 text-sm">No characters found</div>
            <div v-else class="space-y-3">
              <div v-for="char in characters" :key="char.id" class="p-3 rounded-xl bg-white/5 border border-white/5 hover:border-white/10 transition-colors">
                <div class="flex justify-between items-start">
                  <div class="font-medium text-white">{{ char.name }}</div>
                  <div class="text-[10px] px-1.5 py-0.5 rounded bg-white/10 text-gray-400">{{ char.role || 'NPC' }}</div>
                </div>
                <!-- Add more char details if available -->
              </div>
            </div>
          </template>

          <template v-if="activeTab === 'lore'">
            <div v-if="lores.length === 0" class="text-center py-8 text-gray-500 text-sm">No lore entries found</div>
            <div v-else class="space-y-3">
              <div v-for="lore in lores" :key="lore.id" class="p-3 rounded-xl bg-white/5 border border-white/5 hover:border-white/10 transition-colors">
                <div class="font-medium text-neon-blue mb-1 text-sm">{{ lore.title }}</div>
                <p class="text-xs text-gray-400 line-clamp-3">{{ lore.content }}</p>
              </div>
            </div>
          </template>
        </div>
      </div>
    </div>

    <!-- Dialogs -->
    <el-dialog v-model="showOutlineDialog" title="Generate Outline" width="500px" class="glass-dialog-override" destroy-on-close>
      <el-form :model="outlineForm" label-position="top">
        <el-form-item label="Core Premise">
          <el-input
            v-model="outlineForm.premise"
            type="textarea"
            :rows="4"
            placeholder="Summarize your story idea..."
          />
        </el-form-item>
        <el-form-item label="Target Chapter Count">
          <el-input-number v-model="outlineForm.numChapters" :min="5" :max="50" class="w-full" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="flex justify-end gap-3">
          <el-button @click="showOutlineDialog = false">Cancel</el-button>
          <el-button type="primary" @click="confirmGenerateOutline" :loading="generatingOutline">
            Generate
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useNovelStore } from '@/stores/novel'
import { ElMessage } from 'element-plus'
import { Download, Location, Files, Operation, Document, MagicStick, ArrowLeft, ArrowRight } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const store = useNovelStore()

const currentNovel = computed(() => store.currentNovel)
const chapters = computed(() => store.chapters)
const characters = computed(() => store.characters)
const lores = computed(() => store.lores)
const scenes = computed(() => store.scenes)
const currentChapter = computed(() => store.currentChapter)

const activeTab = ref('characters')
const generatingOutline = ref(false)
const generatingBeats = ref(false)
const summarizing = ref(false)
const exporting = ref(false)
const showOutlineDialog = ref(false)

const outlineForm = ref({
  premise: '',
  numChapters: 10
})

async function loadData() {
  const novelId = route.params.id
  if (!novelId) return

  if (store.currentNovel?.id !== novelId || !store.currentNovel) {
    // Reset state to prevent stale data from previous novel (especially scenes/chapters)
    store.reset()
    try {
      await store.loadNovel(novelId)
    } catch (error) {
      ElMessage.error('Failed to load novel details')
      console.error(error)
      return // Stop if novel loading fails
    }
    
    // Load related data independently
    await Promise.all([
      store.loadChapters(novelId).catch(e => console.error('Failed to load chapters', e)),
      store.loadCharacters(novelId).catch(e => console.error('Failed to load characters', e)),
      store.loadLores(novelId).catch(e => console.error('Failed to load lores', e))
    ])

    if (store.currentNovel?.premise) {
      outlineForm.value.premise = store.currentNovel.premise
    }
  } else {
    if (store.currentNovel?.premise) {
      outlineForm.value.premise = store.currentNovel.premise
    }
    // Even if ID hasn't changed, reload if data is missing (e.g. chapters list is empty)
    if (store.chapters.length === 0) {
       await Promise.all([
         store.loadChapters(novelId).catch(e => console.error('Failed to load chapters', e)),
         store.loadCharacters(novelId).catch(e => console.error('Failed to load characters', e)),
         store.loadLores(novelId).catch(e => console.error('Failed to load lores', e))
       ])
    }

    // If a chapter is currently selected, refresh its scenes
    if (store.currentChapter) {
      try {
        await store.loadScenes(store.currentChapter.id)
      } catch (error) {
        console.error('Refresh scenes error:', error)
      }
    }
  }
}

function handleChapterClick(chapter) {
  store.currentChapter = chapters.value.find(c => c.id === chapter.id)
  store.loadScenes(chapter.id)
}

function handleGenerateOutline() {
  showOutlineDialog.value = true
}

async function confirmGenerateOutline() {
  if (!outlineForm.value.premise) {
    ElMessage.warning('Please enter a story premise')
    return
  }

  generatingOutline.value = true
  try {
    await store.generateOutline(route.params.id, {
      premise: outlineForm.value.premise,
      genre: currentNovel.value.genre || 'Fantasy',
      tone: currentNovel.value.tone || 'Serious',
      num_chapters: outlineForm.value.numChapters
    })
    await store.loadCharacters(route.params.id)
    await store.loadLores(route.params.id)
    ElMessage.success('Outline generated successfully')
    showOutlineDialog.value = false
  } catch (error) {
    console.error('Generate outline error:', error)
    ElMessage.error(error.message || 'Generation failed')
  } finally {
    generatingOutline.value = false
  }
}

async function handleGenerateBeats() {
  if (!currentChapter.value) return

  generatingBeats.value = true
  try {
    await store.generateBeats(currentChapter.value.id, {
      num_beats: 6
    })
    await store.loadScenes(currentChapter.value.id)
    ElMessage.success('Scenes split successfully')
  } catch (error) {
    ElMessage.error('Failed to generate scenes')
  } finally {
    generatingBeats.value = false
  }
}

async function handleUpdateSummary() {
  if (!currentChapter.value) return

  summarizing.value = true
  try {
    await store.summarizeChapter(currentChapter.value.id)
    ElMessage.success('Summary updated')
  } catch (error) {
    console.error(error)
    ElMessage.error(error.message || 'Failed to update summary')
  } finally {
    summarizing.value = false
  }
}

async function handleExport() {
  if (!currentNovel.value) return

  exporting.value = true
  try {
    const response = await store.exportNovel(route.params.id)
    
    const blob = new Blob([response.data], { type: 'text/plain;charset=utf-8' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    
    let filename = `${currentNovel.value.title}.txt`
    const disposition = response.headers['content-disposition']
    if (disposition && disposition.indexOf('filename*=') !== -1) {
      const match = disposition.match(/filename\*=utf-8''(.+)/i)
      if (match && match[1]) {
        filename = decodeURIComponent(match[1])
      }
    }
    
    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('Export successful')
  } catch (error) {
    console.error(error)
    ElMessage.error('Export failed')
  } finally {
    exporting.value = false
  }
}

function goToRag() {
  router.push(`/novel/${route.params.id}/rag`)
}

onMounted(() => {
  loadData()
})

watch(
  () => route.params.id,
  (newId) => {
    if (newId) loadData()
  }
)
</script>

<style scoped>
/* Scoped overrides if needed */
</style>
