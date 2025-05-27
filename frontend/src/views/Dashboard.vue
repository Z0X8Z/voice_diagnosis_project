<template>
  <div class="dashboard-container">
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

    <div class="main-content">
      <!-- 最新分析结果 -->
      <div class="latest-analysis">
        <h2>最新分析结果</h2>
        <div class="metrics-grid">
          <div class="metric-card">
            <h3>音量 (RMS)</h3>
            <p>{{ latestAnalysis.metrics.rms?.toFixed(2) || '暂无数据' }}</p>
          </div>
          <div class="metric-card">
            <h3>过零率 (ZCR)</h3>
            <p>{{ latestAnalysis.metrics.zcr?.toFixed(2) || '暂无数据' }}</p>
          </div>
          <div class="metric-card">
            <h3>预测结果</h3>
            <p>{{ latestAnalysis.metrics.model_prediction || '暂无数据' }}</p>
            </div>
          <div class="metric-card">
            <h3>置信度</h3>
            <p>{{ (latestAnalysis.metrics.model_confidence * 100).toFixed(1) }}%</p>
            </div>
                </div>
                </div>

      <!-- 模型对话窗口 -->
      <div class="chat-container">
        <h2>AI 助手对话</h2>
        <div class="chat-messages" ref="chatMessages">
          <div v-if="conversationHistory.length === 0" class="chat-empty-state">
            <p>您可以向AI助手询问关于您的语音健康分析结果的问题</p>
          </div>
          <div 
            v-for="(message, index) in conversationHistory" 
            :key="index" 
            class="message" 
            :class="message.role"
          >
            <div class="message-content">{{ message.content }}</div>
          </div>
          <div v-if="isLoading" class="message assistant loading">
            <div class="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </div>
        <div class="chat-input">
          <el-input
            v-model="userMessage"
            placeholder="请输入您的问题..."
            :disabled="isLoading"
            @keyup.enter="sendMessage"
          >
            <template #append>
              <el-button :disabled="isLoading" @click="sendMessage">
                <el-icon><Position /></el-icon>
                发送
              </el-button>
            </template>
          </el-input>
        </div>
        <div class="chat-summary-actions" style="margin-top: 16px;">
          <el-button type="success" :loading="loadingSummary" @click="handleFinishConversation" style="width: 120px;">
            完成了
          </el-button>
        </div>
        <div v-if="diagnosisSuggestion" class="diagnosis-suggestion" style="margin-top: 20px; background: #f6ffed; border: 1px solid #b7eb8f; border-radius: 6px; padding: 16px;">
          <h3 style="color: #52c41a;">诊断建议</h3>
          <p style="white-space: pre-line;">{{ diagnosisSuggestion }}</p>
        </div>
      </div>

      <!-- 历史趋势图表 -->
      <div class="historical-trends">
        <h2>历史趋势</h2>
        <div class="chart-container">
          <LineChart
            :chart-data="{
              labels: historicalData.dates,
              datasets: [
                {
                  label: '音量 (RMS)',
                  data: historicalData.rms_values,
                  borderColor: '#4CAF50',
                  fill: false
                },
                {
                  label: '过零率 (ZCR)',
                  data: historicalData.zcr_values,
                  borderColor: '#2196F3',
                  fill: false
                },
                {
                  label: '置信度',
                  data: historicalData.confidence_values,
                  borderColor: '#FFC107',
                  fill: false
                }
              ]
            }"
            :options="{
              responsive: true,
              maintainAspectRatio: false,
              scales: {
                y: {
                  beginAtZero: true
                }
              }
            }"
          />
                </div>
            </div>

      <!-- 历史记录表格 -->
      <div class="history-table">
        <h2>历史记录</h2>
        <el-table :data="history" style="width: 100%">
          <el-table-column prop="created_at" label="日期" width="180">
              <template #default="scope">
              {{ new Date(scope.row.created_at).toLocaleString() }}
              </template>
            </el-table-column>
          <el-table-column prop="prediction" label="预测结果" />
            <el-table-column prop="confidence" label="置信度">
              <template #default="scope">
              {{ (scope.row.confidence * 100).toFixed(1) }}%
              </template>
            </el-table-column>
          <el-table-column prop="llm_suggestion" label="AI建议" />
          </el-table>
          </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Position } from '@element-plus/icons-vue'
import logo from '../assets/logo.png'
import { useUserStore } from '../stores/user'
import { useApi } from '../composables/useApi'
import LineChart from '../components/LineChart.vue'
import { useWebSocket } from '../composables/useWebSocket'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const api = useApi()
const { isConnected } = useWebSocket()

const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const activeIndex = computed(() => route.path)

// 最新分析结果
const latestAnalysis = ref({
  metrics: {
    rms: 0,
    zcr: 0,
    model_prediction: '',
    model_confidence: 0
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

// 获取最新分析结果
const fetchLatestAnalysis = async () => {
  try {
    const response = await api.get('/dashboard/latest')
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
  } catch (error) {
    console.error('获取历史记录失败:', error)
    ElMessage.error('获取历史记录失败')
  } finally {
    loading.value = false
  }
}

// 获取 session_id
const getSessionId = () => {
  // 优先取根节点 session_id，否则取 metrics.session_id
  return latestAnalysis.value?.session_id || latestAnalysis.value?.metrics?.session_id
}

// 发送消息到 LLM
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
    await nextTick()
    scrollToBottom()
    const sessionId = getSessionId()
    if (!sessionId) {
      throw new Error('未找到当前会话ID')
    }
    // 使用新的follow-up端点发送问题
    const response = await api.post(`/llm/follow-up/${sessionId}`, {
      question: message
    })
    // 使用返回的对话历史更新本地状态
    if (response.data.conversation_history) {
      conversationHistory.value = response.data.conversation_history
    } else {
      // 兼容旧接口，如果没有返回完整历史，则添加回复
    conversationHistory.value.push({
      role: 'assistant',
        content: response.data.response
    })
    }
    await nextTick()
    scrollToBottom()
  } catch (error) {
    console.error('发送消息失败:', error)
    ElMessage.error(error.response?.data?.detail || '发送消息失败')
    conversationHistory.value.push({
      role: 'assistant',
      content: '抱歉，处理您的消息时出现错误。请稍后重试。'
    })
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

// 用户菜单处理
const handleCommand = (command) => {
  if (command === 'logout') {
    userStore.logout()
    ElMessage.success('已退出登录')
    router.push('/login')
  } else if (command === 'profile') {
    router.push('/settings')
  }
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
  const sessionId = getSessionId()
  if (!sessionId) {
    ElMessage.error('未找到当前会话ID，无法总结诊断建议')
    return
  }
  loadingSummary.value = true
  try {
    // 调用新的/llm/summarize端点来总结对话
    const res = await api.post(`/llm/summarize/${sessionId}`)
    diagnosisSuggestion.value = res.data.summary
    ElMessage.success('诊断建议已生成')
    conversationHistory.value.push({
      role: 'assistant',
      content: '[最终诊断建议] ' + res.data.summary
    })
    // 刷新历史记录，显示最新的诊断建议
    refreshHistory()
    await nextTick()
    scrollToBottom()
  } catch (e) {
    console.error('诊断建议生成失败:', e)
    ElMessage.error(e.response?.data?.detail || '诊断建议生成失败')
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

onMounted(() => {
  refreshHistory()
  window.addEventListener('llm-analysis-complete', handleLLMAnalysisComplete)
  window.addEventListener('voice-analysis-start', handleVoiceAnalysisStart)
  window.addEventListener('voice-analysis-result', handleVoiceAnalysisResult)
})

onBeforeUnmount(() => {
  window.removeEventListener('llm-analysis-complete', handleLLMAnalysisComplete)
  window.removeEventListener('voice-analysis-start', handleVoiceAnalysisStart)
  window.removeEventListener('voice-analysis-result', handleVoiceAnalysisResult)
})

const history = ref([])
</script>

<style scoped>
.dashboard-container {
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
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.latest-analysis,
.historical-trends,
.history-table {
  margin-bottom: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
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

.chat-container {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
  padding: 20px;
}

.chat-messages {
  height: 400px;
  overflow-y: auto;
  padding: 16px;
  background: #f5f5f5;
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
  color: #999;
  font-style: italic;
}

.message {
  margin-bottom: 12px;
  padding: 12px 16px;
  border-radius: 8px;
  max-width: 80%;
  word-break: break-word;
}

.message.user {
  background-color: #e3f2fd;
  margin-left: auto;
  border-bottom-right-radius: 2px;
  align-self: flex-end;
}

.message.assistant {
  background-color: #fff;
  border: 1px solid #e0e0e0;
  margin-right: auto;
  border-bottom-left-radius: 2px;
  align-self: flex-start;
}

.message-content {
  white-space: pre-wrap;
}

.chat-input {
  padding: 0;
}

.typing-indicator {
  display: flex;
  align-items: center;
}

.typing-indicator span {
  height: 8px;
  width: 8px;
  background-color: #999;
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
}

.pagination-container {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style> 