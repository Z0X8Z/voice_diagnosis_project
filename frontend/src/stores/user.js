import { defineStore } from 'pinia'
import axios from 'axios'

// 创建axios实例
const api = axios.create({
  baseURL: '/api/v1',  // 使用相对路径，让Vite代理处理
  timeout: 10000,      // 请求超时时间
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
      console.log('发送请求，使用token:', token) // 调试信息
    } else {
      console.log('发送请求，无token') // 调试信息
    }
    return config
  },
  error => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => response,
  error => {
    if (!error.response) {
      // 网络错误
      console.error('网络错误:', error.message)
      return Promise.reject({
        message: '网络连接失败，请检查网络设置'
      })
    }
    
    // 处理401错误
    if (error.response.status === 401) {
      console.error('认证失败:', error.response.data)
      // 清除无效的token
      localStorage.removeItem('token')
    }
    
    return Promise.reject(error)
  }
)

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    userInfo: null,
    lastError: null,
    latestKpi: null,
    latestLlmSuggestion: null
  }),
  
  getters: {
    isLoggedIn: (state) => !!state.token
  },
  
  actions: {
    async login(username, password) {
      try {
        console.log('尝试登录:', username) // 调试信息
        
        // 使用表单数据格式，与FastAPI的OAuth2PasswordRequestForm兼容
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);
        
        const response = await api.post('/auth/login', 
          formData,
          {
            headers: {
              'Content-Type': 'application/x-www-form-urlencoded'
            }
          }
        )
        
        console.log('登录响应:', response.data) // 调试信息
        
        const { access_token, refresh_token } = response.data
        if (!access_token) {
          throw new Error('服务器未返回token')
        }
        
        this.token = access_token
        localStorage.setItem('token', access_token)
        if (refresh_token) {
          localStorage.setItem('refresh_token', refresh_token)
        }
        
        // 登录成功后立即获取用户信息
        await this.fetchUserInfo()
        
        return true
      } catch (error) {
        console.error('登录失败:', error.response?.data || error.message) // 调试信息
        this.lastError = {
          status: error.response?.status,
          statusText: error.response?.statusText,
          data: error.response?.data,
          message: error.message || '登录失败，请稍后重试'
        }
        return false
      }
    },

    async register(username, email, password) {
      try {
        const response = await api.post('/auth/register', 
          {
            username,
            email,
            password
          }
        )
        return true
      } catch (error) {
        this.lastError = {
          status: error.response?.status,
          statusText: error.response?.statusText,
          data: error.response?.data,
          message: error.message || '注册失败，请稍后重试'
        }
        return false
      }
    },

    logout() {
      this.token = ''
      this.userInfo = null
      localStorage.removeItem('token')
      localStorage.removeItem('refresh_token')
    },
    
    clearError() {
      this.lastError = null
    },

    setLatestKpi(kpi) {
      this.latestKpi = kpi
    },

    setLatestLlmSuggestion(suggestion) {
      this.latestLlmSuggestion = suggestion
    },

    clearLatestDetection() {
      this.latestKpi = null
      this.latestLlmSuggestion = null
    },

    async refreshToken() {
      try {
        const refresh_token = localStorage.getItem('refresh_token')
        if (!refresh_token) throw new Error('无refresh_token')
        const response = await axios.post('/api/v1/auth/refresh', { refresh_token })
        const { access_token } = response.data
        if (!access_token) throw new Error('服务器未返回新token')
        this.token = access_token
        localStorage.setItem('token', access_token)
        return access_token
      } catch (error) {
        this.logout()
        throw error
      }
    },

    async fetchUserInfo() {
      try {
        console.log('获取用户信息...')
        const response = await api.get('/users/me')
        console.log('用户信息响应:', response.data)
        this.userInfo = response.data
        return response.data
      } catch (error) {
        console.error('获取用户信息失败:', error.response?.data || error.message)
        if (error.response?.status === 401) {
          // Token可能已过期，尝试刷新
          try {
            await this.refreshToken()
            // 刷新成功后重试
            const retryResponse = await api.get('/users/me')
            this.userInfo = retryResponse.data
            return retryResponse.data
          } catch (refreshError) {
            console.error('刷新token失败:', refreshError)
            this.logout()
          }
        }
        return null
      }
    }
  }
}) 