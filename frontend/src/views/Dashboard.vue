<template>
  <div class="dashboard-container">
    <!-- 模式状态指示器 -->
    <div class="mode-indicator">
      <el-alert
        :title="modeDescription.title"
        :description="modeDescription.description"
        :type="modeDescription.color"
        show-icon
        :closable="false"
      />
    </div>
    
    <div class="main-content">
      <div class="dashboard-left">
        <!-- 健康结论 -->
        <div class="overview-section">
          <el-card class="main-overview" shadow="hover">
            <div class="overview-header">
              <h2>健康结论</h2>
            </div>
            <div class="overview-content">
              <div class="health-status" :class="{'danger': latestAnalysis.metrics.model_prediction && latestAnalysis.metrics.model_prediction !== '正常'}">
                {{ latestAnalysis.metrics.model_prediction || '暂无数据' }}
              </div>
              <div class="health-confidence" v-if="latestAnalysis.metrics.model_confidence">
                置信度: {{ (latestAnalysis.metrics.model_confidence * 100).toFixed(1) }}%
              </div>
            </div>
          </el-card>
        </div>
        <!-- 历史趋势分析 - 仅在主动分析模式显示 -->
        <el-card v-if="permissions.canViewHistoricalData" class="trend-card" shadow="hover">
          <div class="trend-header">
            <h2>历史趋势分析</h2>
            <el-select v-model="trendFilter" placeholder="选择特征" style="width: 140px;">
              <el-option label="音量 (RMS)" value="rms_values"/>
              <el-option label="过零率 (ZCR)" value="zcr_values"/>
              <el-option label="置信度" value="confidence_values"/>
            </el-select>
          </div>
          <div class="trend-description">
            <p>{{ getTrendDescription() }}</p>
          </div>
          <div class="chart-container">
            <LineChart
              :chart-data="{
                labels: historicalData.dates || [],
                datasets: [
                  {
                    label: trendFilterLabel,
                    data: historicalData[trendFilter] || [],
                    borderColor: '#4CAF50',
                    backgroundColor: 'rgba(76, 175, 80, 0.1)',
                    fill: true,
                    tension: 0.4
                  }
                ]
              }"
              :options="{
                responsive: true,
                maintainAspectRatio: false,
                scales: { 
                  y: { 
                    beginAtZero: trendFilter === 'confidence_values',
                    title: {
                      display: true,
                      text: getTrendYAxisLabel()
                    }
                  },
                  x: {
                    title: {
                      display: true,
                      text: '日期'
                    }
                  }
                },
                plugins: {
                  legend: {
                    display: true
                  },
                  tooltip: {
                    callbacks: {
                      label: function(context) {
                        const value = context.raw;
                        if (trendFilter === 'confidence_values') {
                          return `${trendFilterLabel}: ${(value * 100).toFixed(1)}%`;
                        }
                        return `${trendFilterLabel}: ${value ? value.toFixed(4) : '无数据'}`;
                      }
                    }
                  }
                }
              }"
            />
          </div>
        </el-card>
        
        <!-- 只读模式下的快捷操作 -->
        <el-card v-if="isReadOnlyMode" class="quick-actions-card" shadow="hover">
          <div class="quick-actions-header">
            <h2>快捷操作</h2>
          </div>
          <div class="quick-actions-content">
            <el-button type="primary" size="large" @click="startNewAnalysis" style="width: 100%; margin-bottom: 12px;">
              <el-icon><Position /></el-icon>
              开始新的语音分析
            </el-button>
            <el-button type="default" size="default" @click="goToSettings" style="width: 100%;">
              查看历史记录
            </el-button>
          </div>
        </el-card>
      </div>
      <div class="dashboard-right">
        <!-- 声学特征分析 - 仅在主动分析模式显示 -->
        <el-card v-if="permissions.canViewAcousticFeatures" class="feature-card" shadow="hover">
          <div class="feature-header">
            <h2>声学特征分析</h2>
            <el-button type="primary" @click="showFeatureDetail = true">查看详细特征</el-button>
          </div>
          <div class="feature-description">
            <p>声学特征是评估语音健康的重要指标，包括MFCC特征、色度特征和时域特征等。</p>
          </div>
          <div class="feature-brief">
            <el-row :gutter="20">
              <el-col :span="6">
                <div class="feature-item">
                  <div class="feature-label">MFCC1</div>
                  <div class="feature-value">{{ latestAnalysis.metrics && latestAnalysis.metrics.mfcc_1 !== null ? latestAnalysis.metrics.mfcc_1.toFixed(4) : '—' }}</div>
                </div>
              </el-col>
              <el-col :span="6">
                <div class="feature-item">
                  <div class="feature-label">Chroma1</div>
                  <div class="feature-value">{{ latestAnalysis.metrics && latestAnalysis.metrics.chroma_1 !== null ? latestAnalysis.metrics.chroma_1.toFixed(4) : '—' }}</div>
                </div>
              </el-col>
              <el-col :span="6">
                <div class="feature-item">
                  <div class="feature-label">RMS(音量)</div>
                  <div class="feature-value">{{ latestAnalysis.metrics && latestAnalysis.metrics.rms !== null ? latestAnalysis.metrics.rms.toFixed(4) : '—' }}</div>
                </div>
              </el-col>
              <el-col :span="6">
                <div class="feature-item">
                  <div class="feature-label">ZCR(过零率)</div>
                  <div class="feature-value">{{ latestAnalysis.metrics && latestAnalysis.metrics.zcr !== null ? latestAnalysis.metrics.zcr.toFixed(4) : '—' }}</div>
                </div>
              </el-col>
            </el-row>
          </div>
        </el-card>
        <!-- AI诊断与对话 -->
        <transition name="fade">
          <el-card class="ai-diagnosis-card" shadow="hover" :key="isInteractiveMode ? 'chat' : 'readonly'">
            <div class="diagnosis-header">
              <h2>AI诊断建议</h2>
              <div class="diagnosis-actions">
                <!-- <el-button v-if="isInteractiveMode" type="success" size="small" @click="exportReport">导出报告</el-button> -->
              </div>
            </div>
            <div class="chat-container">
              <div v-if="permissions.canChat">
                <!-- 可对话模式 -->
                <div class="chat-title">
                  <h3>AI 助手对话</h3>
                  <p class="chat-subtitle">您可以向AI助手询问关于您的语音健康分析结果的问题</p>
                </div>
                <div class="chat-messages" ref="chatMessages">
                  <div v-if="conversationHistory.length === 0" class="chat-empty-state">
                    <el-empty description="暂无对话记录" :image-size="100">
                      <template #description>
                        <p>您可以向AI助手询问关于您的语音健康分析结果的问题</p>
                      </template>
                    </el-empty>
                  </div>
                  <div 
                    v-for="(message, index) in conversationHistory" 
                    :key="index" 
                    class="message" 
                    :class="message.role"
                  >
                    <div class="message-content" v-html="renderMarkdown(message.content)"></div>
                  </div>
                  <div v-if="isLoading" class="message assistant loading">
                    <div class="typing-indicator">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  </div>
                </div>
                <div class="chat-input" v-if="permissions.canSendMessage">
                  <el-input
                    v-model="userMessage"
                    placeholder="请输入您的问题..."
                    :disabled="isLoading || loadingSummary"
                    @keyup.enter="sendMessage"
                  >
                    <template #append>
                      <el-button :disabled="isLoading || loadingSummary" @click="sendMessage" type="primary">
                        <el-icon><Position /></el-icon>
                        发送
                      </el-button>
                    </template>
                  </el-input>
                </div>
                <div class="chat-summary-actions" v-if="permissions.canCompleteConversation">
                  <el-button type="success" :loading="loadingSummary" @click="handleFinishConversation">
                    完成对话
                  </el-button>
                </div>
              </div>
              <div v-else>
                <!-- 只读模式 -->
                <div class="chat-title">
                  <h3>AI 诊断建议</h3>
                  <div class="chat-title-actions" v-if="permissions.canRefreshSuggestion">
                    <el-button size="small" type="primary" @click="refreshLatestSuggestion" :loading="loadingLatestSuggestion">
                      <el-icon><Refresh /></el-icon>
                      刷新
                    </el-button>
                  </div>
                  <p class="chat-subtitle" v-if="latestSessionSuggestion.created_at">
                    诊断时间: {{ new Date(latestSessionSuggestion.created_at).toLocaleString() }}
                  </p>
                  <el-alert v-if="showCompletionAlert" title="本次对话已结束，以下为AI诊断建议" type="info" show-icon style="margin-bottom: 12px;" />
                </div>
                <div class="chat-messages">
                  <div v-if="latestSessionSuggestion.diagnosis_suggestion" class="message assistant">
                    <div class="message-content">
                      <div class="diagnosis-header-readonly" v-if="latestSessionSuggestion.metrics">
                        <span class="diagnosis-label">诊断结果:</span>
                        <span class="diagnosis-value" :class="{'danger': latestSessionSuggestion.metrics.model_prediction && latestSessionSuggestion.metrics.model_prediction !== '正常'}">
                          {{ latestSessionSuggestion.metrics.model_prediction || '暂无数据' }}
                        </span>
                        <span class="diagnosis-confidence" v-if="latestSessionSuggestion.metrics.model_confidence">
                          (置信度: {{ (latestSessionSuggestion.metrics.model_confidence * 100).toFixed(1) }}%)
                        </span>
                      </div>
                      <div class="diagnosis-content">
                        <h4 class="diagnosis-suggestion-title">AI诊断建议:</h4>
                        <div class="diagnosis-suggestion-text" v-html="renderedDiagnosisSuggestion"></div>
                      </div>
                      <div class="metrics-summary" v-if="latestSessionSuggestion.metrics && (latestSessionSuggestion.metrics.rms !== null || latestSessionSuggestion.metrics.zcr !== null)">
                        <div class="metrics-title">声学特征摘要:</div>
                        <div class="metrics-grid-readonly">
                          <div class="metric-item-readonly" v-if="latestSessionSuggestion.metrics.rms !== null">
                            <span class="metric-label-readonly">RMS (音量):</span>
                            <span class="metric-value-readonly">{{ latestSessionSuggestion.metrics.rms.toFixed(4) }}</span>
                          </div>
                          <div class="metric-item-readonly" v-if="latestSessionSuggestion.metrics.zcr !== null">
                            <span class="metric-label-readonly">ZCR (过零率):</span>
                            <span class="metric-value-readonly">{{ latestSessionSuggestion.metrics.zcr.toFixed(4) }}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div v-else class="message assistant">
                    <div class="message-content">
                      <el-empty description="暂无AI诊断建议" :image-size="80">
                        <el-button type="primary" @click="startNewAnalysis">
                          开始新的语音分析
                        </el-button>
                      </el-empty>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </el-card>
        </transition>
      </div>
    </div>

    <!-- 声学特征详情对话框 - 仅在主动分析模式可用 -->
    <el-dialog 
      v-if="permissions.canViewAcousticFeatures"
      v-model="showFeatureDetail" 
      title="全部声学特征" 
      width="80%" 
      destroy-on-close
      @open="handleFeatureDialogOpen"
    >
      <div class="feature-tabs" v-if="showFeatureDetail">
        <el-tabs type="border-card">
          <el-tab-pane label="MFCC特征">
            <div class="feature-chart">
              <LineChart
                :chart-data="{
                  labels: Array.from({length: 13}, (_, i) => `MFCC${i+1}`),
                  datasets: [
                    {
                      label: 'MFCC特征值',
                      data: getMfccValues(),
                      backgroundColor: 'rgba(75, 192, 192, 0.2)',
                      borderColor: 'rgba(75, 192, 192, 1)',
                      borderWidth: 2,
                      tension: 0.4
                    }
                  ]
                }"
                :options="{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    title: {
                      display: true,
                      text: 'MFCC特征分布'
                    },
                    tooltip: {
                      callbacks: {
                        label: function(context) {
                          return `MFCC${context.dataIndex+1}: ${context.raw ? context.raw.toFixed(4) : '无数据'}`;
                        }
                      }
                    }
                  },
                  scales: {
                    y: {
                      beginAtZero: false,
                      title: {
                        display: true,
                        text: '特征值'
                      }
                    }
                  }
                }"
              />
            </div>
            <div class="feature-detail-list">
              <el-table :data="mfccTableData" stripe style="width: 100%">
                <el-table-column prop="name" label="特征" width="120" />
                <el-table-column prop="value" label="数值" />
                <el-table-column prop="description" label="说明" />
              </el-table>
            </div>
          </el-tab-pane>
          
          <el-tab-pane label="色度特征">
            <div class="feature-chart">
              <LineChart
                :chart-data="{
                  labels: Array.from({length: 12}, (_, i) => `Chroma${i+1}`),
                  datasets: [
                    {
                      label: '色度特征值',
                      data: getChromaValues(),
                      backgroundColor: 'rgba(153, 102, 255, 0.2)',
                      borderColor: 'rgba(153, 102, 255, 1)',
                      borderWidth: 2,
                      tension: 0.4
                    }
                  ]
                }"
                :options="{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    title: {
                      display: true,
                      text: '色度特征分布'
                    }
                  }
                }"
              />
            </div>
            <div class="feature-detail-list">
              <el-table :data="chromaTableData" stripe style="width: 100%">
                <el-table-column prop="name" label="特征" width="120" />
                <el-table-column prop="value" label="数值" />
                <el-table-column prop="description" label="说明" />
              </el-table>
            </div>
          </el-tab-pane>
          
          <el-tab-pane label="时域特征">
            <div class="feature-chart-grid">
              <div class="feature-chart-item">
                <div class="feature-chart">
                  <el-statistic title="RMS (音量)" :value="latestAnalysis.metrics.rms ? latestAnalysis.metrics.rms.toFixed(4) : '—'">
                    <template #suffix>
                      <el-tooltip content="均方根能量，表示声音的音量大小">
                        <el-icon><QuestionFilled /></el-icon>
                      </el-tooltip>
                    </template>
                  </el-statistic>
                </div>
              </div>
              <div class="feature-chart-item">
                <div class="feature-chart">
                  <el-statistic title="ZCR (过零率)" :value="latestAnalysis.metrics.zcr ? latestAnalysis.metrics.zcr.toFixed(4) : '—'">
                    <template #suffix>
                      <el-tooltip content="过零率，表示信号穿过零点的频率，与声音的频率相关">
                        <el-icon><QuestionFilled /></el-icon>
                      </el-tooltip>
                    </template>
                  </el-statistic>
                </div>
              </div>
            </div>
            <div class="feature-description">
              <h3>时域特征说明</h3>
              <p><strong>RMS (均方根能量):</strong> 表示音频信号的能量或音量大小。较高的RMS值表示声音较大，较低的值表示声音较小。</p>
              <p><strong>ZCR (过零率):</strong> 表示信号从正变为负或从负变为正的频率。在语音分析中，过零率可以用于区分浊音和清音，也可以用于检测语音的起始和结束。</p>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { marked } from 'marked'

let ws = null;

import { ref, computed, onMounted, onBeforeUnmount, nextTick, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Position, QuestionFilled, Refresh } from '@element-plus/icons-vue'
import { useUserStore } from '../stores/user'
import { useApi } from '../composables/useApi'
import { useDashboardMode } from '../composables/useDashboardMode'
import LineChart from '../components/LineChart.vue'
import { useWebSocket } from '../composables/useWebSocket'

console.log('Dashboard 组件初始化')

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const api = useApi()
const { isConnected } = useWebSocket()

// 使用仪表盘模式管理
const {
  currentMode,
  isInteractiveMode,
  isReadOnlyMode,
  permissions,
  activateInteractiveMode,
  completeConversation,
  getModeDescription,
  refreshMode
} = useDashboardMode()

const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)

// 最新分析结果
const latestAnalysis = ref({
  metrics: {
    rms: null,
    zcr: null,
    model_prediction: '',
    model_confidence: 0,
    // 初始化MFCC和Chroma特征为null
    ...Array.from({length: 13}, (_, i) => ({ [`mfcc_${i+1}`]: null })).reduce((acc, curr) => ({...acc, ...curr}), {}),
    ...Array.from({length: 12}, (_, i) => ({ [`chroma_${i+1}`]: null })).reduce((acc, curr) => ({...acc, ...curr}), {})
  },
  created_at: ''
})

const historicalData = ref({
  dates: [],
  rms_values: [],
  zcr_values: [],
  confidence_values: [],
  predictions: []
})

// LLM 对话
const conversationHistory = ref([])
const userMessage = ref('')
const isLoading = ref(false)
const chatMessages = ref(null)
const diagnosisSuggestion = ref('')
const loadingSummary = ref(false)
const loadingLatestSuggestion = ref(false)

// 图表相关
const selectedMetric = ref('f0')
const selectedMetricLabel = computed(() => {
  const labels = {
    f0: '基频(F0)',
    hnr: '谐噪比(HNR)',
    confidence: '置信度'
  }
  return labels[selectedMetric.value]
})
const selectedMetricData = computed(() => {
  const dataMap = {
    f0: historicalData.value.f0_values,
    hnr: historicalData.value.hnr_values,
    confidence: historicalData.value.confidence_values
  }
  return dataMap[selectedMetric.value]
})

// 隐藏的首轮大模型对话，仅用于后续 history 拼接，不显示在对话框
const initialLLMMessage = ref(null)

// 添加常量用于localStorage的key
const CONVERSATION_STORAGE_KEY = 'voice_analysis_conversation';
const INITIAL_MESSAGE_STORAGE_KEY = 'initialLLMMessage';

// 计算属性
const modeDescription = computed(() => getModeDescription())

// 兼容原有逻辑的计算属性
const isActiveSession = computed(() => isInteractiveMode.value)

const trendFilter = ref('rms_values')
const trendFilterLabel = computed(() => {
  if (trendFilter.value === 'rms_values') return '音量 (RMS)'
  if (trendFilter.value === 'zcr_values') return '过零率 (ZCR)'
  if (trendFilter.value === 'confidence_values') return '置信度'
  return ''
})

// 声学特征相关
const showFeatureDetail = ref(false)
const showCompletionAlert = ref(false)

// 获取最新分析结果
const fetchLatestAnalysis = async () => {
  try {
    const response = await api.get('/dashboard/latest')
    console.log('最新分析结果:', response.data)
    latestAnalysis.value = response.data
  } catch (error) {
    console.error('获取最新分析结果失败:', error)
    ElMessage.error('获取最新分析结果失败')
  }
}

// 获取历史数据
const fetchHistoricalData = async () => {
  try {
    const response = await api.get('/dashboard/historical')
    historicalData.value = response.data
  } catch (error) {
    console.error('获取历史数据失败:', error)
    ElMessage.error('获取历史数据失败')
  }
}

// 获取历史记录
const fetchHistory = async () => {
  loading.value = true
  try {
    const response = await api.get('/dashboard/history', {
      params: {
        skip: (currentPage.value - 1) * pageSize.value,
        limit: pageSize.value
      }
    })
    history.value = response.data.records
    total.value = response.data.total
    // 获取历史记录后，只用于其他功能，不再显示在UI上
  } catch (error) {
    console.error('获取历史记录失败:', error)
    ElMessage.error('获取历史记录失败')
  } finally {
    loading.value = false
  }
}

// 获取 session_id
const getSessionId = () => {
  if (latestAnalysis.value?.session_id) return latestAnalysis.value.session_id
  if (latestAnalysis.value?.metrics?.session_id) return latestAnalysis.value.metrics.session_id
  if (latestAnalysis.value?.voice_metrics?.session_id) return latestAnalysis.value.voice_metrics.session_id
  if (Array.isArray(history.value) && history.value.length > 0 && history.value[0]?.session_id) return history.value[0].session_id
  return null
}

// 新增方法
const startNewAnalysis = () => {
  router.push('/home')
}

const goToSettings = () => {
  router.push('/settings')
}

// 修改onMounted钩子，添加从localStorage恢复对话状态的逻辑
onMounted(() => {
  console.log('Dashboard 组件挂载', window.location.href, Date.now())
  console.log('当前URL:', window.location.href)
  console.log('route.query:', route.query)
  console.log('localStorage[voice_analysis_conversation]:', localStorage.getItem(CONVERSATION_STORAGE_KEY))
  refreshHistory()
  
  // 只有在 isActiveSession 为 true 时才恢复对话历史
  if (isActiveSession.value) {
    const savedConversation = localStorage.getItem(CONVERSATION_STORAGE_KEY);
    if (savedConversation) {
      try {
        conversationHistory.value = JSON.parse(savedConversation);
        console.log('已从本地存储恢复对话历史', conversationHistory.value.length, '条消息');
      } catch (e) {
        console.error('恢复对话历史失败:', e);
      }
    }
  }
  
  // 仅语音上传跳转时保存首轮大模型对话
  if (route.query.fromUpload && conversationHistory.value.length === 0) {
    console.log('检测到fromUpload参数且无对话历史，准备写入初始对话')
    // 从 localStorage 读取首轮分析请求内容
    const msg = localStorage.getItem(INITIAL_MESSAGE_STORAGE_KEY)
    if (msg) {
      initialLLMMessage.value = JSON.parse(msg)
      localStorage.removeItem(INITIAL_MESSAGE_STORAGE_KEY)
    }
    conversationHistory.value.push({
      role: 'assistant',
      content: '正在等待AI分析您的语音，请稍候...'
    })
    // 新增：写入localStorage，激活对话模式
    localStorage.setItem(CONVERSATION_STORAGE_KEY, JSON.stringify(conversationHistory.value));
    console.log('已写入初始对话到localStorage:', localStorage.getItem(CONVERSATION_STORAGE_KEY))
    refreshMode() // 确保isActiveSession立即变为true
  }
  
  // diagnosisSuggestion 有内容时自动同步到对话区
  if (diagnosisSuggestion.value) {
    conversationHistory.value.push({
      role: 'assistant',
      content: '[最终诊断建议] ' + diagnosisSuggestion.value
    })
  }
  
  window.addEventListener('llm-analysis-complete', handleLLMAnalysisComplete)
  window.addEventListener('voice-analysis-start', handleVoiceAnalysisStart)
  window.addEventListener('voice-analysis-result', handleVoiceAnalysisResult)
  
  // 建立WebSocket连接
  const userId = userStore.userInfo?.id || userStore.userInfo?.user_id
  if (userId) {
    console.log(`尝试连接WebSocket，用户ID: ${userId}`)
    // 使用确认可用的WebSocket URL格式
    ws = new WebSocket(`ws://${window.location.hostname}:8000/api/v1/diagnosis/ws/diagnosis/${userId}`)
    
    ws.onmessage = (event) => {
      try {
        console.log('收到WebSocket消息:', event.data)
        const data = JSON.parse(event.data)
        if (data.type === 'llm_analysis') {
          // 保存首轮prompt到 initialLLMMessage
          if (route.query.fromUpload && data.llm_prompt) {
            initialLLMMessage.value = {
              role: 'user',
              content: data.llm_prompt
            }
            console.log('[LLM对话调试] 收到首轮llm_prompt:', data.llm_prompt)
          }
          conversationHistory.value.push({
            role: 'assistant',
            content: '[AI诊断建议] ' + data.analysis
          })
          diagnosisSuggestion.value = data.analysis
          ElMessage.success('AI诊断建议已自动推送')
          
          // 保存对话状态到localStorage
          if (isActiveSession.value) {
            saveConversationToStorage()
          }
        }
      } catch (e) {
        console.error('WebSocket消息解析失败', e)
      }
    }
    ws.onopen = () => {
      console.log('WebSocket连接成功')
    }
    ws.onclose = () => {
      console.warn('WebSocket已断开')
    }
    ws.onerror = (e) => {
      console.error('WebSocket错误', e)
    }
  } else {
    console.warn('未获取到用户ID，无法建立WebSocket连接')
  }

  // 监听模式切换，进入只读模式时显示提示并设置定时器
  watch(isActiveSession, (val, oldVal) => {
    if (oldVal && !val) {
      showCompletionAlert.value = true;
      ElMessage({
        message: '对话已完成，已切换为只读模式。您可以查看AI诊断建议。',
        type: 'info',
        duration: 2500
      })
      // 10秒后隐藏提示
      setTimeout(() => {
        showCompletionAlert.value = false;
      }, 10000);
    }
  })

  // 初始化时，如果是只读模式，也显示提示并设置定时器
  if (!isActiveSession.value) {
    showCompletionAlert.value = true;
    // 10秒后隐藏提示
    setTimeout(() => {
      showCompletionAlert.value = false;
    }, 10000);
  }
})

// 监听路由变化，保存对话状态
watch(
  () => route.path,
  (newPath, oldPath) => {
    if (oldPath === '/dashboard' && newPath !== '/dashboard') {
      if (isActiveSession.value) {
        saveConversationToStorage()
      }
    }
  }
)

// 添加保存对话状态到localStorage的函数
const saveConversationToStorage = () => {
  if (conversationHistory.value.length > 0) {
    try {
      localStorage.setItem(CONVERSATION_STORAGE_KEY, JSON.stringify(conversationHistory.value))
      console.log('对话历史已保存到本地存储', conversationHistory.value.length, '条消息')
    } catch (e) {
      console.error('保存对话历史失败:', e)
    }
  }
}

// 修改sendMessage函数，发送消息后保存对话状态
const sendMessage = async () => {
  if (!userMessage.value.trim() || isLoading.value) return
  const message = userMessage.value
  userMessage.value = ''
  isLoading.value = true
  try {
    conversationHistory.value.push({
      role: 'user',
      content: message
    })
    // 组装完整历史，首轮大模型对话拼到最前面（不显示在对话框）
    let fullHistory = []
    if (initialLLMMessage.value) {
      fullHistory.push(initialLLMMessage.value)
    }
    // 过滤掉AI占位消息
    fullHistory = fullHistory.concat(conversationHistory.value.filter(m => m.role !== 'assistant' || m.content !== 'AI正在思考，请稍候...'))
    // 调试信息：打印本次发送的完整历史
    console.log('[LLM对话调试] 本次发送的历史：', JSON.stringify(fullHistory, null, 2))
    await nextTick()
    scrollToBottom()
    // 插入AI思考中占位
    conversationHistory.value.push({
      role: 'assistant',
      content: 'AI正在思考，请稍候...'
    })
    await nextTick()
    scrollToBottom()
    const sessionId = getSessionId()
    if (!sessionId) {
      throw new Error('未找到当前会话ID')
    }
    // 发送完整历史到 /llm/chat，单独设置超时时间为40秒
    const response = await api.post(`/llm/chat`, {
      message,
      session_id: sessionId,
      history: fullHistory
    }, { timeout: 40000 })
    // 替换最后一条AI占位为真实回复
    if (conversationHistory.value.length && conversationHistory.value[conversationHistory.value.length - 1].content === 'AI正在思考，请稍候...') {
      conversationHistory.value[conversationHistory.value.length - 1].content = response.data.analysis
    } else {
      conversationHistory.value.push({
        role: 'assistant',
        content: response.data.analysis
      })
    }
    // 保存对话状态到localStorage
    if (isActiveSession.value) {
      saveConversationToStorage()
    }
    
    await nextTick()
    scrollToBottom()
  } catch (error) {
    console.error('发送消息失败:', error)
    if (error.code === 'ECONNABORTED') {
      ElMessage.error('AI响应超时，请稍后重试或检查网络。')
    } else {
      ElMessage.error(error.response?.data?.detail || '发送消息失败')
    }
    // 替换最后一条AI占位为错误提示
    if (conversationHistory.value.length && conversationHistory.value[conversationHistory.value.length - 1].content === 'AI正在思考，请稍候...') {
      conversationHistory.value[conversationHistory.value.length - 1].content = '抱歉，处理您的消息时出现错误。请稍后重试。'
    } else {
      conversationHistory.value.push({
        role: 'assistant',
        content: '抱歉，处理您的消息时出现错误。请稍后重试。'
      })
    }
    // 即使出错也保存对话状态
    if (isActiveSession.value) {
      saveConversationToStorage()
    }
  } finally {
    isLoading.value = false
  }
}

// 滚动到聊天底部
const scrollToBottom = () => {
  if (chatMessages.value) {
    chatMessages.value.scrollTop = chatMessages.value.scrollHeight
  }
}

// 更新图表
const updateCharts = () => {
  // 图表会自动更新，因为使用了计算属性
}

// 查看详情
const viewDetails = (row) => {
  // TODO: 实现查看详情功能
  console.log('查看详情:', row)
}

// 刷新历史记录
const refreshHistory = () => {
  fetchHistory()
  fetchLatestAnalysis()
  fetchHistoricalData()
  fetchLatestSessionSuggestion()
}

// 分页处理
const handleSizeChange = (val) => {
  pageSize.value = val
  fetchHistory()
}

const handleCurrentChange = (val) => {
  currentPage.value = val
  fetchHistory()
}

// 监听LLM分析完成事件
const handleLLMAnalysisComplete = (event) => {
  const data = event.detail
  // 更新对话历史
  conversationHistory.value.push({
    role: 'assistant',
    content: data.analysis.llm_suggestion
  })
  // 更新最新分析结果
  latestAnalysis.value = {
    metrics: {
      rms: data.voice_metrics.rms,
      zcr: data.voice_metrics.zcr,
      model_prediction: data.analysis.model_prediction,
      model_confidence: data.analysis.model_confidence
    },
    created_at: data.timestamp
  }
  // 滚动到底部
  nextTick(() => {
    scrollToBottom()
})
}

const handleFinishConversation = async () => {
  console.log('点击完成对话，当前localStorage:', localStorage.getItem(CONVERSATION_STORAGE_KEY))
  const sessionId = getSessionId()
  if (!sessionId) {
    ElMessage.error('未找到当前会话ID，无法总结诊断建议，请先进行一次有效诊断')
    return
  }
  if (conversationHistory.value.length === 0) {
    ElMessage.warning('请先与AI进行对话')
    return
  }
  // 添加AI正在总结的提示消息
  conversationHistory.value.push({
    role: 'assistant',
    content: 'AI正在总结对话内容，请稍候...'
  })
  await nextTick()
  scrollToBottom()
  loadingSummary.value = true
  try {
    // 单独设置超时时间为40秒
    const res = await api.post(`/llm/summarize/${sessionId}`, conversationHistory.value, { timeout: 40000 })
    // 移除"AI正在总结..."消息
    if (conversationHistory.value.length && 
        conversationHistory.value[conversationHistory.value.length - 1].content === 'AI正在总结对话内容，请稍候...') {
      conversationHistory.value.pop()
    }
    diagnosisSuggestion.value = res.data.summary
    ElMessage.success('诊断建议已生成')
    if (diagnosisSuggestion.value) {
      conversationHistory.value.push({
        role: 'assistant',
        content: '[最终诊断建议] ' + diagnosisSuggestion.value
      })
    }
    
    // 使用新的完成对话方法切换到只读模式
    completeConversation()
    
    console.log('对话已完成，已切换到只读模式')
    refreshHistory()
    await nextTick()
    scrollToBottom()
    // 新增日志
    console.log('完成对话后，页面未刷新，当前URL:', window.location.href, Date.now())
  } catch (e) {
    console.error('诊断建议生成失败:', e)
    
    // 移除"AI正在总结..."消息
    if (conversationHistory.value.length && 
        conversationHistory.value[conversationHistory.value.length - 1].content === 'AI正在总结对话内容，请稍候...') {
      conversationHistory.value.pop()
    }
    
    // 根据错误类型提供更友好的提示
    let errorMsg = '诊断建议生成失败'
    if (e.code === 'ECONNABORTED') {
      errorMsg = '总结超时，大模型处理时间过长，请稍后再试'
    } else if (e.response?.status === 422) {
      errorMsg = '请求参数错误，请检查对话内容格式'
    } else if (e.response?.data?.detail) {
      errorMsg = e.response.data.detail
    }
    
    ElMessage.error(errorMsg)
    
    // 添加错误提示到对话区
    conversationHistory.value.push({
      role: 'assistant',
      content: `[错误] ${errorMsg}，请稍后重试。`
    })
    
    // 保存对话状态到localStorage（即使出错）
    if (isActiveSession.value) {
      saveConversationToStorage()
    }
    
    await nextTick()
    scrollToBottom()
  } finally {
    loadingSummary.value = false
  }
}

const handleVoiceAnalysisStart = () => {
  conversationHistory.value.push({
    role: 'assistant',
    content: 'AI正在分析，请稍候...'
  })
  nextTick(() => scrollToBottom())
}

const handleVoiceAnalysisResult = (event) => {
  const result = event.detail?.result || ''
  // 移除最后一条"AI正在分析..."
  if (conversationHistory.value.length && conversationHistory.value[conversationHistory.value.length - 1].content === 'AI正在分析，请稍候...') {
    conversationHistory.value.pop()
  }
  conversationHistory.value.push({
    role: 'assistant',
    content: result
  })
  nextTick(() => scrollToBottom())
}

onBeforeUnmount(() => {
  window.removeEventListener('llm-analysis-complete', handleLLMAnalysisComplete)
  window.removeEventListener('voice-analysis-start', handleVoiceAnalysisStart)
  window.removeEventListener('voice-analysis-result', handleVoiceAnalysisResult)
  if (ws) ws.close()
  if (isActiveSession.value) {
    saveConversationToStorage()
  }
})

const history = ref([])

// 只读模式下的最新诊断建议
const latestSessionSuggestion = ref({
  diagnosis_suggestion: '',
  created_at: '',
  session_id: null,
  metrics: {
    model_prediction: '',
    model_confidence: 0,
    rms: null,
    zcr: null
  }
})

const fetchLatestSessionSuggestion = async () => {
  try {
    // 获取最新的诊断会话（包含诊断建议和语音指标）
    const response = await api.get('/dashboard/latest-session')
    console.log('获取到的最新诊断建议:', response.data)
    if (response.data) {
      latestSessionSuggestion.value = {
        diagnosis_suggestion: response.data.diagnosis_suggestion || '',
        created_at: response.data.created_at || '',
        session_id: response.data.session_id || null,
        metrics: response.data.metrics || {
          model_prediction: '',
          model_confidence: 0,
          rms: null,
          zcr: null
        }
      }
    }
  } catch (e) {
    console.error('获取最新诊断建议失败:', e)
    latestSessionSuggestion.value = {
      diagnosis_suggestion: '',
      created_at: '',
      session_id: null,
      metrics: {
        model_prediction: '',
        model_confidence: 0,
        rms: null,
        zcr: null
      }
    }
  }
}

// 监听模式切换，进入只读模式时自动拉取
watch(isActiveSession, (val) => {
  if (!val) {
    fetchLatestSessionSuggestion()
  }
}, { immediate: true })

const refreshLatestSuggestion = async () => {
  loadingLatestSuggestion.value = true
  try {
    await fetchLatestSessionSuggestion()
    ElMessage.success('诊断建议已刷新')
  } catch (e) {
    ElMessage.error('刷新失败')
  } finally {
    loadingLatestSuggestion.value = false
  }
}

const renderedDiagnosisSuggestion = computed(() => {
  console.log('diagnosis_suggestion:', latestSessionSuggestion.value.diagnosis_suggestion)
  if (latestSessionSuggestion.value.diagnosis_suggestion) {
    let html = ''
    if (typeof marked.parse === 'function') {
      html = marked.parse(latestSessionSuggestion.value.diagnosis_suggestion)
    } else {
      html = marked(latestSessionSuggestion.value.diagnosis_suggestion)
    }
    console.log('marked 渲染结果:', html)
    return html
  }
  return ''
})

// 添加表格数据计算属性
const mfccTableData = computed(() => {
  if (!latestAnalysis.value || !latestAnalysis.value.metrics) return [];
  
  return Array.from({length: 13}, (_, i) => {
    const index = i + 1;
    const key = `mfcc_${index}`;
    const value = latestAnalysis.value.metrics[key];
    
    return {
      name: `MFCC${index}`,
      value: value !== undefined && value !== null ? value.toFixed(4) : '—',
      description: index === 1 ? '表示语音的总体能量' : `第${index}维梅尔频率倒谱系数`
    };
  });
});

const chromaTableData = computed(() => {
  if (!latestAnalysis.value || !latestAnalysis.value.metrics) return [];
  
  return Array.from({length: 12}, (_, i) => {
    const index = i + 1;
    const key = `chroma_${index}`;
    const value = latestAnalysis.value.metrics[key];
    
    return {
      name: `Chroma${index}`,
      value: value !== undefined && value !== null ? value.toFixed(4) : '—',
      description: `第${index}个色度特征，对应音高特征`
    };
  });
});

// 添加辅助函数，获取MFCC和色度特征值
const getMfccValues = () => {
  if (!latestAnalysis.value || !latestAnalysis.value.metrics) return Array(13).fill(null);
  return Array.from({length: 13}, (_, i) => latestAnalysis.value.metrics[`mfcc_${i+1}`]);
};

const getChromaValues = () => {
  if (!latestAnalysis.value || !latestAnalysis.value.metrics) return Array(12).fill(null);
  return Array.from({length: 12}, (_, i) => latestAnalysis.value.metrics[`chroma_${i+1}`]);
};

// 添加对话框打开事件处理
const handleFeatureDialogOpen = () => {
  // 对话框打开时，等待DOM更新后再初始化图表
  nextTick(() => {
    console.log('特征详情对话框已打开，准备初始化图表')
  })
}

// 添加趋势描述和Y轴标签函数
const getTrendDescription = () => {
  if (trendFilter.value === 'rms_values') {
    return '音量(RMS)反映了声音的能量大小，可用于评估声音的响度变化。';
  } else if (trendFilter.value === 'zcr_values') {
    return '过零率(ZCR)表示信号穿过零点的频率，与声音的频率特性相关，可用于区分浊音和清音。';
  } else if (trendFilter.value === 'confidence_values') {
    return '置信度反映了模型对预测结果的确信程度，越高表示预测越可靠。';
  }
  return '';
};

const getTrendYAxisLabel = () => {
  if (trendFilter.value === 'rms_values') {
    return '音量值';
  } else if (trendFilter.value === 'zcr_values') {
    return '过零率值';
  } else if (trendFilter.value === 'confidence_values') {
    return '置信度 (0-1)';
  }
  return '';
};

// 工具函数
const renderMarkdown = (content) => {
  if (!content) return ''
  return marked.parse(content)
}
</script>

<style scoped>
.dashboard-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #e0f7fa 0%, #b2ebf2 100%);
}

/* 模式指示器样式 */
.mode-indicator {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.main-content {
  padding: 40px 0 20px 0;
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  flex-direction: row;
  align-items: flex-start;
  justify-content: center;
  gap: 40px;
}

.dashboard-left {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 64px;
  margin-top: 0;
}

.dashboard-right {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 32px;
  margin-top: 120px;
}

.overview-section {
  margin-bottom: 0;
  width: 100%;
  display: flex;
  justify-content: center;
}

.main-overview {
  background-color: #f8f9fa;
  border-radius: 18px;
  width: 420px;
  min-width: 420px;
  max-width: 420px;
  min-height: 160px;
  box-shadow: 0 4px 24px #b3e5fc55;
  margin: 0 16px;
}

.trend-card {
  background-color: #f8f9fa;
  border-radius: 18px;
  width: 420px;
  min-width: 420px;
  max-width: 420px;
  min-height: 420px;
  box-shadow: 0 4px 24px #b3e5fc55;
}

/* 快捷操作卡片样式 */
.quick-actions-card {
  background-color: #f8f9fa;
  border-radius: 18px;
  width: 420px;
  min-width: 420px;
  max-width: 420px;
  min-height: 160px;
  box-shadow: 0 4px 24px #b3e5fc55;
}

.quick-actions-header {
  margin-bottom: 16px;
}

.quick-actions-header h2 {
  color: #1976d2;
  font-size: 20px;
  font-weight: 600;
  margin: 0;
}

.quick-actions-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.feature-card {
  margin-bottom: 0;
  background-color: #f8f9fa;
  border-radius: 18px;
  width: 900px;
  min-width: 900px;
  max-width: 900px;
  min-height: 220px;
  box-shadow: 0 4px 24px #b3e5fc55;
}

.ai-diagnosis-card {
  margin-bottom: 0;
  background-color: #f8f9fa;
  border-radius: 18px;
  width: 900px;
  min-width: 900px;
  max-width: 900px;
  min-height: 420px;
  box-shadow: 0 4px 24px #b3e5fc55;
}

.settings-entry {
  text-align: right;
  margin-top: 16px;
  width: 900px;
  min-width: 900px;
  max-width: 900px;
}

@media (max-width: 1300px) {
  .main-content {
    flex-direction: column;
    align-items: center;
    gap: 24px;
  }
  .dashboard-left, .dashboard-right {
    width: 100%;
    min-width: 0;
    align-items: center;
    margin-top: 0;
  }
  .ai-diagnosis-card, .trend-card, .settings-entry, .feature-card {
    width: 98vw;
    min-width: 0;
    max-width: 98vw;
  }
  .main-overview {
    width: 98vw;
    min-width: 0;
    max-width: 98vw;
  }
}

.overview-header {
  margin-bottom: 16px;
  border-bottom: 1px solid #ebeef5;
  padding-bottom: 12px;
}

.overview-header h2 {
  margin: 0;
  font-size: 18px;
  color: #303133;
}

.overview-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px 0;
}

.health-status {
  font-size: 32px;
  font-weight: bold;
  color: #67c23a;
  margin-bottom: 12px;
}

.health-status.danger {
  color: #f56c6c;
}

.health-confidence {
  font-size: 16px;
  color: #909399;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  padding: 16px;
}

.metric-card {
  display: flex;
  flex-direction: column;
  padding: 12px;
  background: #f5f5f5;
  border-radius: 4px;
}

.metric-label {
  font-size: 14px;
  color: #666;
  margin-bottom: 4px;
}

.metric-value {
  font-size: 18px;
  font-weight: bold;
  color: #2196f3;
}

.diagnosis-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  border-bottom: 1px solid #ebeef5;
  padding-bottom: 12px;
}

.diagnosis-header h2 {
  margin: 0;
  font-size: 18px;
  color: #303133;
}

.diagnosis-actions {
  display: flex;
  gap: 8px;
}

.chat-container {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  padding: 20px;
}

.chat-title {
  margin-bottom: 16px;
}

.chat-title h3 {
  margin: 0 0 8px 0;
  font-size: 16px;
  color: #303133;
}

.chat-subtitle {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
  margin-bottom: 0;
}

.chat-title-actions {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 8px;
}

.chat-messages {
  height: 400px;
  overflow-y: auto;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
  margin-bottom: 16px;
  display: flex;
  flex-direction: column;
}

.chat-empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #909399;
}

.message {
  margin-bottom: 12px;
  padding: 12px 16px;
  border-radius: 8px;
  max-width: 80%;
  word-break: break-word;
}

.message.user {
  background-color: #ecf5ff;
  margin-left: auto;
  border-bottom-right-radius: 2px;
  align-self: flex-end;
}

.message.assistant {
  background-color: #fff;
  border: 1px solid #ebeef5;
  margin-right: auto;
  border-bottom-left-radius: 2px;
  align-self: flex-start;
}

.message-content {
  white-space: pre-wrap;
}

.chat-input {
  margin-bottom: 16px;
}

.chat-summary-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
}

.typing-indicator {
  display: flex;
  align-items: center;
}

.typing-indicator span {
  height: 8px;
  width: 8px;
  background-color: #909399;
  border-radius: 50%;
  display: inline-block;
  margin: 0 2px;
  animation: typing 1s infinite ease-in-out;
}

.typing-indicator span:nth-child(1) {
  animation-delay: 0s;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0% { transform: scale(1); }
  50% { transform: scale(1.5); }
  100% { transform: scale(1); }
}

.chart-container {
  height: 400px;
  padding: 16px;
  background-color: #fff;
  border-radius: 4px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.pagination-container {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

.feature-item {
  background-color: #f5f7fa;
  border-radius: 4px;
  padding: 10px;
  text-align: center;
}

.feature-label {
  font-size: 14px;
  color: #606266;
  margin-bottom: 5px;
}

.feature-value {
  font-size: 20px;
  font-weight: bold;
  color: #409EFF;
}

.feature-tabs {
  height: 600px;
}

.feature-chart {
  height: 300px;
  margin-bottom: 20px;
}

.feature-chart-grid {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
}

.feature-chart-item {
  flex: 1;
  background-color: #f5f7fa;
  border-radius: 4px;
  padding: 20px;
}

.feature-description {
  background-color: #f5f7fa;
  border-radius: 4px;
  padding: 20px;
}

.feature-detail-list {
  margin-top: 20px;
}

.trend-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  border-bottom: 1px solid #ebeef5;
  padding-bottom: 12px;
}

.trend-header h2 {
  margin: 0;
  font-size: 18px;
  color: #303133;
}

.trend-description {
  margin-bottom: 16px;
  color: #606266;
  font-size: 14px;
  background-color: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
}

.feature-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  border-bottom: 1px solid #ebeef5;
  padding-bottom: 12px;
}

.feature-header h2 {
  margin: 0;
  font-size: 18px;
  color: #303133;
}

.feature-description {
  margin-bottom: 16px;
  color: #606266;
  font-size: 14px;
}

.feature-brief {
  background-color: #fff;
  border-radius: 4px;
  padding: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.feature-item {
  background-color: #f5f7fa;
  border-radius: 4px;
  padding: 16px;
  text-align: center;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.feature-label {
  font-size: 14px;
  color: #606266;
  margin-bottom: 8px;
}

.feature-value {
  font-size: 20px;
  font-weight: bold;
  color: #409EFF;
}

/* 只读模式样式 */
.chat-subtitle {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
  margin-bottom: 0;
}

.chat-title-actions {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 8px;
}

.diagnosis-header-readonly {
  margin-bottom: 12px;
}

.diagnosis-label {
  font-weight: bold;
  margin-right: 8px;
}

.diagnosis-value {
  font-weight: bold;
  font-size: 16px;
  color: #67c23a;
}

.diagnosis-value.danger {
  color: #f56c6c;
}

.diagnosis-confidence {
  font-size: 14px;
  color: #909399;
  margin-left: 8px;
}

.diagnosis-content {
  margin-bottom: 16px;
  white-space: pre-wrap;
  line-height: 1.5;
}

.diagnosis-suggestion-title {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
  margin-top: 0;
  margin-bottom: 8px;
}

.diagnosis-suggestion-text {
  background: #f6f8fa;
  border-radius: 8px;
  padding: 18px 22px;
  margin: 16px 0;
  font-size: 1.1em;
  color: #222;
  line-height: 1.7;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  word-break: break-word;
}

.diagnosis-suggestion-text h1,
.diagnosis-suggestion-text h2,
.diagnosis-suggestion-text h3 {
  margin-top: 1em;
  margin-bottom: 0.5em;
  font-weight: bold;
}

.diagnosis-suggestion-text ul,
.diagnosis-suggestion-text ol {
  margin: 0.5em 0 0.5em 1.5em;
}

.diagnosis-suggestion-text code {
  background: #f3f3f3;
  border-radius: 4px;
  padding: 2px 6px;
  font-size: 0.95em;
  color: #c7254e;
}

.diagnosis-suggestion-text pre {
  background: #f3f3f3;
  border-radius: 4px;
  padding: 10px;
  overflow-x: auto;
  font-size: 0.95em;
  color: #333;
}

.metrics-summary {
  background-color: #f5f7fa;
  border-radius: 4px;
  padding: 12px;
  margin-top: 16px;
}

.metrics-title {
  font-weight: bold;
  margin-bottom: 8px;
  color: #606266;
}

.metrics-grid-readonly {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

.metric-item-readonly {
  display: flex;
  flex-direction: column;
  padding: 8px;
  background-color: #ffffff;
  border-radius: 4px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.metric-label-readonly {
  font-size: 13px;
  color: #909399;
  margin-bottom: 4px;
}

.metric-value-readonly {
  font-size: 16px;
  font-weight: bold;
  color: #409EFF;
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 1.2s;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style> 