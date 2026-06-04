import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/login', name: 'login', component: () => import('../views/LoginView.vue'), meta: { guest: true } },
  { path: '/register', name: 'register', component: () => import('../views/RegisterView.vue'), meta: { guest: true } },
  { path: '/', name: 'chat', component: () => import('../views/ChatView.vue'), meta: { auth: true } },
  { path: '/search', name: 'search', component: () => import('../views/SearchView.vue'), meta: { auth: true } },
  { path: '/docs', name: 'docs', component: () => import('../views/DocsView.vue'), meta: { auth: true } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')

  if (to.meta.auth && !token) {
    return next('/login')
  }
  if (to.meta.guest && token) {
    return next('/')
  }
  next()
})

export default router
