import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '../stores/user'

const router = createRouter({
  history: createWebHistory(),
  routes: [
  {
    path: '/',
      redirect: '/home'
  },
  {
    path: '/login',
    name: 'Login',
      component: () => import('../views/Login.vue'),
      meta: { requiresAuth: false }
  },
  {
    path: '/register',
    name: 'Register',
      component: () => import('../views/Register.vue'),
      meta: { requiresAuth: false }
  },
  {
    path: '/home',
    name: 'Home',
    component: () => import('../views/Home.vue'),
    meta: { requiresAuth: true }
    },
    {
      path: '/dashboard',
      name: 'Dashboard',
      component: () => import('../views/Dashboard.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/settings',
      name: 'Settings',
      component: () => import('../views/Settings.vue'),
      meta: { requiresAuth: true }
    }
  ]
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  
  // 检查路由是否需要认证
  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    // 如果需要认证但用户未登录，重定向到登录页
    next({ name: 'Login' })
  } else if (to.meta.requiresAuth === false && userStore.isLoggedIn) {
    // 如果用户已登录但访问登录/注册页，重定向到主页
    next({ name: 'Home' })
  } else {
    // 其他情况正常导航
    next()
  }
})

export default router 