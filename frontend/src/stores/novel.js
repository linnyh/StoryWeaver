import { defineStore } from 'pinia'
import { ref } from 'vue'
import { novelApi, chapterApi, sceneApi, characterApi, loreApi } from '@/api'

export const useNovelStore = defineStore('novel', () => {
  // 状态
  const currentNovel = ref(null)
  const chapters = ref([])
  const characters = ref([])
  const lores = ref([])
  const currentChapter = ref(null)
  const currentScene = ref(null)
  const scenes = ref([])

  // 加载小说
  async function loadNovel(id) {
    const { data } = await novelApi.get(id)
    currentNovel.value = data
    return data
  }

  // 加载章节列表
  async function loadChapters(novelId) {
    const { data } = await chapterApi.list(novelId)
    chapters.value = data
    return data
  }

  // 加载角色列表
  async function loadCharacters(novelId) {
    const { data } = await characterApi.list(novelId)
    characters.value = data
    return data
  }

  // 加载世界观列表
  async function loadLores(novelId) {
    const { data } = await loreApi.list(novelId)
    lores.value = data
    return data
  }

  // 加载场景列表
  async function loadScenes(chapterId) {
    const { data } = await sceneApi.list(chapterId)
    scenes.value = data
    return data
  }

  // 生成大纲
  async function generateOutline(novelId, data) {
    const response = await novelApi.generateOutline(novelId, data)
    await loadChapters(novelId)
    return response.data
  }

  // 生成场景细纲
  async function generateBeats(chapterId, data) {
    const response = await chapterApi.generateBeats(chapterId, data)
    await loadScenes(chapterId)
    return response.data
  }

  // 生成章节摘要
  async function summarizeChapter(chapterId) {
    const response = await chapterApi.summarize(chapterId)
    // 更新本地章节列表中的摘要
    const index = chapters.value.findIndex(c => c.id === chapterId)
    if (index !== -1) {
      chapters.value[index].summary = response.data.summary
    }
    // 如果当前选中的就是该章节，也更新
    if (currentChapter.value && currentChapter.value.id === chapterId) {
      currentChapter.value.summary = response.data.summary
    }
    return response.data
  }

  // 创建小说
  async function createNovel(data) {
    const response = await novelApi.create(data)
    return response.data
  }

  // 更新场景内容
  async function updateScene(sceneId, data) {
    const response = await sceneApi.update(sceneId, data)
    // 更新本地状态
    const index = scenes.value.findIndex(s => s.id === sceneId)
    if (index !== -1) {
      scenes.value[index] = response.data
    }
    return response.data
  }

  // 导出小说
  async function exportNovel(novelId) {
    const response = await novelApi.export(novelId)
    return response // 返回整个 response 以便获取 headers
  }

  // 重置状态
  function reset() {
    currentNovel.value = null
    chapters.value = []
    characters.value = []
    lores.value = []
    currentChapter.value = null
    currentScene.value = null
    scenes.value = []
  }

  return {
    currentNovel,
    chapters,
    characters,
    lores,
    currentChapter,
    currentScene,
    scenes,
    loadNovel,
    loadChapters,
    loadCharacters,
    loadLores,
    loadScenes,
    generateOutline,
    generateBeats,
    summarizeChapter,
    createNovel,
    updateScene,
    exportNovel,
    reset
  }
})
