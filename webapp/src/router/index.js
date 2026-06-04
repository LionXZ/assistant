import { createRouter, createWebHistory } from 'vue-router'
import ChatView from '../views/ChatView.vue'
import SearchView from '../views/SearchView.vue'
import DocsView from '../views/DocsView.vue'

const routes = [
  { path: '/', name: 'chat', component: ChatView },
  { path: '/search', name: 'search', component: SearchView },
  { path: '/docs', name: 'docs', component: DocsView },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
