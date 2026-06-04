import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'chat', component: ()=>import('../views/ChatView.vue') },
  { path: '/search', name: 'search', component: ()=>import('../views/SearchView.vue') },
  { path: '/docs', name: 'docs', component:  ()=>import('../views/DocsView.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
