<template>
  <div class="microphone-test-container">
    <div class="test-content">
      <el-card class="test-card">
        <template #header>
          <div class="card-header">
            <el-icon class="test-icon"><VideoCamera /></el-icon>
            <h2>麦克风质量评估</h2>
          </div>
        </template>

        <!-- 测试说明 -->
        <div v-if="currentStep === 'introduction'" class="introduction">
          <div class="intro-content">
            <h3>为什么需要测试麦克风？</h3>
            <p>为了确保最佳的语音分析效果，我们需要验证您的麦克风和环境是否适合进行呼吸音检测。</p>
            
            <div class="test-steps">
              <h4>测试流程：</h4>
              <div class="step-list">
                <div class="step-item">
                  <div class="step-number">1</div>
                  <div class="step-content">
                    <h5>环境噪声测试</h5>
                    <p>保持安静2秒钟，检测环境噪声水平</p>
                  </div>
                </div>
                <div class="step-item">
                  <div class="step-number">2</div>
                  <div class="step-content">
                    <h5>呼吸音测试</h5>
                    <p>靠近麦克风正常呼吸5秒钟，检测麦克风收音效果</p>
                  </div>
                </div>
              </div>
            </div>

            <div class="preparation-tips">
              <h4>准备工作：</h4>
              <ul>
                <li>选择安静的房间</li>
                <li>关闭风扇、空调等噪音源</li>
                <li>确保麦克风工作正常</li>
                <li>准备好与麦克风保持10-20厘米距离</li>
              </ul>
            </div>

            <el-button type="primary" size="large" @click="startTest" class="start-btn">
              开始测试
            </el-button>
          </div>
        </div>

        <!-- 噪声测试 -->
        <div v-if="currentStep === 'noise_test'" class="test-step">
          <div class="step-header">
            <h3>第一步：环境噪声测试</h3>
            <p>请保持完全安静，不要说话或移动，我们将录制2秒钟来检测环境噪声水平</p>
          </div>

          <div class="test-area">
            <canvas ref="noiseCanvas" class="waveform-canvas"></canvas>
            <div class="volume-feedback" :class="noiseLevelClass">{{ noiseVolumeFeedback }}</div>
            
            <button
              class="test-btn"
              :class="{ recording: isNoiseRecording }"
              @click="toggleNoiseRecording"
              :disabled="noiseTestCompleted"
            >
              <el-icon><Microphone /></el-icon>
            </button>
            
            <div class="test-tip">
              {{ isNoiseRecording ? '正在检测环境噪声...' : noiseTestCompleted ? '噪声测试已完成' : '点击开始噪声测试' }}
            </div>

            <div v-if="noiseTestCompleted" class="test-result">
              <el-alert
                :title="noiseTestResult.passed ? '环境噪声测试通过' : '环境噪声过高'"
                :type="noiseTestResult.passed ? 'success' : 'warning'"
                :description="noiseTestResult.message"
                show-icon
              />
              <el-button type="primary" @click="nextStep" class="next-btn">
                下一步：呼吸音测试
              </el-button>
            </div>
          </div>
        </div>

        <!-- 呼吸音测试 -->
        <div v-if="currentStep === 'breath_test'" class="test-step">
          <div class="step-header">
            <h3>第二步：呼吸音测试</h3>
            <p>请靠近麦克风10-20厘米，正常缓慢呼吸5秒钟，我们将检测麦克风收音效果</p>
            <div v-if="breathAttempts > 0" class="attempt-counter">
              <el-tag type="info">已尝试 {{ breathAttempts }} 次</el-tag>
            </div>
          </div>

          <div class="test-area">
            <canvas ref="breathCanvas" class="waveform-canvas"></canvas>
            <div class="volume-feedback" :class="breathLevelClass">{{ breathVolumeFeedback }}</div>
            
            <button
              class="test-btn"
              :class="{ recording: isBreathRecording, success: lastBreathQuality && lastBreathQuality.is_acceptable }"
              @click="toggleBreathRecording"
              :disabled="isCheckingQuality"
            >
              <el-icon v-if="isCheckingQuality"><Loading /></el-icon>
              <el-icon v-else-if="lastBreathQuality && lastBreathQuality.is_acceptable"><Check /></el-icon>
              <el-icon v-else><Microphone /></el-icon>
            </button>
            
            <div class="test-tip">
              <span v-if="isBreathRecording">正在录制呼吸音...</span>
              <span v-else-if="isCheckingQuality">正在分析音频质量...</span>
              <span v-else-if="lastBreathQuality && lastBreathQuality.is_acceptable">质量达标！可以继续下一步</span>
              <span v-else>点击开始呼吸音测试</span>
            </div>

            <!-- 实时质量反馈 -->
            <div v-if="lastBreathQuality" class="quality-feedback">
              <div class="quality-summary">
                <el-progress
                  type="circle"
                  :percentage="lastBreathQuality.quality_score"
                  :color="getScoreColor(lastBreathQuality.quality_score)"
                  :width="80"
                />
                <div class="quality-info">
                  <h4>质量评分</h4>
                  <p :class="getQualityClass(lastBreathQuality.quality_level)">
                    {{ lastBreathQuality.quality_level }}
                  </p>
                  <small>时长: {{ lastBreathQuality.duration.toFixed(1) }}秒</small>
                </div>
              </div>

              <!-- 详细反馈 -->
              <div class="detailed-feedback">
                <div class="feedback-item">
                  <span class="feedback-label">🔊 音量:</span>
                  <span>{{ lastBreathQuality.detailed_feedback.volume_feedback }}</span>
                </div>
                <div class="feedback-item">
                  <span class="feedback-label">⏱️ 时长:</span>
                  <span>{{ lastBreathQuality.detailed_feedback.duration_feedback }}</span>
                </div>
                <div class="feedback-item">
                  <span class="feedback-label">🎵 质量:</span>
                  <span>{{ lastBreathQuality.detailed_feedback.quality_feedback }}</span>
                </div>
              </div>

              <!-- 问题和建议 -->
              <div v-if="lastBreathQuality.issues.length > 0" class="quality-issues">
                <h5>需要改善的问题：</h5>
                <ul>
                  <li v-for="issue in lastBreathQuality.issues" :key="issue" class="issue-item">
                    {{ issue }}
                  </li>
                </ul>
              </div>

              <div class="quality-suggestions">
                <h5>建议：</h5>
                <ul>
                  <li v-for="suggestion in lastBreathQuality.suggestions" :key="suggestion" class="suggestion-item">
                    {{ suggestion }}
                  </li>
                </ul>
              </div>
            </div>

            <!-- 操作按钮 -->
            <div class="breath-test-actions">
              <el-button 
                v-if="lastBreathQuality && !lastBreathQuality.is_acceptable" 
                type="warning" 
                @click="retryBreathTest"
                :disabled="isBreathRecording || isCheckingQuality"
                class="retry-btn"
              >
                重新录音
              </el-button>
              
              <el-button 
                v-if="lastBreathQuality && lastBreathQuality.is_acceptable" 
                type="primary" 
                @click="proceedToAnalysis"
                class="continue-btn"
              >
                质量良好，继续分析
              </el-button>
            </div>
          </div>
        </div>

        <!-- 测试结果 -->
        <div v-if="currentStep === 'results'" class="test-results">
          <div class="results-header">
            <h3>麦克风质量评估结果</h3>
          </div>

          <div v-if="testResults" class="results-content">
            <!-- 总体评估 -->
            <div class="overall-assessment">
              <div class="quality-score">
                <el-progress
                  type="circle"
                  :percentage="testResults.quality_score"
                  :color="getScoreColor(testResults.quality_score)"
                  :width="120"
                />
                <div class="score-text">
                  <h4>质量评分</h4>
                  <p>{{ testResults.overall_quality }}</p>
                </div>
              </div>
              
              <div class="test-status">
                <el-alert
                  :title="testResults.test_passed ? '测试通过！' : '测试未通过'"
                  :type="testResults.test_passed ? 'success' : 'warning'"
                  :description="testResults.test_passed ? '您的麦克风和环境适合进行语音诊断' : '建议根据以下建议进行调整'"
                  show-icon
                />
              </div>
            </div>

            <!-- 详细指标 -->
            <div class="detailed-metrics">
              <h4>详细检测指标</h4>
              <el-descriptions :column="2" border>
                <el-descriptions-item label="环境噪声">
                  <span :class="getMetricClass(testResults.detailed_analysis.noise_analysis)">
                    {{ testResults.detailed_analysis.noise_analysis }}
                  </span>
                  <small>(RMS: {{ testResults.metrics.noise_rms.toFixed(4) }})</small>
                </el-descriptions-item>
                <el-descriptions-item label="呼吸音音量">
                  <span :class="getMetricClass(testResults.detailed_analysis.volume_analysis)">
                    {{ testResults.detailed_analysis.volume_analysis }}
                  </span>
                  <small>(RMS: {{ testResults.metrics.breath_rms.toFixed(4) }})</small>
                </el-descriptions-item>
                <el-descriptions-item label="信噪比">
                  <span :class="getMetricClass(testResults.detailed_analysis.snr_analysis)">
                    {{ testResults.detailed_analysis.snr_analysis }}
                  </span>
                  <small>({{ testResults.metrics.snr.toFixed(1) }} dB)</small>
                </el-descriptions-item>
                <el-descriptions-item label="频率特征">
                  <span :class="getMetricClass(testResults.detailed_analysis.frequency_analysis)">
                    {{ testResults.detailed_analysis.frequency_analysis }}
                  </span>
                  <small>({{ (testResults.metrics.frequency_ratio * 100).toFixed(1) }}%)</small>
                </el-descriptions-item>
              </el-descriptions>
            </div>

            <!-- 问题和建议 -->
            <div v-if="testResults.issues.length > 0" class="issues-recommendations">
              <h4>发现的问题</h4>
              <ul class="issues-list">
                <li v-for="issue in testResults.issues" :key="issue" class="issue-item">
                  {{ issue }}
                </li>
              </ul>
            </div>

            <div class="recommendations">
              <h4>改善建议</h4>
              <ul class="recommendations-list">
                <li v-for="recommendation in testResults.recommendations" :key="recommendation" class="recommendation-item">
                  {{ recommendation }}
                </li>
              </ul>
            </div>

            <!-- 操作按钮 -->
            <div class="action-buttons">
              <el-button @click="resetTest" class="restart-btn">重新测试</el-button>
              <el-button 
                type="primary" 
                @click="goToHome" 
                :disabled="!testResults.test_passed"
                class="continue-btn"
              >
                {{ testResults.test_passed ? '开始语音检测' : '改善后重新测试' }}
              </el-button>
            </div>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { VideoCamera, Microphone, Loading, Check } from '@element-plus/icons-vue'
import { useUserStore } from '../stores/user'

const router = useRouter()
const userStore = useUserStore()

// 测试步骤控制
const currentStep = ref('introduction')
const isAnalyzing = ref(false)

// 噪声测试相关
const isNoiseRecording = ref(false)
const noiseTestCompleted = ref(false)
const noiseTestResult = ref(null)
const noiseVolumeFeedback = ref('准备中...')
const noiseLevelClass = ref('normal')
const noiseCanvas = ref(null)
let noiseMediaRecorder = null
let noiseAudioChunks = []
let noiseAudioContext = null
let noiseAnalyser = null
let noiseAnimationId = null

// 呼吸音测试相关
const isBreathRecording = ref(false)
const breathTestCompleted = ref(false)
const breathTestResult = ref(null)
const breathVolumeFeedback = ref('准备中...')
const breathLevelClass = ref('normal')
const breathCanvas = ref(null)
const breathAttempts = ref(0)
const lastBreathQuality = ref(null)
const isCheckingQuality = ref(false)
const acceptableBreathAudio = ref(null) // 存储质量达标的音频
let breathMediaRecorder = null
let breathAudioChunks = []
let breathAudioContext = null
let breathAnalyser = null
let breathAnimationId = null

// 测试结果
const testResults = ref(null)

// 录音时长配置
const NOISE_DURATION = 2000 // 2秒
const BREATH_DURATION = 5000 // 5秒

const drawWaveform = (analyser, canvas, volumeFeedback, levelClass, isNoise = false) => {
  if (!analyser || !canvas.value) return
  
  const ctx = canvas.value.getContext('2d')
  const bufferLength = analyser.fftSize
  const dataArray = new Uint8Array(bufferLength)
  analyser.getByteTimeDomainData(dataArray)
  
  ctx.clearRect(0, 0, canvas.value.width, canvas.value.height)
  ctx.beginPath()
  
  let sum = 0
  for (let i = 0; i < bufferLength; i++) {
    const v = dataArray[i] / 128.0
    const y = (v * canvas.value.height) / 2
    
    if (i === 0) {
      ctx.moveTo(i, y)
    } else {
      ctx.lineTo(i, y)
    }
    sum += Math.abs(v - 1)
  }
  
  ctx.strokeStyle = isNoise ? '#f56c6c' : '#2196f3'
  ctx.lineWidth = 2
  ctx.stroke()
  
  // 音量反馈
  const avg = sum / bufferLength
  if (isNoise) {
    // 噪声测试：期望音量很低
    if (avg < 0.02) {
      volumeFeedback.value = '环境很安静'
      levelClass.value = 'good'
    } else if (avg < 0.05) {
      volumeFeedback.value = '环境较安静'
      levelClass.value = 'normal'
    } else {
      volumeFeedback.value = '环境噪声过高'
      levelClass.value = 'high'
    }
  } else {
    // 呼吸音测试：期望适中音量
    if (avg < 0.05) {
      volumeFeedback.value = '声音太小，请靠近麦克风'
      levelClass.value = 'low'
    } else if (avg > 0.35) {
      volumeFeedback.value = '声音太大，请调整距离'
      levelClass.value = 'high'
    } else {
      volumeFeedback.value = '音量正常'
      levelClass.value = 'good'
    }
  }
  
  const animationId = requestAnimationFrame(() => drawWaveform(analyser, canvas, volumeFeedback, levelClass, isNoise))
  if (isNoise) {
    noiseAnimationId = animationId
  } else {
    breathAnimationId = animationId
  }
}

const startVisualizer = async (isNoise = false) => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        noiseSuppression: false, // 测试时不要降噪
        echoCancellation: false,
        autoGainControl: false
      }
    })
    
    const audioContext = new (window.AudioContext || window.webkitAudioContext)()
    const source = audioContext.createMediaStreamSource(stream)
    const analyser = audioContext.createAnalyser()
    analyser.fftSize = 512
    source.connect(analyser)
    
    if (isNoise) {
      noiseAudioContext = audioContext
      noiseAnalyser = analyser
      drawWaveform(analyser, noiseCanvas, noiseVolumeFeedback, noiseLevelClass, true)
    } else {
      breathAudioContext = audioContext
      breathAnalyser = analyser
      drawWaveform(analyser, breathCanvas, breathVolumeFeedback, breathLevelClass, false)
    }
    
    return stream
  } catch (err) {
    ElMessage.error('无法获取麦克风权限')
    throw err
  }
}

const stopVisualizer = (isNoise = false) => {
  if (isNoise) {
    if (noiseAnimationId) cancelAnimationFrame(noiseAnimationId)
    if (noiseAudioContext) noiseAudioContext.close()
    noiseAudioContext = null
    noiseAnalyser = null
  } else {
    if (breathAnimationId) cancelAnimationFrame(breathAnimationId)
    if (breathAudioContext) breathAudioContext.close()
    breathAudioContext = null
    breathAnalyser = null
  }
}

const startTest = () => {
  currentStep.value = 'noise_test'
}

const nextStep = () => {
  currentStep.value = 'breath_test'
}

const toggleNoiseRecording = async () => {
  if (!isNoiseRecording.value) {
    try {
      const stream = await startVisualizer(true)
      noiseMediaRecorder = new MediaRecorder(stream)
      noiseAudioChunks = []
      
      noiseMediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) noiseAudioChunks.push(e.data)
      }
      
      noiseMediaRecorder.onstop = () => {
        stopVisualizer(true)
        processNoiseTest()
      }
      
      noiseMediaRecorder.start()
      isNoiseRecording.value = true
      
      // 2秒后自动停止
      setTimeout(() => {
        if (noiseMediaRecorder && isNoiseRecording.value) {
          noiseMediaRecorder.stop()
          isNoiseRecording.value = false
        }
      }, NOISE_DURATION)
      
    } catch (err) {
      ElMessage.error('无法开始录音')
    }
  }
}

const toggleBreathRecording = async () => {
  if (!isBreathRecording.value) {
    try {
      const stream = await startVisualizer(false)
      breathMediaRecorder = new MediaRecorder(stream)
      breathAudioChunks = []
      
      breathMediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) breathAudioChunks.push(e.data)
      }
      
      breathMediaRecorder.onstop = () => {
        stopVisualizer(false)
        checkBreathQuality()
      }
      
      breathMediaRecorder.start()
      isBreathRecording.value = true
      breathAttempts.value++
      
      // 5秒后自动停止
      setTimeout(() => {
        if (breathMediaRecorder && isBreathRecording.value) {
          breathMediaRecorder.stop()
          isBreathRecording.value = false
        }
      }, BREATH_DURATION)
      
    } catch (err) {
      ElMessage.error('无法开始录音')
    }
  }
}

const processNoiseTest = () => {
  noiseTestCompleted.value = true
  // 简单的本地检测，实际分析在服务器端进行
  noiseTestResult.value = {
    passed: true, // 暂时设为通过，最终结果由服务器决定
    message: '环境噪声检测完成，请继续呼吸音测试'
  }
}

const checkBreathQuality = async () => {
  try {
    isCheckingQuality.value = true
    
    // 创建音频文件
    const breathBlob = new Blob(breathAudioChunks, { type: 'audio/webm' })
    
    const formData = new FormData()
    formData.append('breath_file', breathBlob, `breath_attempt_${breathAttempts.value}.webm`)
    
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
    lastBreathQuality.value = result.quality_result
    
    if (lastBreathQuality.value.is_acceptable) {
      // 质量达标，保存音频供最终分析使用
      acceptableBreathAudio.value = breathBlob
      ElMessage.success('呼吸音质量良好！')
    } else {
      ElMessage.warning(`第${breathAttempts.value}次录音质量需要改善，请根据建议重新录音`)
    }
    
  } catch (error) {
    ElMessage.error(`质量检测失败: ${error.message}`)
    lastBreathQuality.value = null
  } finally {
    isCheckingQuality.value = false
  }
}

const retryBreathTest = () => {
  lastBreathQuality.value = null
  breathVolumeFeedback.value = '准备中...'
  breathLevelClass.value = 'normal'
}

const proceedToAnalysis = async () => {
  if (!acceptableBreathAudio.value) {
    ElMessage.error('没有可用的高质量呼吸音频')
    return
  }
  
  try {
    isAnalyzing.value = true
    
    // 使用环境噪声和质量达标的呼吸音进行最终分析
    const noiseBlob = new Blob(noiseAudioChunks, { type: 'audio/webm' })
    
    const formData = new FormData()
    formData.append('noise_file', noiseBlob, 'noise_test.webm')
    formData.append('breath_file', acceptableBreathAudio.value, 'breath_final.webm')
    
    const response = await fetch('/api/v1/microphone-test/analyze', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${userStore.token}`
      },
      body: formData
    })
    
    if (!response.ok) {
      throw new Error('分析请求失败')
    }
    
    const result = await response.json()
    testResults.value = result.test_result
    currentStep.value = 'results'
    
    ElMessage.success('麦克风质量分析完成')
    
  } catch (error) {
    ElMessage.error(`分析失败: ${error.message}`)
  } finally {
    isAnalyzing.value = false
  }
}

const getScoreColor = (score) => {
  if (score >= 85) return '#67c23a'
  if (score >= 70) return '#52c41a'
  if (score >= 50) return '#faad14'
  return '#f5222d'
}

const getQualityClass = (level) => {
  const levelMap = {
    '优秀': 'quality-excellent',
    '良好': 'quality-good',
    '一般': 'quality-fair',
    '较差': 'quality-poor'
  }
  return levelMap[level] || 'quality-unknown'
}

const getMetricClass = (status) => {
  return status === '良好' ? 'metric-good' : 'metric-poor'
}

const resetTest = () => {
  currentStep.value = 'introduction'
  isNoiseRecording.value = false
  isBreathRecording.value = false
  isCheckingQuality.value = false
  isAnalyzing.value = false
  noiseTestCompleted.value = false
  breathTestCompleted.value = false
  breathAttempts.value = 0
  lastBreathQuality.value = null
  acceptableBreathAudio.value = null
  testResults.value = null
  noiseTestResult.value = null
  breathTestResult.value = null
  
  // 重置音频相关状态
  noiseVolumeFeedback.value = '准备中...'
  noiseLevelClass.value = 'normal'
  breathVolumeFeedback.value = '准备中...'
  breathLevelClass.value = 'normal'
  
  // 清理音频上下文
  stopVisualizer(true)
  stopVisualizer(false)
}

const goToHome = () => {
  if (testResults.value && testResults.value.test_passed) {
    router.push('/home')
  } else {
    ElMessage.warning('请先通过麦克风测试')
  }
}

onMounted(() => {
  // 初始化画布
  if (noiseCanvas.value) {
    noiseCanvas.value.width = 400
    noiseCanvas.value.height = 80
  }
  if (breathCanvas.value) {
    breathCanvas.value.width = 400
    breathCanvas.value.height = 80
  }
})

onBeforeUnmount(() => {
  // 清理所有音频资源
  stopVisualizer(true)
  stopVisualizer(false)
  
  // 停止所有正在进行的录音
  if (noiseMediaRecorder && noiseMediaRecorder.state === 'recording') {
    noiseMediaRecorder.stop()
  }
  if (breathMediaRecorder && breathMediaRecorder.state === 'recording') {
    breathMediaRecorder.stop()
  }
})
</script>

<style scoped>
.microphone-test-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #e8f5e8 0%, #f0f9ff 100%);
}

.test-content {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding: 60px 20px 20px;
  min-height: 90vh;
}

.test-card {
  width: 600px;
  border-radius: 22px;
  box-shadow: 0 4px 32px rgba(0, 0, 0, 0.1);
  background: #fff;
  padding: 32px 24px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 20px;
  font-weight: bold;
  color: #2196f3;
}

.test-icon {
  font-size: 32px;
  color: #2196f3;
}

.introduction {
  text-align: center;
}

.intro-content h3 {
  color: #2196f3;
  margin-bottom: 16px;
}

.test-steps {
  margin: 32px 0;
  text-align: left;
}

.step-list {
  display: flex;
  gap: 24px;
  margin: 16px 0;
}

.step-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  flex: 1;
}

.step-number {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #2196f3;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  flex-shrink: 0;
}

.step-content h5 {
  margin: 0 0 8px 0;
  color: #333;
}

.step-content p {
  margin: 0;
  color: #666;
  font-size: 14px;
}

.preparation-tips {
  background: #f5f7fa;
  border-radius: 12px;
  padding: 20px;
  margin: 24px 0;
  text-align: left;
}

.preparation-tips ul {
  margin: 8px 0 0 0;
  padding-left: 20px;
}

.preparation-tips li {
  margin: 8px 0;
  color: #666;
}

.start-btn {
  margin-top: 24px;
  padding: 12px 32px;
  font-size: 16px;
}

.test-step {
  text-align: center;
}

.step-header h3 {
  color: #2196f3;
  margin-bottom: 16px;
}

.step-header p {
  color: #666;
  margin-bottom: 32px;
}

.test-area {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.waveform-canvas {
  width: 400px;
  height: 80px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  margin: 18px 0 16px 0;
  display: block;
}

.volume-feedback {
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 16px;
  padding: 8px 16px;
  border-radius: 16px;
  transition: all 0.3s;
}

.volume-feedback.good {
  background: #f0f9ff;
  color: #2196f3;
}

.volume-feedback.normal {
  background: #fff7e6;
  color: #fa8c16;
}

.volume-feedback.low {
  background: #fff1f0;
  color: #ff4d4f;
}

.volume-feedback.high {
  background: #fff1f0;
  color: #ff4d4f;
}

.test-btn {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: linear-gradient(135deg, #2196f3 60%, #64b5f6 100%);
  border: none;
  color: #fff;
  font-size: 32px;
  box-shadow: 0 4px 16px rgba(33, 150, 243, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  margin-bottom: 16px;
  transition: all 0.3s;
}

.test-btn:hover {
  box-shadow: 0 8px 32px rgba(33, 150, 243, 0.4);
  transform: scale(1.05);
}

.test-btn.recording {
  background: linear-gradient(135deg, #f56c6c 60%, #ff9800 100%);
  animation: pulse 1.5s infinite;
}

.test-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
  animation: none;
}

@keyframes pulse {
  0% { box-shadow: 0 0 0 0 rgba(245, 108, 108, 0.4); }
  70% { box-shadow: 0 0 0 20px rgba(245, 108, 108, 0); }
  100% { box-shadow: 0 0 0 0 rgba(245, 108, 108, 0); }
}

.test-tip {
  font-size: 16px;
  color: #666;
  margin-bottom: 24px;
}

.test-result {
  margin-top: 24px;
  width: 100%;
}

.next-btn, .analyze-btn {
  margin-top: 16px;
  padding: 12px 24px;
}

.test-results {
  padding: 20px 0;
}

.results-header h3 {
  color: #2196f3;
  text-align: center;
  margin-bottom: 32px;
}

.overall-assessment {
  display: flex;
  gap: 32px;
  align-items: center;
  margin-bottom: 32px;
  padding: 24px;
  background: #f8f9fa;
  border-radius: 12px;
}

.quality-score {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.score-text h4 {
  margin: 0;
  color: #333;
}

.score-text p {
  margin: 4px 0 0 0;
  color: #666;
}

.test-status {
  flex: 1;
}

.detailed-metrics {
  margin-bottom: 32px;
}

.detailed-metrics h4 {
  color: #333;
  margin-bottom: 16px;
}

.metric-good {
  color: #67c23a;
  font-weight: bold;
}

.metric-poor {
  color: #f56c6c;
  font-weight: bold;
}

.issues-recommendations {
  margin-bottom: 24px;
}

.issues-recommendations h4 {
  color: #f56c6c;
  margin-bottom: 12px;
}

.issues-list {
  list-style: none;
  padding: 0;
}

.issue-item {
  background: #fff2f0;
  border-left: 4px solid #f56c6c;
  padding: 12px 16px;
  margin: 8px 0;
  border-radius: 4px;
}

.recommendations h4 {
  color: #2196f3;
  margin-bottom: 12px;
}

.recommendations-list {
  list-style: none;
  padding: 0;
}

.recommendation-item {
  background: #f0f9ff;
  border-left: 4px solid #2196f3;
  padding: 12px 16px;
  margin: 8px 0;
  border-radius: 4px;
}

.action-buttons {
  display: flex;
  gap: 16px;
  justify-content: center;
  margin-top: 32px;
}

.restart-btn, .continue-btn {
  padding: 12px 24px;
  font-size: 16px;
}

.test-btn.success {
  background: linear-gradient(135deg, #67c23a 60%, #95d475 100%);
}

.attempt-counter {
  margin-top: 12px;
  text-align: center;
}

.quality-feedback {
  margin-top: 20px;
  background: #f8f9fa;
  border-radius: 12px;
  padding: 20px;
  border: 1px solid #e9ecef;
}

.quality-summary {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 20px;
}

.quality-info h4 {
  margin: 0 0 4px 0;
  color: #333;
  font-size: 14px;
}

.quality-info p {
  margin: 0 0 4px 0;
  font-weight: bold;
  font-size: 16px;
}

.quality-info small {
  color: #666;
  font-size: 12px;
}

.quality-excellent { color: #52c41a; }
.quality-good { color: #1890ff; }
.quality-fair { color: #faad14; }
.quality-poor { color: #f5222d; }

.detailed-feedback {
  margin-bottom: 16px;
}

.feedback-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 8px 0;
  padding: 6px 12px;
  background: #fff;
  border-radius: 6px;
  font-size: 14px;
  color: #666;
}

.feedback-label {
  font-weight: bold;
  color: #2196f3;
  min-width: 60px;
}

.quality-issues, .quality-suggestions {
  margin: 16px 0;
}

.quality-issues h5, .quality-suggestions h5 {
  margin: 0 0 8px 0;
  font-size: 14px;
  font-weight: bold;
}

.quality-issues h5 {
  color: #f5222d;
}

.quality-suggestions h5 {
  color: #2196f3;
}

.quality-issues ul, .quality-suggestions ul {
  margin: 0;
  padding: 0;
  list-style: none;
}

.issue-item {
  background: #fff2f0;
  border-left: 3px solid #f5222d;
  padding: 8px 12px;
  margin: 4px 0;
  border-radius: 4px;
  font-size: 13px;
}

.suggestion-item {
  background: #f0f9ff;
  border-left: 3px solid #2196f3;
  padding: 8px 12px;
  margin: 4px 0;
  border-radius: 4px;
  font-size: 13px;
}

.breath-test-actions {
  margin-top: 20px;
  display: flex;
  gap: 12px;
  justify-content: center;
  flex-wrap: wrap;
}

.retry-btn, .continue-btn {
  padding: 10px 20px;
  font-size: 14px;
  border-radius: 8px;
  min-width: 120px;
}

.retry-btn {
  background: #faad14;
  border-color: #faad14;
  color: #fff;
}

.retry-btn:hover {
  background: #ffc53d;
  border-color: #ffc53d;
}

.continue-btn {
  background: #52c41a;
  border-color: #52c41a;
}

.continue-btn:hover {
  background: #73d13d;
  border-color: #73d13d;
}

@media (max-width: 768px) {
  .test-card {
    width: 100%;
    margin: 0 10px;
  }
  
  .step-list {
    flex-direction: column;
    gap: 16px;
  }
  
  .overall-assessment {
    flex-direction: column;
    gap: 20px;
  }
  
  .waveform-canvas {
    width: 100%;
    max-width: 350px;
  }
  
  .quality-summary {
    flex-direction: column;
    gap: 12px;
    text-align: center;
  }
  
  .breath-test-actions {
    flex-direction: column;
    align-items: center;
  }
  
  .retry-btn, .continue-btn {
    width: 100%;
    max-width: 200px;
  }
  
  .feedback-item {
    font-size: 13px;
  }
}
</style> 