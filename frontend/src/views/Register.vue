<template>
  <div class="register-container">
    <el-card class="register-card">
      <h2>注册</h2>
      <el-form :model="registerForm" :rules="rules" ref="registerFormRef">
        <el-form-item prop="username">
          <el-input 
            v-model="registerForm.username"
            placeholder="用户名"
            prefix-icon="User"
          />
        </el-form-item>
        <el-form-item prop="email">
          <el-input 
            v-model="registerForm.email"
            placeholder="邮箱"
            prefix-icon="Message"
          />
        </el-form-item>
        <el-form-item prop="password">
          <el-input 
            v-model="registerForm.password"
            type="password"
            placeholder="密码"
            prefix-icon="Lock"
            show-password
          />
        </el-form-item>
        <el-form-item prop="confirmPassword">
          <el-input 
            v-model="registerForm.confirmPassword"
            type="password"
            placeholder="确认密码"
            prefix-icon="Lock"
            show-password
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleRegister" :loading="loading" class="submit-btn">
            注册
          </el-button>
        </el-form-item>
        
        <!-- 错误信息展示 -->
        <el-alert
          v-if="errorMessage"
          :title="errorMessage"
          type="error"
          show-icon
          :closable="true"
          @close="clearError"
        />
        
        <div class="login-link">
          已有账号？
          <router-link to="/login">立即登录</router-link>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { ElMessage } from 'element-plus'
import { User, Lock, Message } from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()
const registerFormRef = ref(null)
const loading = ref(false)

// 计算属性：获取用户状态中的错误信息
const errorMessage = computed(() => {
  if (!userStore.lastError) return ''
  
  // 如果服务器返回了详细错误信息
  if (userStore.lastError.data && userStore.lastError.data.detail) {
    return userStore.lastError.data.detail
  }
  
  // 如果有HTTP状态错误
  if (userStore.lastError.status) {
    return `错误 ${userStore.lastError.status}: ${userStore.lastError.statusText || '请求失败'}`
  }
  
  // 其他错误
  return userStore.lastError.message || '注册失败，请稍后重试'
})

// 清除错误信息
const clearError = () => {
  userStore.clearError()
}

const registerForm = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

const validatePass2 = (rule, value, callback) => {
  if (value === '') {
    callback(new Error('请再次输入密码'))
  } else if (value !== registerForm.password) {
    callback(new Error('两次输入密码不一致!'))
  } else {
    callback()
  }
}

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '长度在 6 到 20 个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    { validator: validatePass2, trigger: 'blur' }
  ]
}

const handleRegister = async () => {
  if (!registerFormRef.value) return
  
  // 先清除可能存在的错误信息
  clearError()
  
  await registerFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        const success = await userStore.register(
          registerForm.username,
          registerForm.email,
          registerForm.password
        )
        if (success) {
          ElMessage.success('注册成功')
          router.push('/login')
        } 
        // 错误信息现在从 errorMessage 计算属性获取并显示
      } finally {
        loading.value = false
      }
    }
  })
}
</script>

<style scoped>
.register-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #e0f7fa 0%, #b2ebf2 100%);
}

.register-card {
  width: 400px;
  padding: 32px 28px 24px 28px;
  border-radius: 22px;
  box-shadow: 0 4px 32px #b3e5fc55;
  background: #fff;
}

.register-card h2 {
  text-align: center;
  margin-bottom: 30px;
  color: #2196f3;
  font-size: 26px;
  font-weight: bold;
  letter-spacing: 2px;
}

.el-form-item {
  margin-bottom: 24px;
}

.el-input {
  border-radius: 12px;
  box-shadow: 0 1px 4px #b3e5fc22;
  font-size: 16px;
}

.el-input:focus-within {
  box-shadow: 0 0 0 2px #2196f3aa;
}

.submit-btn {
  width: 100%;
  border-radius: 16px;
  background: linear-gradient(90deg, #2196f3 60%, #64b5f6 100%);
  font-size: 18px;
  font-weight: bold;
  letter-spacing: 1px;
  transition: background 0.2s, box-shadow 0.2s;
}
.submit-btn:hover {
  background: linear-gradient(90deg, #1976d2 60%, #64b5f6 100%);
  box-shadow: 0 4px 16px #2196f355;
}

.el-alert {
  margin-bottom: 18px;
  border-radius: 12px;
  font-size: 15px;
}

.login-link {
  text-align: center;
  margin-top: 18px;
  font-size: 15px;
  color: #888;
}

.login-link a {
  color: #2196f3;
  text-decoration: none;
  font-weight: bold;
  margin-left: 4px;
  transition: color 0.2s;
}
.login-link a:hover {
  color: #1976d2;
}

@media (max-width: 600px) {
  .register-card {
    width: 98vw;
    min-width: 0;
    padding: 16px 4px;
  }
}
</style> 