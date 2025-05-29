<template>
  <div class="settings-container">
    <div class="main-content">
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
            <el-button type="primary" @click="saveUserSettings" :loading="loading">
              保存设置
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../stores/user'
import { useApi } from '../composables/useApi'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const api = useApi()
const userFormRef = ref(null)
const loading = ref(false)

const userForm = ref({
  username: '',
  email: '',
  newPassword: '',
  confirmPassword: ''
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
        if (value && value !== userForm.value.newPassword) {
          callback(new Error('两次输入密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// 页面加载时获取用户信息
onMounted(async () => {
  try {
    // 如果store中已有用户信息，直接使用
    if (userStore.userInfo) {
      userForm.value.username = userStore.userInfo.username || ''
      userForm.value.email = userStore.userInfo.email || ''
    } else {
      // 否则重新获取用户信息
      const userData = await userStore.fetchUserInfo()
      if (userData) {
        userForm.value.username = userData.username || ''
        userForm.value.email = userData.email || ''
      }
    }
  } catch (error) {
    ElMessage.error('获取用户信息失败')
  }
})

const saveUserSettings = async () => {
  if (!userFormRef.value) return

  // 新增：前端主动校验密码输入
  if (userForm.value.newPassword) {
    // 如果输入了新密码，必须同时输入确认密码
    if (!userForm.value.confirmPassword) {
      ElMessage.error('请输入确认密码')
      return
    }
    // 两次密码必须一致
    if (userForm.value.newPassword !== userForm.value.confirmPassword) {
      ElMessage.error('两次输入的密码不一致')
      return
    }
  }

  try {
    // 表单验证
    await userFormRef.value.validate()
    
    loading.value = true
    
    // 构建更新数据对象
    const updateData = {
      username: userForm.value.username,
      email: userForm.value.email
    }
    
    // 如果有输入新密码，则包含密码更新
    if (userForm.value.newPassword) {
      updateData.password = userForm.value.newPassword
    }
    
    console.log('[DEBUG] updateData:', updateData)
    
    // 调用API更新用户信息
    const response = await api.put('/users/me', updateData)
    console.log('[DEBUG] API响应:', response)
    
    // 检查是否修改了密码
    if (updateData.password) {
      // 清除本地token
      localStorage.removeItem('token')
      // 调用 userStore 的登出方法（如果有）
      if (userStore.logout) {
        userStore.logout()
      } else {
        userStore.isLoggedIn = false
        userStore.userInfo = null
      }
      // 跳转到登录页
      ElMessage.success('密码修改成功，请重新登录')
      router.push({ name: 'Login' })
      return
    }

    // 更新本地存储的用户信息
    await userStore.fetchUserInfo()
    
    // 清空密码字段
    userForm.value.newPassword = ''
    userForm.value.confirmPassword = ''
    
    ElMessage.success('用户设置已保存')
  } catch (error) {
    console.error('[DEBUG] 保存设置失败:', error)
    if (error.config) {
      console.error('[DEBUG] 请求体:', error.config.data)
    }
    if (error.response) {
      console.error('[DEBUG] 响应内容:', error.response)
    }
    // 优化超时错误提示
    if (error.code === 'ECONNABORTED') {
      ElMessage.error('保存设置超时，可能是网络问题或服务器繁忙，请稍后重试')
    } else if (error.response?.data?.detail) {
      if (Array.isArray(error.response.data.detail)) {
        // FastAPI/Pydantic风格的字段错误
        const msg = error.response.data.detail.map(e => {
          if (e.loc && e.msg) {
            return `${e.loc.join('.')}: ${e.msg}`
          } else if (typeof e === 'string') {
            return e
          } else {
            return JSON.stringify(e)
          }
        }).join('\n')
        ElMessage.error(msg)
      } else if (typeof error.response.data.detail === 'string') {
        ElMessage.error(error.response.data.detail)
      } else {
        ElMessage.error(JSON.stringify(error.response.data.detail))
      }
    } else {
      ElMessage.error('保存设置失败')
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.settings-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #e0f7fa 0%, #b2ebf2 100%);
}

.main-content {
  padding: 80px 20px 20px;
  max-width: 600px;
  margin: 0 auto;
  display: flex;
  justify-content: center;
  align-items: flex-start;
}

.settings-card {
  width: 100%;
  border-radius: 22px;
  box-shadow: 0 4px 32px #b3e5fc55;
  background: #fff;
  padding: 32px 24px 24px 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 18px;
  font-weight: bold;
  color: #2196f3;
}

.el-form {
  margin-top: 18px;
}

.el-form-item {
  margin-bottom: 28px;
}
</style>