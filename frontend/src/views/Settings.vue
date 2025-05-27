<template>
  <div class="settings-container">
    <header class="nav-header">
      <div class="logo-title">
        <img :src="logo" class="logo-img" />
        <span class="system-title">声肺康智能分析</span>
      </div>
      <div class="nav-right">
      <el-menu
        :default-active="activeIndex"
        class="nav-menu"
        mode="horizontal"
        router
      >
        <el-menu-item index="/home">主页</el-menu-item>
        <el-menu-item index="/dashboard">仪表盘</el-menu-item>
        <el-menu-item index="/settings">设置</el-menu-item>
      </el-menu>
        <el-dropdown @command="handleCommand">
          <el-button type="primary" plain>
            <el-icon><User /></el-icon>
            用户菜单
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile">个人信息</el-dropdown-item>
              <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </header>
    <div class="main-content">
      <el-row :gutter="20">
        <el-col :span="12">
          <el-card class="settings-card">
            <template #header>
              <div class="card-header">
                <span>用户设置</span>
              </div>
            </template>
            <el-form
              ref="userFormRef"
              :model="userForm"
              :rules="userRules"
              label-width="100px"
            >
              <el-form-item label="用户名" prop="username">
                <el-input v-model="userForm.username" />
              </el-form-item>
              <el-form-item label="邮箱" prop="email">
                <el-input v-model="userForm.email" />
              </el-form-item>
              <el-form-item label="修改密码" prop="newPassword">
                <el-input
                  v-model="userForm.newPassword"
                  type="password"
                  show-password
                  placeholder="输入新密码"
                />
              </el-form-item>
              <el-form-item label="确认密码" prop="confirmPassword">
                <el-input
                  v-model="userForm.confirmPassword"
                  type="password"
                  show-password
                  placeholder="再次输入新密码"
                />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="saveUserSettings">
                  保存设置
                </el-button>
              </el-form-item>
            </el-form>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card class="settings-card">
            <template #header>
              <div class="card-header">
                <span>系统设置</span>
              </div>
            </template>
            <el-form
              ref="systemFormRef"
              :model="systemForm"
              label-width="120px"
            >
              <el-form-item label="自动保存分析结果">
                <el-switch v-model="systemForm.autoSave" />
              </el-form-item>
              <el-form-item label="分析结果通知">
                <el-switch v-model="systemForm.notifications" />
              </el-form-item>
              <el-form-item label="主题">
                <el-select v-model="systemForm.theme">
                  <el-option label="浅色" value="light" />
                  <el-option label="深色" value="dark" />
                </el-select>
              </el-form-item>
              <el-form-item label="语言">
                <el-select v-model="systemForm.language">
                  <el-option label="简体中文" value="zh-CN" />
                  <el-option label="English" value="en-US" />
                </el-select>
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="saveSystemSettings">
                  保存设置
                </el-button>
              </el-form-item>
            </el-form>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User } from '@element-plus/icons-vue'
import logo from '../assets/logo.png'
import { useUserStore } from '../stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const userFormRef = ref(null)
const systemFormRef = ref(null)
const activeIndex = computed(() => route.path)
const userForm = ref({
  username: '',
  email: '',
  newPassword: '',
  confirmPassword: ''
})
const systemForm = ref({
  autoSave: true,
  notifications: true,
  theme: 'light',
  language: 'zh-CN'
})
const userRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ],
  newPassword: [
    { min: 6, message: '密码长度不能小于 6 个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    {
      validator: (rule, value, callback) => {
        if (value !== userForm.value.newPassword) {
          callback(new Error('两次输入密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}
const saveUserSettings = async () => {
  if (!userFormRef.value) return
  try {
    await userFormRef.value.validate()
    ElMessage.success('用户设置已保存')
  } catch (error) {
    ElMessage.error('表单验证失败')
  }
}
const saveSystemSettings = async () => {
  try {
    ElMessage.success('系统设置已保存')
  } catch (error) {
    ElMessage.error('保存设置失败')
  }
}
const handleCommand = (command) => {
  if (command === 'logout') {
    userStore.logout()
    ElMessage.success('已退出登录')
    router.push('/login')
  } else if (command === 'profile') {
    router.push('/settings')
  }
}
</script>

<style scoped>
.settings-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #e0f7fa 0%, #b2ebf2 100%);
}
.nav-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  box-shadow: 0 2px 8px #e0e0e0;
  padding: 0 40px;
  height: 64px;
}
.logo-title {
  display: flex;
  align-items: center;
}
.logo-img {
  height: 40px;
  margin-right: 16px;
}
.system-title {
  font-size: 22px;
  font-weight: bold;
  color: #2196f3;
  letter-spacing: 2px;
}
.nav-menu {
  background: transparent;
  border-bottom: none;
}
.main-content {
  padding: 80px 20px 20px;
  max-width: 1200px;
  margin: 0 auto;
}
.settings-card {
  margin-bottom: 20px;
  border-radius: 18px;
  box-shadow: 0 4px 24px #b3e5fc55;
  background: #fff;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.card-header span {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
}
</style> 