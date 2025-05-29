<template>
  <div class="home-container">
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
import { Microphone } from '@element-plus/icons-vue'
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
  // 上传新语音前，清除仪表盘本地存储
  localStorage.removeItem('voice_analysis_conversation');
  const audioBlob = new Blob(audioChunks, { type: 'audio/webm' })
  const formData = new FormData()
  const timestamp = new Date().getTime()
  formData.append('file', audioBlob, `voice_${timestamp}.webm`)
  // 存储首轮分析请求内容到 localStorage
  localStorage.setItem('initialLLMMessage', JSON.stringify({
    role: 'user',
    content: '请分析我的语音健康' // 你可以根据实际业务动态生成
  }))
  
  // 检查token是否存在
  if (!userStore.token) {
    console.error('Token不存在，请先登录')
    uploadStatus.value = { type: 'error', message: '请先登录' }
    router.push('/login')
    return
  }
  
  let triedRefresh = false
  while (true) {
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
      if (response.status === 401 && !triedRefresh) {
        // token过期，尝试刷新
        try {
          await userStore.refreshToken()
          triedRefresh = true
          continue // 重试上传
        } catch (e) {
          uploadStatus.value = { type: 'error', message: '登录已过期，请重新登录' }
          router.push('/login')
          return
        }
      }
      if (!response.ok) {
        const errorData = await response.json()
        console.error('上传错误详情:', errorData)
        throw new Error(errorData.detail || '上传失败')
      }
      const result = await response.json()
      uploadStatus.value = { type: 'success', message: '上传成功' }
      analysisResult.value = result.result
      userStore.setLatestKpi(result.result)
      
      // 保存首轮对话内容到localStorage，以便在仪表盘页面恢复
      if (result.llm_prompt) {
        try {
          localStorage.setItem('initialLLMMessage', JSON.stringify({
            role: 'user',
            content: result.llm_prompt
          }))
          console.log('已保存首轮对话内容到localStorage')
        } catch (e) {
          console.error('保存首轮对话内容失败:', e)
        }
      }
      
      // 跳转到dashboard页面
      setTimeout(() => {
        router.push({ path: '/dashboard', query: { fromUpload: 1 } })
      }, 800)
      break
    } catch (error) {
      if (error.message === '登录已过期，请重新登录') return
      console.error('上传错误:', error)
      uploadStatus.value = { type: 'error', message: `上传失败: ${error.message}` }
      analysisResult.value = null
      break
    }
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

.main-content {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding: 60px 20px 20px;
  min-height: 80vh;
}

.upload-card {
  width: 480px;
  border-radius: 22px;
  box-shadow: 0 4px 32px #b3e5fc55;
  background: #fff;
  padding: 32px 24px 24px 24px;
  margin-top: 32px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 20px;
  font-weight: bold;
  color: #2196f3;
}

.upload-main-icon {
  font-size: 32px;
  color: #2196f3;
}

.record-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin: 32px 0 24px 0;
}

.record-tips {
  background: #f5f7fa;
  border-radius: 12px;
  padding: 12px 18px;
  margin-bottom: 18px;
  font-size: 15px;
  color: #666;
  box-shadow: 0 2px 8px #e0e0e055;
}

.waveform-canvas {
  width: 320px;
  height: 60px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 12px #b3e5fc33;
  margin: 18px 0 10px 0;
  display: block;
}

.volume-feedback {
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 10px;
  padding: 4px 18px;
  border-radius: 16px;
  background: #e3f2fd;
  color: #2196f3;
  box-shadow: 0 1px 4px #b3e5fc33;
  transition: background 0.3s, color 0.3s;
}

.volume-feedback.low {
  background: #fff3e0;
  color: #ff9800;
}

.volume-feedback.high {
  background: #ffebee;
  color: #e53935;
}

.record-btn {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: linear-gradient(135deg, #2196f3 60%, #64b5f6 100%);
  border: none;
  color: #fff;
  font-size: 32px;
  box-shadow: 0 4px 16px #2196f355;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  margin-bottom: 8px;
  transition: box-shadow 0.2s, background 0.2s, transform 0.2s;
}

.record-btn:hover {
  box-shadow: 0 8px 32px #2196f399;
  background: linear-gradient(135deg, #1976d2 60%, #64b5f6 100%);
  transform: scale(1.07);
}

.record-btn.recording {
  background: linear-gradient(135deg, #e53935 60%, #ffb300 100%);
  animation: pulse 1.2s infinite;
}

@keyframes pulse {
  0% { box-shadow: 0 0 0 0 #e5393533; }
  70% { box-shadow: 0 0 0 16px #e5393500; }
  100% { box-shadow: 0 0 0 0 #e5393500; }
}

.record-tip {
  font-size: 15px;
  color: #2196f3;
  margin-bottom: 8px;
  font-weight: 500;
}

.upload-status {
  margin: 18px 0 0 0;
}

.analysis-result {
  margin-top: 28px;
  background: #f5f7fa;
  border-radius: 14px;
  box-shadow: 0 2px 8px #b3e5fc33;
  padding: 18px 20px;
}

.analysis-result h3 {
  color: #2196f3;
  font-size: 18px;
  margin-bottom: 12px;
}

@media (max-width: 600px) {
  .main-content {
    padding: 20px 4px;
  }
  .upload-card {
    width: 100%;
    min-width: 0;
    padding: 16px 4px;
  }
  .waveform-canvas {
    width: 98vw;
    min-width: 0;
  }
}
</style> 