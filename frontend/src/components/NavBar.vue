<template>
  <header class="nav-header">
    <div class="logo-title">
      <img :src="logo" class="logo-img" />
      <span class="system-title">声肺康智能分析</span>
    </div>
    <nav class="nav-menu-wrapper">
      <el-menu
        :default-active="activeRoute"
        class="nav-menu"
        mode="horizontal"
        router
      >
        <el-menu-item index="/home">主页</el-menu-item>
        <el-menu-item index="/dashboard">仪表盘</el-menu-item>
      </el-menu>
    </nav>
    <div class="nav-right">
      <el-dropdown @command="handleCommand">
        <el-button type="primary" plain>
          <el-icon><User /></el-icon>
          {{ userName || '未登录' }}
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="settings">个人设置</el-dropdown-item>
            <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User } from '@element-plus/icons-vue'
import logo from '../assets/logo.png'
import { useUserStore } from '../stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

// 计算当前激活的路由
const activeRoute = computed(() => route.path)

// 计算用户名
const userName = computed(() => {
  return userStore.userInfo?.username || ''
})

// 处理用户菜单命令
const handleCommand = (command) => {
  if (command === 'logout') {
    userStore.logout()
    ElMessage.success('已退出登录')
    router.push('/login')
  } else if (command === 'settings') {
    router.push('/settings')
  }
}
</script>

<style scoped>
.nav-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  padding: 0 48px;
  height: 72px;
  position: sticky;
  top: 0;
  z-index: 100;
  min-width: 0;
}

.logo-title {
  display: flex;
  align-items: center;
  flex-shrink: 0;
  min-width: 120px;
}

.logo-img {
  height: 44px;
  margin-right: 18px;
  transition: transform 0.3s;
}

.logo-img:hover {
  transform: scale(1.05);
}

.system-title {
  font-size: 24px;
  font-weight: bold;
  color: #2196f3;
  letter-spacing: 2px;
  background: linear-gradient(45deg, #2196f3, #64b5f6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  white-space: nowrap;
}

.nav-menu-wrapper {
  flex: 1 1 auto;
  min-width: 0;
  margin: 0 24px;
  overflow-x: auto;
}

.nav-menu {
  min-width: 0;
  background: transparent;
  border-bottom: none;
  height: 72px;
  line-height: 72px;
  white-space: nowrap;
}

.nav-menu :deep(.el-menu-item) {
  min-width: 80px !important;
  max-width: none !important;
  overflow: visible !important;
  text-overflow: unset !important;
  white-space: nowrap !important;
  display: inline-flex !important;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  padding: 0 24px;
  border-radius: 4px;
  transition: all 0.3s;
  height: 50px;
  line-height: 50px;
  margin: 0 4px;
}

.nav-menu :deep(.el-menu-item.is-active) {
  font-weight: bold;
  color: #2196f3;
  background-color: rgba(33, 150, 243, 0.1);
}

.nav-menu :deep(.el-menu-item:hover) {
  background-color: rgba(33, 150, 243, 0.05);
}

.nav-menu :deep(.el-menu--horizontal .el-menu-item:not(.is-disabled):focus) {
  color: #2196f3;
}

.nav-right {
  display: flex;
  align-items: center;
  gap: 24px;
  flex-shrink: 0;
  min-width: 120px;
}

:deep(.el-dropdown .el-button) {
  padding: 10px 18px;
  border-radius: 8px;
  font-weight: bold;
  transition: all 0.3s;
  border: 2px solid #2196f3;
  min-width: 80px;
  white-space: nowrap;
  overflow: visible;
  text-overflow: unset;
  max-width: none;
}

:deep(.el-dropdown .el-button span),
:deep(.el-dropdown .el-button .el-icon) {
  min-width: 0 !important;
  max-width: none !important;
  overflow: visible !important;
  text-overflow: unset !important;
  white-space: nowrap !important;
}

:deep(.el-dropdown .el-button:hover) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(33, 150, 243, 0.2);
}

@media (max-width: 768px) {
  .nav-header {
    padding: 0 16px;
  }
  .system-title {
    font-size: 20px;
  }
  .nav-menu-wrapper {
    margin: 0 12px;
  }
  .nav-menu :deep(.el-menu-item) {
    padding: 0 12px;
    min-width: 80px;
  }
  :deep(.el-dropdown .el-button) {
    font-size: 14px;
    padding: 8px 10px;
    min-width: 60px;
  }
}
</style>

<style>
:root {
  /* 保证全局字体和背景 */
}
:deep(.el-dropdown .el-button),
:deep(.el-dropdown .el-button span),
:deep(.el-dropdown .el-button .el-icon),
:deep(.el-menu),
:deep(.el-menu--horizontal),
:deep(.el-menu-item) {
  min-width: 0 !important;
  max-width: none !important;
  overflow: visible !important;
  text-overflow: unset !important;
  white-space: nowrap !important;
}
</style> 