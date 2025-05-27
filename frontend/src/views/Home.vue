<template>
  <div class="home-container">
    <!-- 顶部导航栏 -->
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
    <!-- 主要内容区域 -->
    <div class="main-content">
      <el-card class="upload-card">
        <template #header>
          <div class="card-header">
            <el-icon class="upload-main-icon"><Microphone /></el-icon>
            <h2>语音智能分析</h2>
          </div>
        </template>
        <div class="record-area">
          <div class="record-tips">
            <b>录音建议：</b>
            <ul>
              <li>关闭风扇、空调等噪音源</li>
              <li>距离麦克风10cm以内</li>
              <li>正对麦克风</li>
              <li>保持安静环境</li>
            </ul>
          </div>
          <canvas ref="waveformCanvas" class="waveform-canvas"></canvas>
          <div class="volume-feedback" :class="volumeLevelClass">{{ volumeFeedback }}</div>
          <button
            class="record-btn"
            :class="{ recording: isRecording }"
            @click="toggleRecording"
          >
            <el-icon><Microphone /></el-icon>
          </button>
          <div class="record-tip">
            {{ isRecording ? '录音中...点击停止' : '点击录音' }}
          </div>
        </div>

        <!-- 上传状态和结果 -->
        <div v-if="uploadStatus" class="upload-status">
          <el-alert
            :title="uploadStatus.message"
            :type="uploadStatus.type"
            :closable="false"
            show-icon
          />
        </div>

        <!-- 分析结果 -->
        <div v-if="analysisResult" class="analysis-result">
          <h3>分析结果</h3>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="预测结果">
              {{ analysisResult.prediction }}
            </el-descriptions-item>
            <el-descriptions-item label="置信度">
              {{ (analysisResult.confidence * 100).toFixed(2) }}%
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Microphone, User } from '@element-plus/icons-vue'
import logo from '../assets/logo.png'
import { useUserStore } from '../stores/user'
import axios from 'axios'

const route = useRoute()
const router = useRouter()
const uploadStatus = ref(null)
const analysisResult = ref(null)
const isRecording = ref(false)
let mediaRecorder = null
let audioChunks = []
let audioContext = null
let analyser = null
let source = null
let animationId = null
const waveformCanvas = ref(null)
const volumeFeedback = ref('音量正常')
const volumeLevelClass = ref('normal')
const userStore = useUserStore()

const activeIndex = computed(() => route.path)

const drawWaveform = () => {
  if (!analyser || !waveformCanvas.value) return
  const canvas = waveformCanvas.value
  const ctx = canvas.getContext('2d')
  const bufferLength = analyser.fftSize
  const dataArray = new Uint8Array(bufferLength)
  analyser.getByteTimeDomainData(dataArray)
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  ctx.beginPath()
  let sum = 0
  for (let i = 0; i < bufferLength; i++) {
    const v = dataArray[i] / 128.0
    const y = (v * canvas.height) / 2
    if (i === 0) {
      ctx.moveTo(i, y)
    } else {
      ctx.lineTo(i, y)
    }
    sum += Math.abs(v - 1)
  }
  ctx.strokeStyle = '#2196f3'
  ctx.lineWidth = 2
  ctx.stroke()
  // 音量反馈
  const avg = sum / bufferLength
  if (avg < 0.05) {
    volumeFeedback.value = '声音太小'
    volumeLevelClass.value = 'low'
  } else if (avg > 0.35) {
    volumeFeedback.value = '声音太大'
    volumeLevelClass.value = 'high'
  } else {
    volumeFeedback.value = '音量正常'
    volumeLevelClass.value = 'normal'
  }
  animationId = requestAnimationFrame(drawWaveform)
}

const startVisualizer = (stream) => {
  audioContext = new (window.AudioContext || window.webkitAudioContext)()
  source = audioContext.createMediaStreamSource(stream)
  analyser = audioContext.createAnalyser()
  analyser.fftSize = 512
  source.connect(analyser)
  drawWaveform()
}

const stopVisualizer = () => {
  if (animationId) cancelAnimationFrame(animationId)
  if (audioContext) audioContext.close()
  audioContext = null
  analyser = null
  source = null
}

const toggleRecording = async () => {
  if (!isRecording.value) {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          noiseSuppression: true,
          echoCancellation: true,
          autoGainControl: true
        }
      })
      mediaRecorder = new window.MediaRecorder(stream)
      audioChunks = []
      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunks.push(e.data)
      }
      mediaRecorder.onstop = () => {
        stopVisualizer()
        uploadAudio()
      }
      mediaRecorder.start()
      isRecording.value = true
      startVisualizer(stream)
    } catch (err) {
      ElMessage.error('无法获取麦克风权限')
    }
  } else {
    if (mediaRecorder) {
      mediaRecorder.stop()
      isRecording.value = false
    }
  }
}

const uploadAudio = async () => {
  const audioBlob = new Blob(audioChunks, { type: 'audio/webm' })
  const formData = new FormData()
  const timestamp = new Date().getTime()
  formData.append('file', audioBlob, `voice_${timestamp}.webm`)
  
  // 检查token是否存在
  if (!userStore.token) {
    console.error('Token不存在，请先登录')
    uploadStatus.value = { type: 'error', message: '请先登录' }
    router.push('/login')
    return
  }
  
  try {
    uploadStatus.value = { type: 'info', message: '正在上传录音...' }
    console.log('使用的token:', userStore.token) // 调试信息
    const response = await fetch('/api/v1/diagnosis/upload', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${userStore.token}`
      },
      body: formData
    })
    if (!response.ok) {
      const errorData = await response.json()
      console.error('上传错误详情:', errorData)
      throw new Error(errorData.detail || '上传失败')
    }
    const result = await response.json()
    uploadStatus.value = { type: 'success', message: '上传成功' }
    analysisResult.value = result.result
    userStore.setLatestKpi(result.result)
    // 跳转到dashboard页面
    setTimeout(() => {
      window.location.href = '/dashboard'
    }, 800)
  } catch (error) {
    console.error('上传错误:', error)
    uploadStatus.value = { type: 'error', message: `上传失败: ${error.message}` }
    analysisResult.value = null
  }
}

const uploadFile = async (file) => {
  try {
    const token = userStore.token
    if (!token) {
      console.error('Token is missing')
      ElMessage.error('请先登录')
      return
    }

    // 验证 token 格式
    if (!token.startsWith('Bearer ')) {
      console.error('Invalid token format:', token)
      ElMessage.error('认证信息无效')
      return
    }

    console.log('Uploading file with token:', token)
    const formData = new FormData()
    formData.append('file', file)

    const response = await axios.post(
      `${import.meta.env.VITE_API_BASE_URL}/api/v1/diagnosis/upload`,
      formData,
      {
        headers: {
          'Authorization': token
        }
      }
    )

    if (response.data) {
      console.log('Upload response:', response.data)
      ElMessage.success('文件上传成功')
      // 处理上传成功后的逻辑
    }
  } catch (error) {
    console.error('Upload error:', error)
    if (error.response) {
      console.error('Error response:', error.response.data)
      if (error.response.status === 401) {
        ElMessage.error('认证失败，请重新登录')
        userStore.logout()
        router.push('/login')
      } else {
        ElMessage.error(error.response.data.detail || '上传失败')
      }
    } else {
      ElMessage.error('上传失败，请检查网络连接')
    }
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

onMounted(() => {
  if (waveformCanvas.value) {
    waveformCanvas.value.width = 400
    waveformCanvas.value.height = 80
  }
})
onBeforeUnmount(() => {
  stopVisualizer()
})
</script>

<style scoped>
.home-container {
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

.nav-right {
  display: flex;
  align-items: center;
  gap: 20px;
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
  max-width: 500px;
  margin: 0 auto;
}

.upload-card {
  margin: 60px auto 0;
  max-width: 500px;
  border-radius: 18px;
  box-shadow: 0 4px 24px #b3e5fc55;
  background: #fff;
}

.card-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.upload-main-icon {
  font-size: 48px;
  color: #2196f3;
}

.record-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin: 40px 0 20px 0;
}

.record-tips {
  font-size: 15px;
  color: #333;
  margin-bottom: 10px;
  background: #fffbe6;
  border-radius: 8px;
  padding: 10px 18px;
  box-shadow: 0 2px 8px #ffe08255;
}

.record-tips ul {
  margin: 0 0 0 18px;
  padding: 0;
}

.waveform-canvas {
  width: 400px;
  height: 80px;
  background: #e3f2fd;
  border-radius: 8px;
  margin-bottom: 10px;
}

.volume-feedback {
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 10px;
}

.volume-feedback.low { color: #e53935; }
.volume-feedback.high { color: #e53935; }
.volume-feedback.normal { color: #43a047; }

.record-btn {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  background: #ff3b3b;
  color: #fff;
  border: none;
  outline: none;
  font-size: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 24px #ffb3b3aa;
  cursor: pointer;
  transition: background 0.2s, box-shadow 0.2s;
}

.record-btn.recording {
  background: #b71c1c;
  box-shadow: 0 0 0 8px #ffb3b355;
}

.record-tip {
  margin-top: 18px;
  font-size: 18px;
  color: #b71c1c;
  font-weight: bold;
}

.upload-status {
  margin-top: 20px;
}

.analysis-result {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}

.analysis-result h3 {
  margin-bottom: 16px;
  color: #303133;
}
</style> 