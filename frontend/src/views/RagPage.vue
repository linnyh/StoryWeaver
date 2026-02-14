<template>
  <div class="rag-page">
    <el-card class="rag-card">
      <template #header>
        <div class="header">
          <div class="left">
            <el-button link @click="goBack">
              <el-icon><ArrowLeft /></el-icon>
              返回
            </el-button>
            <span class="title">RAG 知识库摘要</span>
          </div>
          <div class="right">
            <el-input
              v-model="searchQuery"
              placeholder="搜索摘要内容..."
              prefix-icon="Search"
              clearable
              style="width: 300px; margin-right: 16px"
            />
            <el-tag>共 {{ filteredSummaries.length }} 条记录</el-tag>
          </div>
        </div>
      </template>

      <div v-loading="loading" class="content">
        <el-empty v-if="!loading && filteredSummaries.length === 0" description="暂无摘要数据" />
        
        <div v-else class="summary-grid">
          <el-row :gutter="20">
            <el-col :span="24" v-for="(item, index) in filteredSummaries" :key="item.id">
              <el-card class="summary-item" shadow="hover">
                <div class="summary-header">
                  <div class="meta-info">
                    <span class="scene-id">
                      <el-icon><Location /></el-icon> 
                      场景 ID: {{ item.metadata?.scene_id || 'Unknown' }}
                    </span>
                    <el-divider direction="vertical" />
                    <span class="doc-id">Doc ID: {{ item.id }}</span>
                  </div>
                  <div class="actions">
                    <el-button type="primary" link size="small" @click="handleEdit(item)">
                      <el-icon><Edit /></el-icon> 编辑
                    </el-button>
                    <el-button type="danger" link size="small" @click="handleDelete(item)">
                      <el-icon><Delete /></el-icon> 删除
                    </el-button>
                  </div>
                </div>
                
                <div class="summary-content">
                  {{ item.text }}
                </div>
                
                <div class="summary-footer" v-if="item.metadata">
                  <div class="tags">
                    <el-tag size="small" type="info" effect="plain" v-for="(val, key) in item.metadata" :key="key" class="meta-tag">
                      {{ key }}: {{ val }}
                    </el-tag>
                  </div>
                </div>
              </el-card>
            </el-col>
          </el-row>
        </div>
      </div>
    </el-card>

    <!-- 编辑对话框 -->
    <el-dialog v-model="showEditDialog" title="编辑摘要" width="500px">
      <el-form :model="editForm">
        <el-form-item label="摘要内容">
          <el-input
            v-model="editForm.text"
            type="textarea"
            :rows="6"
            placeholder="请输入摘要内容"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmEdit" :loading="saving">
          保存
        </el-button>
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
    ElMessage.error('加载摘要失败')
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
    ElMessage.success('更新成功')
    showEditDialog.value = false
    await loadSummaries()
  } catch (error) {
    ElMessage.error('更新失败')
  } finally {
    saving.value = false
  }
}

function handleDelete(item) {
  ElMessageBox.confirm(
    '确定要删除这条摘要吗？此操作不可恢复。',
    '警告',
    {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(async () => {
    try {
      await novelApi.deleteRagSummary(route.params.id, item.id)
      ElMessage.success('删除成功')
      await loadSummaries()
    } catch (error) {
      ElMessage.error('删除失败')
    }
  })
}

onMounted(() => {
  loadSummaries()
})
</script>

<style lang="scss" scoped>
.rag-page {
  padding: 20px;
  height: 100%;
  box-sizing: border-box;
  background-color: #f5f7fa;
}

.rag-card {
  height: 100%;
  display: flex;
  flex-direction: column;
  border: none;
  
  :deep(.el-card__body) {
    flex: 1;
    overflow-y: auto;
    padding: 0;
    background-color: #f5f7fa;
  }
  
  :deep(.el-card__header) {
    padding: 16px 24px;
    border-bottom: 1px solid #ebeef5;
  }
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  
  .left {
    display: flex;
    align-items: center;
    gap: 12px;
    
    .title {
      font-size: 18px;
      font-weight: 600;
      color: #303133;
    }
  }
  
  .right {
    display: flex;
    align-items: center;
    gap: 16px;
  }
}

.summary-grid {
  padding: 24px;
  max-width: 1000px;
  margin: 0 auto;
}

.summary-item {
  margin-bottom: 24px;
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
  border: 1px solid #e4e7ed;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
  background-color: #ffffff;
  
  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 24px rgba(0, 0, 0, 0.08);
    border-color: #dcdfe6;
  }
  
  :deep(.el-card__body) {
    padding: 24px;
  }
  
  .summary-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding-bottom: 16px;
    border-bottom: 1px solid #f2f6fc;
    
    .meta-info {
      display: flex;
      align-items: center;
      gap: 12px;
      font-size: 13px;
      color: #606266;
      font-weight: 500;
      
      .scene-id {
        display: flex;
        align-items: center;
        gap: 6px;
        color: #409eff;
        background-color: #ecf5ff;
        padding: 4px 8px;
        border-radius: 4px;
      }
      
      .doc-id {
        font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
        color: #909399;
        font-size: 12px;
        background-color: #f4f4f5;
        padding: 2px 6px;
        border-radius: 4px;
      }
    }

    .actions {
      display: flex;
      align-items: center;
    }
  }
  
  .summary-content {
    font-size: 15px;
    line-height: 1.8;
    color: #303133;
    margin-bottom: 24px;
    white-space: pre-wrap;
    text-align: justify;
    padding: 0 4px;
  }
  
  .summary-footer {
    display: flex;
    justify-content: flex-end;
    padding-top: 16px;
    border-top: 1px dashed #ebeef5;
    
    .tags {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
  }
}
</style>