<template>
  <div class="novel-page">
    <el-row :gutter="20">
      <!-- 左侧：章节树 -->
      <el-col :span="6">
        <el-card class="chapter-tree-card">
          <template #header>
            <div class="card-header">
              <span>章节结构</span>
              <div class="header-buttons">
                <el-button
                  link
                  type="primary"
                  size="small"
                  @click="handleExport"
                  :loading="exporting"
                  :disabled="!currentNovel"
                >
                  <el-icon><Download /></el-icon>
                  导出全文
                </el-button>
                <el-button
                  type="primary"
                  size="small"
                  @click="handleGenerateOutline"
                  :loading="generatingOutline"
                  :disabled="!currentNovel"
                >
                  生成大纲
                </el-button>
              </div>
            </div>
          </template>

          <div v-if="!currentNovel" class="empty-state">
            <el-skeleton :rows="3" animated />
          </div>

          <div v-else-if="chapters.length === 0" class="empty-state">
            <el-empty description="暂无章节" :image-size="80" />
          </div>

          <div v-else class="chapter-tree">
            <el-tree
              :data="treeData"
              :props="treeProps"
              @node-click="handleChapterClick"
              node-key="id"
              :current-node-key="currentChapter?.id"
              default-expand-all
              highlight-current
            >
              <template #default="{ node, data }">
                <span class="tree-node">
                  <span>{{ node.label }}</span>
                  <el-tag v-if="data.sceneCount > 0" size="small" type="info">
                    {{ data.sceneCount }} 场景
                  </el-tag>
                </span>
              </template>
            </el-tree>
          </div>
        </el-card>
      </el-col>

      <!-- 中间：章节/场景内容 -->
      <el-col :span="12">
        <el-card class="content-card">
          <template #header>
            <div class="card-header">
              <span>{{ currentChapter?.title || '选择一个章节' }}</span>
              <div v-if="currentChapter" class="header-actions">
                <el-button
                  size="small"
                  @click="handleUpdateSummary"
                  :loading="summarizing"
                  :disabled="scenes.length === 0"
                >
                  更新摘要
                </el-button>
                <el-button
                  size="small"
                  @click="handleGenerateBeats"
                  :loading="generatingBeats"
                >
                  拆分场景
                </el-button>
              </div>
            </div>
          </template>

          <div v-if="!currentChapter" class="empty-state">
            <el-empty description="从左侧选择章节" />
          </div>

          <div v-else>
            <!-- 章节概要 -->
            <div v-if="currentChapter.summary" class="chapter-summary">
              <h4>章节概要</h4>
              <p>{{ currentChapter.summary }}</p>
            </div>

            <!-- 场景列表 -->
            <div v-if="scenes.length > 0" class="scene-list">
              <div
                v-for="scene in scenes"
                :key="scene.id"
                class="scene-item"
                @click="$router.push(`/write/${scene.id}`)"
              >
                <div class="scene-info">
                  <div class="scene-location">
                    <el-icon><Location /></el-icon>
                    {{ scene.location || '未指定地点' }}
                  </div>
                  <div class="scene-beat">
                    {{ scene.beat_description || '暂无场景描述' }}
                  </div>
                  <div class="scene-status">
                    <el-tag :type="scene.status === 'approved' ? 'success' : 'info'" size="small">
                      {{ scene.status === 'approved' ? '已完成' : '草稿' }}
                    </el-tag>
                  </div>
                </div>
              </div>
            </div>

            <div v-else class="empty-state">
              <el-empty description="暂无场景，点击「拆分场景」生成" :image-size="60" />
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：角色和世界观 -->
      <el-col :span="6">
        <el-card class="sidebar-card">
          <template #header>
            <div class="card-header">
              <span>资料库</span>
              <el-button link size="small" @click="goToRag">
                <el-icon><Files /></el-icon>
                RAG 摘要
              </el-button>
            </div>
          </template>
          <el-tabs v-model="activeTab">
            <el-tab-pane label="角色" name="characters">
              <div class="sidebar-content">
                <div
                  v-for="char in characters"
                  :key="char.id"
                  class="character-item"
                >
                  <div class="char-name">{{ char.name }}</div>
                  <div class="char-role">{{ char.role || '配角' }}</div>
                </div>
                <el-empty v-if="characters.length === 0" description="暂无角色" :image-size="60" />
              </div>
            </el-tab-pane>
            <el-tab-pane label="世界观" name="lore">
              <div class="sidebar-content">
                <div
                  v-for="lore in lores"
                  :key="lore.id"
                  class="lore-item"
                >
                  <div class="lore-title">{{ lore.title }}</div>
                  <div class="lore-content">{{ lore.content }}</div>
                </div>
                <el-empty v-if="lores.length === 0" description="暂无世界观设定" :image-size="60" />
              </div>
            </el-tab-pane>
          </el-tabs>
        </el-card>
      </el-col>
    </el-row>

    <!-- 生成大纲对话框 -->
    <el-dialog v-model="showOutlineDialog" title="生成大纲" width="500px">
      <el-form :model="outlineForm" label-width="80px">
        <el-form-item label="故事核">
          <el-input
            v-model="outlineForm.premise"
            type="textarea"
            :rows="3"
            placeholder="一句话概括你的故事"
          />
        </el-form-item>
        <el-form-item label="章节数">
          <el-input-number v-model="outlineForm.numChapters" :min="5" :max="30" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showOutlineDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmGenerateOutline" :loading="generatingOutline">
          生成
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useNovelStore } from '@/stores/novel'
import { ElMessage } from 'element-plus'
import { Download, Location, Files } from '@element-plus/icons-vue'

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

const treeProps = {
  // children: 'scenes',
  label: 'title'
}

const treeData = computed(() => {
  return chapters.value.map(chapter => ({
    id: chapter.id,
    title: chapter.title || `第 ${chapter.order_index} 章`,
    sceneCount: chapter.scene_count || 0
  }))
})

async function loadData() {
  const novelId = route.params.id
  if (!novelId) return

  // 只有当小说ID发生变化时才重置状态
  if (store.currentNovel?.id !== novelId) {
    store.reset()
    try {
      await store.loadNovel(novelId)
      await store.loadChapters(novelId)
      await store.loadCharacters(novelId)
      await store.loadLores(novelId)

      if (currentNovel.value?.premise) {
        outlineForm.value.premise = currentNovel.value.premise
      }
    } catch (error) {
      ElMessage.error('加载小说详情失败')
      console.error(error)
    }
  } else {
    // 如果小说ID没变（例如从写作页返回），我们只需要刷新一下场景列表以获取最新状态（如完成状态）
    // 如果当前选了章节，就刷新该章节的场景
    if (store.currentChapter) {
      try {
        await store.loadScenes(store.currentChapter.id)
      } catch (error) {
        console.error('Refresh scenes error:', error)
      }
    }
  }
}

function handleChapterClick(data) {
  store.currentChapter = chapters.value.find(c => c.id === data.id)
  store.loadScenes(data.id)
}

function handleGenerateOutline() {
  showOutlineDialog.value = true
}

async function confirmGenerateOutline() {
  if (!outlineForm.value.premise) {
    ElMessage.warning('请输入故事核')
    return
  }

  generatingOutline.value = true
  try {
    await store.generateOutline(route.params.id, {
      premise: outlineForm.value.premise,
      genre: currentNovel.value.genre || '玄幻',
      tone: currentNovel.value.tone || '严肃',
      num_chapters: outlineForm.value.numChapters
    })
    await store.loadCharacters(route.params.id)
    await store.loadLores(route.params.id)
    ElMessage.success('大纲生成成功')
    showOutlineDialog.value = false
  } catch (error) {
    console.error('Generate outline error:', error)
    ElMessage.error(error.message || '生成失败')
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
    // 重新加载场景列表
    await store.loadScenes(currentChapter.value.id)
    ElMessage.success('场景拆分成功')
  } catch (error) {
    ElMessage.error('生成失败')
  } finally {
    generatingBeats.value = false
  }
}

async function handleUpdateSummary() {
  if (!currentChapter.value) return

  summarizing.value = true
  try {
    await store.summarizeChapter(currentChapter.value.id)
    ElMessage.success('摘要更新成功')
  } catch (error) {
    console.error(error)
    ElMessage.error(error.message || '更新摘要失败')
  } finally {
    summarizing.value = false
  }
}

async function handleExport() {
  if (!currentNovel.value) return

  exporting.value = true
  try {
    const response = await store.exportNovel(route.params.id)
    
    // Create download link
    const blob = new Blob([response.data], { type: 'text/plain;charset=utf-8' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    
    // Extract filename from header or use default
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
    
    ElMessage.success('导出成功')
  } catch (error) {
    console.error(error)
    ElMessage.error('导出失败')
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

<style lang="scss" scoped>
.novel-page {
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;

  .header-buttons {
    display: flex;
    gap: 8px;
    align-items: center;
  }
}

.chapter-tree-card {
  height: calc(100vh - 140px);

  .tree-node {
    display: flex;
    align-items: center;
    gap: 8px;
    width: 100%;
  }
}

.content-card {
  height: calc(100vh - 140px);
  overflow-y: auto;

  .chapter-summary {
    padding: 16px;
    background: #f5f7fa;
    border-radius: 8px;
    margin-bottom: 16px;

    h4 {
      margin: 0 0 8px;
      font-size: 14px;
      color: #666;
    }

    p {
      margin: 0;
      font-size: 14px;
      line-height: 1.6;
      color: #333;
    }
  }

  .scene-item {
    padding: 16px;
    border-bottom: 1px solid #eee;
    cursor: pointer;
    transition: all 0.2s;

    &:hover {
      background: #f5f7fa;
    }

    .scene-location {
      display: flex;
      align-items: center;
      gap: 4px;
      font-weight: 500;
      color: #333;
      margin-bottom: 8px;
    }

    .scene-beat {
      font-size: 14px;
      color: #666;
      margin-bottom: 8px;
      line-height: 1.5;
    }
  }
}

.sidebar-card {
  height: calc(100vh - 140px);

  .sidebar-content {
    max-height: 400px;
    overflow-y: auto;
  }

  .character-item {
    padding: 12px;
    border-bottom: 1px solid #eee;

    .char-name {
      font-weight: 500;
      margin-bottom: 4px;
    }

    .char-role {
      font-size: 12px;
      color: #999;
    }
  }

  .lore-item {
    padding: 12px;
    border-bottom: 1px solid #eee;

    .lore-title {
      font-weight: 500;
      margin-bottom: 4px;
      color: #409eff;
    }

    .lore-content {
      font-size: 13px;
      color: #666;
      line-height: 1.5;
    }
  }
}
</style>
