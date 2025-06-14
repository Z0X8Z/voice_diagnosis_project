import axios from 'axios'

export function useApi() {
  const api = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
    timeout: 10000,
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
      }
      return config
    },
    error => {
      return Promise.reject(error)
    }
  )
  
  // 响应拦截器
  api.interceptors.response.use(
    response => response,
    error => {
      if (error.response) {
        switch (error.response.status) {
          case 401:
            // 未授权，清除token并跳转到登录页
            localStorage.removeItem('token')
            window.location.href = '/login'
            break
          case 403:
            // 权限不足
            console.error('权限不足')
            break
          case 404:
            // 资源不存在
            console.error('请求的资源不存在')
            break
          case 500:
            // 服务器错误
            console.error('服务器错误')
            break
          default:
            console.error('请求失败:', error.response.data)
        }
      } else if (error.request) {
        // 请求已发出但没有收到响应
        console.error('网络错误，请检查网络连接')
      } else {
        // 请求配置出错
        console.error('请求配置错误:', error.message)
      }
      return Promise.reject(error)
    }
  )
  
  return api
} 