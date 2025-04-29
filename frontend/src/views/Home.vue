<template>
  <div class="home-container">
    <el-container>
      <el-header>
        <div class="header-content">
          <h2>声肺康系统</h2>
          <el-button type="danger" @click="handleLogout">退出登录</el-button>
        </div>
      </el-header>
      <el-main>
        <el-card>
          <h3>欢迎使用声肺康系统</h3>
          <p>您已成功登录系统</p>
        </el-card>
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { ElMessage } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()

const handleLogout = () => {
  userStore.logout()
  ElMessage.success('已退出登录')
  router.push('/login')
}
</script>

<style scoped>
.home-container {
  min-height: 100vh;
  background-color: #f5f5f5;
}

.el-header {
  background-color: #fff;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  padding: 0 20px;
}

.header-content {
  height: 60px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-content h2 {
  margin: 0;
  color: #409EFF;
}

.el-main {
  padding: 20px;
}

.el-card {
  text-align: center;
  padding: 20px;
}

.el-card h3 {
  color: #409EFF;
  margin-bottom: 15px;
}
</style> 