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
            <div class="mic-test-tip">
              <el-icon><Warning /></el-icon>
              <span>首次使用建议先进行</span>
              <el-button text type="primary" @click="goToMicTest" class="mic-test-link">
                麦克风质量测试
              </el-button>
            </div>
          </div>
          
          <!-- 录音区域 -->
          <canvas ref="waveformCanvas" class="waveform-canvas"></canvas>
          <div class="volume-feedback" :class="volumeLevelClass">{{ volumeFeedback }}</div>
          
          <!-- 录音按钮 -->
          <button
            class="record-btn"
            :class="{ 
              recording: isRecording, 
              success: lastAudioQuality && lastAudioQuality.is_acceptable,
              checking: isCheckingQuality 
            }"
            @click="toggleRecording"
            :disabled="isCheckingQuality || isUploading"
          >
            <el-icon v-if="isCheckingQuality"><Loading /></el-icon>
            <el-icon v-else-if="lastAudioQuality && lastAudioQuality.is_acceptable"><Check /></el-icon>
            <el-icon v-else><Microphone /></el-icon>
          </button>
          
          <div class="record-tip">
            <span v-if="isRecording">录音中...点击停止</span>
            <span v-else-if="isCheckingQuality">正在检测音频质量...</span>
            <span v-else-if="isUploading">正在上传分析...</span>
            <span v-else-if="lastAudioQuality && lastAudioQuality.is_acceptable">音频质量良好！点击上传分析</span>
            <span v-else-if="recordAttempts > 0">音频质量需要改善，请重新录音</span>
            <span v-else>点击录音</span>
          </div>

          <!-- 录音尝试次数显示 -->
          <div v-if="recordAttempts > 0" class="attempt-info">
            <el-tag type="info" size="small">已录音 {{ recordAttempts }} 次</el-tag>
          </div>

          <!-- 音频质量反馈 -->
          <div v-if="lastAudioQuality" class="audio-quality-feedback">
            <div class="quality-header">
              <el-progress
                type="circle"
                :percentage="lastAudioQuality.quality_score"
                :color="getQualityColor(lastAudioQuality.quality_score)"
                :width="60"
              />
              <div class="quality-text">
                <span class="quality-score">{{ lastAudioQuality.quality_score }}分</span>
                <span class="quality-level" :class="getQualityClass(lastAudioQuality.quality_level)">
                  {{ lastAudioQuality.quality_level }}
                </span>
              </div>
            </div>

            <!-- 简化的反馈信息 -->
            <div class="simple-feedback">
              <div class="feedback-row">
                <span class="label">🔊 音量:</span>
                <span>{{ lastAudioQuality.detailed_feedback.volume_feedback }}</span>
              </div>
              <div class="feedback-row">
                <span class="label">⏱️ 时长:</span>
                <span>{{ lastAudioQuality.detailed_feedback.duration_feedback }}</span>
              </div>
              <div class="feedback-row">
                <span class="label">🎵 质量:</span>
                <span>{{ lastAudioQuality.detailed_feedback.quality_feedback }}</span>
              </div>
            </div>

            <!-- 操作按钮 -->
            <div class="quality-actions">
              <el-button 
                v-if="!lastAudioQuality.is_acceptable" 
                type="warning" 
                size="small"
                @click="retryRecording"
                :disabled="isRecording || isCheckingQuality"
              >
                重新录音
              </el-button>
              
              <el-button 
                v-if="lastAudioQuality.is_acceptable" 
                type="primary" 
                size="small"
                @click="proceedToAnalysis"
                :loading="isUploading"
              >
                {{ isUploading ? '正在分析...' : '开始分析' }}
              </el-button>
            </div>

            <!-- 问题和建议（只在质量不达标时显示） -->
            <div v-if="!lastAudioQuality.is_acceptable && showDetailedFeedback" class="detailed-issues">
              <div v-if="lastAudioQuality.issues.length > 0" class="issues">
                <h5>需要改善：</h5>
                <ul>
                  <li v-for="issue in lastAudioQuality.issues" :key="issue">{{ issue }}</li>
                </ul>
              </div>
              <div class="suggestions">
                <h5>建议：</h5>
                <ul>
                  <li v-for="suggestion in lastAudioQuality.suggestions" :key="suggestion">{{ suggestion }}</li>
                </ul>
              </div>
            </div>

            <div v-if="!lastAudioQuality.is_acceptable" class="toggle-details">
              <el-button text size="small" @click="showDetailedFeedback = !showDetailedFeedback">
                {{ showDetailedFeedback ? '收起详情' : '查看详情' }}
              </el-button>
            </div>
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
import { Microphone, Warning, Loading, Check } from '@element-plus/icons-vue'
import { useUserStore } from '../stores/user'
import axios from 'axios'

const route = useRoute()
const router = useRouter()
const uploadStatus = ref(null)
const analysisResult = ref(null)
const isRecording = ref(false)
const isCheckingQuality = ref(false)
const isUploading = ref(false)
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
const recordAttempts = ref(0)
const lastAudioQuality = ref(null)
const showDetailedFeedback = ref(false)
const acceptableAudioBlob = ref(null)

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
          noiseSuppression: false, // 测试时不要降噪
          echoCancellation: false,
          autoGainControl: false
        }
      })
      mediaRecorder = new window.MediaRecorder(stream)
      audioChunks = []
      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunks.push(e.data)
      }
      mediaRecorder.onstop = () => {
        stopVisualizer()
        checkAudioQuality() // 录音结束后检测质量
      }
      mediaRecorder.start()
      isRecording.value = true
      recordAttempts.value++
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

const checkAudioQuality = async () => {
  try {
    isCheckingQuality.value = true
    
    // 创建音频文件
    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' })
    
    const formData = new FormData()
    formData.append('breath_file', audioBlob, `voice_attempt_${recordAttempts.value}.webm`)
    
    const response = await fetch('/api/v1/microphone-test/check-breath-quality', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${userStore.token}`
      },
      body: formData
    })
    
    if (!response.ok) {
      throw new Error('质量检测请求失败')
    }
    
    const result = await response.json()
    lastAudioQuality.value = result.quality_result
    
    if (lastAudioQuality.value.is_acceptable) {
      ElMessage.success('录音质量良好！可以开始分析')
      // 保存高质量音频供后续分析使用
      acceptableAudioBlob.value = audioBlob
    } else {
      ElMessage.warning(`第${recordAttempts.value}次录音质量需要改善，请查看建议后重新录音`)
      showDetailedFeedback.value = true // 自动展开详细反馈
    }
    
  } catch (error) {
    ElMessage.error(`质量检测失败: ${error.message}`)
    lastAudioQuality.value = null
  } finally {
    isCheckingQuality.value = false
  }
}

const retryRecording = () => {
  // 重置状态，准备重新录音
  lastAudioQuality.value = null
  showDetailedFeedback.value = false
  volumeFeedback.value = '音量正常'
  volumeLevelClass.value = 'normal'
  uploadStatus.value = null
  analysisResult.value = null
}

const proceedToAnalysis = async () => {
  if (!acceptableAudioBlob.value) {
    ElMessage.error('没有可用的高质量音频')
    return
  }
  
  // 使用高质量音频进行分析
  await uploadAudio(acceptableAudioBlob.value)
}

const uploadAudio = async (audioBlob = null) => {
  // 上传新语音前，清除仪表盘本地存储
  localStorage.removeItem('voice_analysis_conversation');
  
  // 如果没有提供audioBlob，使用最新的录音（向后兼容）
  const blobToUpload = audioBlob || new Blob(audioChunks, { type: 'audio/webm' })
  
  const formData = new FormData()
  const timestamp = new Date().getTime()
  formData.append('file', blobToUpload, `voice_${timestamp}.webm`)
  
  // 存储首轮分析请求内容到 localStorage
  localStorage.setItem('initialLLMMessage', JSON.stringify({
    role: 'user',
    content: '请分析我的语音健康'
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
      isUploading.value = true
      uploadStatus.value = { type: 'info', message: '正在上传录音...' }
      console.log('使用的token:', userStore.token)
      
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
    } finally {
      isUploading.value = false
    }
  }
}

const goToMicTest = () => {
  router.push('/microphone-test')
}

const getQualityColor = (score) => {
  if (score >= 80) return '#409EFF'
  if (score >= 60) return '#67C23A'
  if (score >= 40) return '#E6A23C'
  return '#F56C6C'
}

const getQualityClass = (level) => {
  return level.toLowerCase().replace(' ', '-')
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

.record-btn.success {
  background: linear-gradient(135deg, #67c23a 60%, #95d475 100%);
}

.record-btn.checking {
  background: linear-gradient(135deg, #409eff 60%, #79bbff 100%);
  cursor: not-allowed;
}

.record-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
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

.mic-test-tip {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  font-size: 15px;
  color: #666;
}

.mic-test-link {
  padding: 0;
  background: none;
  border: none;
  color: #2196f3;
  font: inherit;
  cursor: pointer;
  outline: inherit;
}

.audio-quality-feedback {
  margin-top: 20px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(179, 229, 252, 0.2);
  border: 1px solid #e3f2fd;
}

.quality-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.quality-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.quality-score {
  font-size: 20px;
  font-weight: bold;
  color: #2196f3;
}

.quality-level {
  font-size: 14px;
  font-weight: 500;
}

.quality-level.优秀 { color: #67c23a; }
.quality-level.良好 { color: #409eff; }
.quality-level.一般 { color: #e6a23c; }
.quality-level.较差 { color: #f56c6c; }

.simple-feedback {
  background: #fff;
  border-radius: 8px;
  padding: 12px;
  margin: 12px 0;
}

.feedback-row {
  display: flex;
  align-items: center;
  margin-bottom: 6px;
  font-size: 14px;
}

.feedback-row:last-child {
  margin-bottom: 0;
}

.feedback-row .label {
  font-weight: bold;
  color: #2196f3;
  min-width: 60px;
  margin-right: 8px;
}

.quality-actions {
  margin-top: 16px;
  display: flex;
  gap: 12px;
  justify-content: center;
}

.detailed-issues {
  margin-top: 16px;
  padding: 12px;
  background: #fff;
  border-radius: 8px;
  border-left: 4px solid #f56c6c;
}

.detailed-issues h5 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #f56c6c;
}

.detailed-issues ul {
  margin: 0;
  padding-left: 16px;
}

.detailed-issues li {
  margin: 4px 0;
  font-size: 13px;
  color: #666;
}

.issues {
  margin-bottom: 12px;
}

.suggestions h5 {
  color: #2196f3 !important;
}

.toggle-details {
  margin-top: 12px;
  text-align: center;
}

.attempt-info {
  margin-top: 8px;
  text-align: center;
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