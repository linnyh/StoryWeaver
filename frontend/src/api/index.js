import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 300000
})

// 小说 API
export const novelApi = {
  create: (data) => api.post('/novels/', data),
  list: () => api.get('/novels/'),
  get: (id) => api.get(`/novels/${id}`),
  update: (id, data) => api.put(`/novels/${id}`, data),
  delete: (id) => api.delete(`/novels/${id}`),
  generateOutline: (id, data) => api.post(`/novels/${id}/outline`, data),
  getRagSummaries: (id) => api.get(`/novels/${id}/rag/summaries`),
  updateRagSummary: (novelId, docId, data) => api.put(`/novels/${novelId}/rag/summaries/${docId}`, data),
  deleteRagSummary: (novelId, docId) => api.delete(`/novels/${novelId}/rag/summaries/${docId}`),
  export: (id) => api.get(`/novels/${id}/export`, { responseType: 'blob' })
}

// 章节 API
export const chapterApi = {
  create: (data) => api.post('/chapters/', data),
  list: (novelId) => api.get('/chapters/', { params: { novel_id: novelId } }),
  get: (id) => api.get(`/chapters/${id}`),
  update: (id, data) => api.put(`/chapters/${id}`, data),
  delete: (id) => api.delete(`/chapters/${id}`),
  generateBeats: (id, data) => api.post(`/chapters/${id}/beats`, data),
  summarize: (id) => api.post(`/chapters/${id}/summarize`)
}

// 场景 API
export const sceneApi = {
  create: (data) => api.post('/scenes/', data),
  list: (chapterId) => api.get('/scenes/', { params: { chapter_id: chapterId } }),
  get: (id) => api.get(`/scenes/${id}`),
  update: (id, data) => api.put(`/scenes/${id}`, data),
  delete: (id) => api.delete(`/scenes/${id}`),
  generate: (id) => new EventSource(`/api/scenes/${id}/generate`),
  summarize: (id) => api.post(`/scenes/${id}/summarize`),
  chat: (id, message) => api.post(`/scenes/${id}/chat`, { message }, { responseType: 'stream' }) // Use stream or handle SSE manually if needed, but for simple POST usually we use fetch for SSE
}

// 角色 API
export const characterApi = {
  create: (data) => api.post('/characters/', data),
  list: (novelId) => api.get('/characters/', { params: { novel_id: novelId } }),
  get: (id) => api.get(`/characters/${id}`),
  update: (id, data) => api.put(`/characters/${id}`, data),
  delete: (id) => api.delete(`/characters/${id}`)
}

// 世界观 API
export const loreApi = {
  create: (data) => api.post('/lore/', data),
  list: (novelId) => api.get('/lore/', { params: { novel_id: novelId } }),
  delete: (id) => api.delete(`/lore/${id}`)
}

export const relationshipApi = {
  list: (novelId) => api.get('/relationships/', { params: { novel_id: novelId } })
}

export default api
