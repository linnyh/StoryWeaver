import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/HomePage.vue')
  },
  {
    path: '/novel/:id',
    name: 'Novel',
    component: () => import('@/views/NovelPage.vue')
  },
  {
    path: '/novel/:id/rag',
    name: 'RagView',
    component: () => import('@/views/RagPage.vue')
  },
  {
    path: '/write/:sceneId',
    name: 'Writer',
    component: () => import('@/views/WriterPage.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
