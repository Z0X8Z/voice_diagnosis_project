import { defineStore } from 'pinia'
import axios from 'axios'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    userInfo: null
  }),
  
  actions: {
    async login(username, password) {
      try {
        const response = await axios.post('http://localhost:8000/api/v1/auth/login', {
          username,
          password
        })
        const { access_token } = response.data
        this.token = access_token
        localStorage.setItem('token', access_token)
        return true
      } catch (error) {
        console.error('登录失败:', error)
        return false
      }
    },

    async register(username, email, password) {
      try {
        const response = await axios.post('http://localhost:8000/api/v1/auth/register', {
          username,
          email,
          password
        })
        return true
      } catch (error) {
        console.error('注册失败:', error)
        return false
      }
    },

    logout() {
      this.token = ''
      this.userInfo = null
      localStorage.removeItem('token')
    }
  }
}) 