<script setup>
import { onMounted, computed } from 'vue'
import { useUserStore } from './stores/user'
import { useRoute } from 'vue-router'
import NavBar from './components/NavBar.vue'
import UserManual from './components/UserManual.vue'

const userStore = useUserStore()
const route = useRoute()

// 计算当前是否需要显示导航栏（登录和注册页面不显示）
const showNavBar = computed(() => {
  return !route.path.includes('/login') && !route.path.includes('/register')
})

onMounted(async () => {
  console.log('App组件挂载，检查用户登录状态')
  if (userStore.isLoggedIn && !userStore.userInfo) {
    console.log('用户已登录但无用户信息，尝试获取用户信息')
    await userStore.fetchUserInfo()
  }
})
</script>

<template>
  <!-- 登录和注册页面不显示导航栏 -->
  <NavBar v-if="showNavBar" />
  <router-view></router-view>
  <!-- 用户手册按钮，固定在右下角 -->
  <UserManual />
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen,
    Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
}

/* 添加全局页面内容样式，考虑导航栏高度 */
.page-content {
  padding-top: 20px;
}
</style>
