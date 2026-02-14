<template>
  <div class="h-screen w-screen overflow-hidden bg-space-950 text-gray-100 flex font-sans relative selection:bg-neon-blue/30 selection:text-neon-blue">
    <!-- Background Effects -->
    <div class="absolute inset-0 z-0 overflow-hidden pointer-events-none">
      <div class="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-neon-purple/10 blur-[120px] animate-pulse-slow"></div>
      <div class="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] rounded-full bg-neon-blue/10 blur-[120px] animate-pulse-slow delay-1000"></div>
    </div>

    <!-- Sidebar -->
    <aside class="w-64 z-10 glass-panel border-r border-white/5 flex flex-col backdrop-blur-xl bg-space-900/60 transition-all duration-300">
      <div class="h-16 flex items-center px-6 border-b border-white/5 shrink-0">
        <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-neon-blue to-neon-purple flex items-center justify-center mr-3 shadow-lg shadow-neon-blue/20">
          <span class="font-bold text-white text-lg">S</span>
        </div>
        <h1 class="text-xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400 font-display">StoryWeaver</h1>
      </div>

      <nav class="flex-1 p-4 space-y-2 overflow-y-auto custom-scrollbar">
        <router-link to="/" custom v-slot="{ navigate, isActive }">
          <div @click="navigate" 
               class="flex items-center px-4 py-3 rounded-xl cursor-pointer transition-all duration-300 group"
               :class="isActive ? 'bg-neon-blue/10 text-neon-blue border border-neon-blue/20 shadow-[0_0_15px_rgba(0,240,255,0.1)]' : 'hover:bg-white/5 text-gray-400 hover:text-white border border-transparent'">
            <el-icon :class="isActive ? 'text-neon-blue' : 'text-gray-500 group-hover:text-white'" class="mr-3 text-lg transition-colors"><HomeFilled /></el-icon>
            <span class="font-medium">首页</span>
            <div v-if="isActive" class="ml-auto w-1.5 h-1.5 rounded-full bg-neon-blue shadow-[0_0_8px_rgba(0,240,255,0.8)]"></div>
          </div>
        </router-link>
        
        <router-link to="/" custom v-slot="{ navigate, isActive }">
          <div @click="navigate" 
               class="flex items-center px-4 py-3 rounded-xl cursor-pointer transition-all duration-300 group"
               :class="isActive ? 'bg-neon-blue/10 text-neon-blue border border-neon-blue/20 shadow-[0_0_15px_rgba(0,240,255,0.1)]' : 'hover:bg-white/5 text-gray-400 hover:text-white border border-transparent'">
            <el-icon :class="isActive ? 'text-neon-blue' : 'text-gray-500 group-hover:text-white'" class="mr-3 text-lg transition-colors"><Folder /></el-icon>
            <span class="font-medium">我的作品</span>
            <div v-if="isActive" class="ml-auto w-1.5 h-1.5 rounded-full bg-neon-blue shadow-[0_0_8px_rgba(0,240,255,0.8)]"></div>
          </div>
        </router-link>
        <router-link to="/settings" custom v-slot="{ navigate, isActive }">
          <div @click="navigate" 
               class="flex items-center px-4 py-3 rounded-xl cursor-pointer transition-all duration-300 group"
               :class="isActive ? 'bg-neon-blue/10 text-neon-blue border border-neon-blue/20 shadow-[0_0_15px_rgba(0,240,255,0.1)]' : 'hover:bg-white/5 text-gray-400 hover:text-white border border-transparent'">
            <el-icon :class="isActive ? 'text-neon-blue' : 'text-gray-500 group-hover:text-white'" class="mr-3 text-lg transition-colors"><Setting /></el-icon>
            <span class="font-medium">设置</span>
            <div v-if="isActive" class="ml-auto w-1.5 h-1.5 rounded-full bg-neon-blue shadow-[0_0_8px_rgba(0,240,255,0.8)]"></div>
          </div>
        </router-link>
      </nav>

      <div class="p-4 border-t border-white/5 shrink-0">
        <div class="flex items-center p-3 rounded-xl bg-white/5 hover:bg-white/10 cursor-pointer transition-colors border border-white/5 group">
          <div class="w-8 h-8 rounded-full bg-gradient-to-tr from-gray-700 to-gray-600 flex items-center justify-center text-xs font-bold border border-white/10 group-hover:border-neon-blue/30 transition-colors">User</div>
          <div class="ml-3">
            <p class="text-sm font-medium text-white group-hover:text-neon-blue transition-colors">Writer</p>
            <p class="text-xs text-gray-500">Pro Plan</p>
          </div>
        </div>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="flex-1 z-10 flex flex-col relative h-full overflow-hidden">
      <!-- Top Bar -->
      <header class="h-16 glass-panel border-b border-white/5 flex items-center justify-between px-8 bg-space-900/40 backdrop-blur-md sticky top-0 z-20 shrink-0">
        <div class="flex items-center text-sm text-gray-400">
          <span class="hover:text-white cursor-pointer transition-colors">Workspace</span>
          <el-icon class="mx-2 text-gray-600"><ArrowRight /></el-icon>
          <span class="text-white font-medium">Dashboard</span>
        </div>
        <div class="flex items-center gap-4">
          <div class="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center text-gray-400 hover:text-white hover:bg-white/10 cursor-pointer transition-all border border-transparent hover:border-white/10">
            <el-icon><Bell /></el-icon>
          </div>
        </div>
      </header>

      <!-- Router View Container -->
      <div class="flex-1 overflow-y-auto p-8 scroll-smooth relative custom-scrollbar">
         <router-view v-slot="{ Component }">
           <transition name="fade" mode="out-in">
             <component :is="Component" />
           </transition>
         </router-view>
      </div>
    </main>
  </div>
</template>

<script setup>
import { HomeFilled, Folder, Setting, ArrowRight, Bell } from '@element-plus/icons-vue'
</script>

<style>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.2);
}
</style>
