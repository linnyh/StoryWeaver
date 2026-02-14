<template>
  <div class="app-container">
    <el-container>
      <el-header class="app-header">
        <div class="header-left">
          <h1>StoryWeaver</h1>
          <span class="subtitle">AI 小说创作系统</span>
        </div>
        <div class="header-right">
          <el-button type="primary" @click="$router.push('/')">
            <el-icon><HomeFilled /></el-icon>
            首页
          </el-button>
        </div>
      </el-header>
      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { HomeFilled } from '@element-plus/icons-vue'
</script>

<style lang="scss">
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.app-container {
  height: 100%;
}

.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 0 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);

  .header-left {
    display: flex;
    align-items: baseline;
    gap: 12px;

    h1 {
      font-size: 24px;
      font-weight: 600;
    }

    .subtitle {
      font-size: 14px;
      opacity: 0.8;
    }
  }
}

.app-main {
  height: calc(100vh - 60px);
  background: #f5f7fa;
  padding: 20px;
}
</style>
