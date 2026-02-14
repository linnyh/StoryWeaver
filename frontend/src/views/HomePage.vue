<template>
  <div class="home-page">
    <el-card class="novel-list-card">
      <template #header>
        <div class="card-header">
          <div class="left">
            <span>我的小说</span>
            <el-button 
              v-if="isSelectionMode" 
              type="danger" 
              size="small" 
              plain
              @click="handleBatchDelete"
              :disabled="selectedNovels.length === 0"
            >
              删除选中 ({{ selectedNovels.length }})
            </el-button>
            <el-button 
              v-if="isSelectionMode" 
              size="small" 
              @click="cancelSelection"
            >
              取消
            </el-button>
          </div>
          <div class="right">
            <el-button 
              v-if="!isSelectionMode && novels.length > 0" 
              link 
              type="primary" 
              @click="isSelectionMode = true"
            >
              批量管理
            </el-button>
            <el-button type="primary" @click="showCreateDialog = true">
              <el-icon><Plus /></el-icon>
              新建小说
            </el-button>
          </div>
        </div>
      </template>

      <div v-if="loading" class="loading-container">
        <el-skeleton :rows="5" animated />
      </div>

      <div v-else-if="novels.length === 0" class="empty-state">
        <el-empty description="还没有小说，点击新建开始创作" />
      </div>

      <div v-else class="novel-grid">
        <el-card
          v-for="novel in novels"
          :key="novel.id"
          class="novel-card"
          :class="{ 'is-selected': selectedNovels.includes(novel.id) }"
          shadow="hover"
          @click="handleNovelClick(novel)"
        >
          <!-- 选择模式下的遮罩层 -->
          <div v-if="isSelectionMode" class="selection-overlay">
            <el-checkbox 
              :model-value="selectedNovels.includes(novel.id)"
              @change="toggleSelection(novel.id)"
              @click.stop
            />
          </div>

          <div class="card-header">
            <h3>{{ novel.title }}</h3>
            <!-- 非选择模式下显示单个删除按钮 -->
            <el-button 
              v-if="!isSelectionMode"
              type="danger" 
              link 
              :icon="Delete" 
              @click.stop="handleDeleteNovel(novel)"
              class="delete-btn"
            />
          </div>
          <p class="novel-premise">{{ novel.premise || '暂无简介' }}</p>
          <div class="novel-meta">
            <el-tag size="small" effect="plain">{{ novel.genre || '未分类' }}</el-tag>
            <el-tag size="small" type="info" effect="plain">{{ novel.tone || '未设定' }}</el-tag>
          </div>
        </el-card>
        
        <el-card class="add-card" shadow="hover" @click="showCreateDialog = true">
          <div class="add-content">
            <el-icon :size="32"><Plus /></el-icon>
            <span>新建小说</span>
          </div>
        </el-card>
      </div>
    </el-card>

    <!-- 新建小说对话框 -->
    <el-dialog v-model="showCreateDialog" title="创建新小说" width="500px">
      <el-form :model="newNovel" label-width="80px">
        <el-form-item label="标题">
          <el-input v-model="newNovel.title" placeholder="输入小说标题" />
        </el-form-item>
        <el-form-item label="故事核">
          <el-input
            v-model="newNovel.premise"
            type="textarea"
            :rows="3"
            placeholder="一句话概括你的故事"
          />
        </el-form-item>
        <el-form-item label="题材">
          <el-select v-model="newNovel.genre" placeholder="选择题材">
            <el-option label="玄幻" value="玄幻" />
            <el-option label="科幻" value="科幻" />
            <el-option label="言情" value="言情" />
            <el-option label="悬疑" value="悬疑" />
            <el-option label="都市" value="都市" />
          </el-select>
        </el-form-item>
        <el-form-item label="风格">
          <el-select v-model="newNovel.tone" placeholder="选择风格">
            <el-option label="严肃" value="严肃" />
            <el-option label="幽默" value="幽默" />
            <el-option label="黑暗" value="黑暗" />
            <el-option label="轻松" value="轻松" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreateNovel" :loading="creating">
          创建
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { novelApi } from '@/api'
import { useRouter } from 'vue-router'
import { Plus, Delete } from '@element-plus/icons-vue'
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

<style lang="scss" scoped>
.home-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.novel-list-card {
  min-height: 500px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  
  .left {
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 16px;
    font-weight: bold;
  }
  
  .right {
    display: flex;
    gap: 12px;
  }
}

.novel-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
  padding: 20px 0;
}

.novel-card {
  height: 180px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
  display: flex;
  flex-direction: column;
  position: relative;
  border-radius: 12px;
  border: 1px solid #ebeef5;
  overflow: hidden;

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 24px rgba(0, 0, 0, 0.08);
    border-color: #dcdfe6;

    .delete-btn {
      opacity: 1;
    }
  }

  &.is-selected {
    border-color: #409eff;
    background-color: #ecf5ff;
    transform: translateY(-4px);
  }

  :deep(.el-card__body) {
    height: 100%;
    padding: 20px;
    display: flex;
    flex-direction: column;
    box-sizing: border-box;
  }

  .selection-overlay {
    position: absolute;
    top: 12px;
    right: 12px;
    z-index: 20;
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 12px;
    width: 100%;

    h3 {
      margin: 0;
      font-size: 18px;
      font-weight: 600;
      color: #303133;
      line-height: 1.4;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
      flex: 1;
      padding-right: 8px; 
    }

    .delete-btn {
      flex-shrink: 0;
      opacity: 0;
      transition: opacity 0.2s;
      padding: 8px;
      margin-top: -8px;
      margin-right: -8px;
      z-index: 10;
    }
  }

  &:hover .delete-btn {
    opacity: 1;
  }

  .novel-premise {
    font-size: 14px;
    color: #606266;
    line-height: 1.6;
    margin: 0 0 16px;
    flex: 1;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .novel-meta {
    display: flex;
    gap: 8px;
    margin-top: auto;
  }
}

.add-card {
  height: 180px;
  cursor: pointer;
  border: 2px dashed #dcdfe6;
  background-color: #fcfcfc;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  transition: all 0.3s;

  &:hover {
    border-color: #409eff;
    color: #409eff;
    background-color: #ecf5ff;
  }

  :deep(.el-card__body) {
    padding: 0;
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .add-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 12px;
    color: #909399;
    
    span {
      font-size: 16px;
    }
  }
}

.empty-state {
  padding: 80px 0;
}
</style>
