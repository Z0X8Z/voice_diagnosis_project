import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'

// 仪表盘模式管理
export function useDashboardMode() {
  const route = useRoute()
  const storageVersion = ref(0) // 用于触发响应式更新
  
  // 常量定义
  const CONVERSATION_STORAGE_KEY = 'voice_analysis_conversation'
  const SESSION_STATE_KEY = 'dashboard_session_state'
  
  // 仪表盘模式枚举
  const DASHBOARD_MODES = {
    INTERACTIVE: 'interactive',  // 主动分析模式 - 可对话
    READ_ONLY: 'read_only'      // 只读模式 - 仅查看
  }
  
  /**
   * 清理过期或无效的会话状态
   */
  const cleanupExpiredSessions = () => {
    try {
      const sessionState = localStorage.getItem(SESSION_STATE_KEY)
      if (sessionState) {
        const state = JSON.parse(sessionState)
        
        // 如果会话已完成超过24小时，清理相关数据
        if (state.isCompleted && state.completedTime) {
          const now = Date.now()
          const completedTime = state.completedTime
          const hoursSinceCompletion = (now - completedTime) / (1000 * 60 * 60)
          
          if (hoursSinceCompletion > 24) {
            localStorage.removeItem(SESSION_STATE_KEY)
            localStorage.removeItem(CONVERSATION_STORAGE_KEY)
            console.log('✅ 已清理过期的会话状态')
            return true
          }
        }
        
        // 如果会话开始超过24小时但未完成，也清理掉
        if (state.startTime && !state.isCompleted) {
          const now = Date.now()
          const startTime = state.startTime
          const hoursSinceStart = (now - startTime) / (1000 * 60 * 60)
          
          if (hoursSinceStart > 24) {
            localStorage.removeItem(SESSION_STATE_KEY)
            localStorage.removeItem(CONVERSATION_STORAGE_KEY)
            console.log('✅ 已清理超时未完成的会话状态')
            return true
          }
        }
      }
    } catch (error) {
      console.warn('清理会话状态时出错:', error)
      // 如果解析出错，直接清理
      localStorage.removeItem(SESSION_STATE_KEY)
      localStorage.removeItem(CONVERSATION_STORAGE_KEY)
      return true
    }
    
    return false
  }

  /**
   * 判断当前仪表盘模式
   * @returns {string} 'interactive' 或 'read_only'
   */
  const currentMode = computed(() => {
    storageVersion.value // 依赖版本号确保响应式
    
    // 0. 首先清理过期的会话状态
    const cleaned = cleanupExpiredSessions()
    if (cleaned) {
      storageVersion.value++ // 触发重新计算
    }
    
    // 1. 检查是否从语音上传跳转而来
    if (route.query.fromUpload) {
      return DASHBOARD_MODES.INTERACTIVE
    }
    
    // 2. 如果不是从上传跳转，而是用户主动访问，检查是否有已完成的会话
    // 如果有已完成的会话，直接清理并进入只读模式
    try {
      const sessionState = localStorage.getItem(SESSION_STATE_KEY)
      if (sessionState) {
        const state = JSON.parse(sessionState)
        if (state.isCompleted) {
          // 用户主动访问且会话已完成，清理数据进入只读模式
          localStorage.removeItem(SESSION_STATE_KEY)
          localStorage.removeItem(CONVERSATION_STORAGE_KEY)
          console.log('✅ 检测到用户主动访问dashboard，已清理完成的会话状态')
          storageVersion.value++
          return DASHBOARD_MODES.READ_ONLY
        }
        // 如果会话活跃且未完成，则是交互模式
        else if (state.isActive && !state.isCompleted) {
          return DASHBOARD_MODES.INTERACTIVE
        }
      }
    } catch (error) {
      console.warn('解析会话状态失败:', error)
      // 解析失败，清理数据
      localStorage.removeItem(SESSION_STATE_KEY)
      localStorage.removeItem(CONVERSATION_STORAGE_KEY)
      storageVersion.value++
    }
    
    // 3. 检查localStorage中是否有对话历史（此时应该是未完成的会话）
    try {
      const conversationHistory = localStorage.getItem(CONVERSATION_STORAGE_KEY)
      if (conversationHistory) {
        const history = JSON.parse(conversationHistory)
        if (Array.isArray(history) && history.length > 0) {
          return DASHBOARD_MODES.INTERACTIVE
        }
      }
    } catch (error) {
      console.warn('解析对话历史失败:', error)
    }
    
    // 4. 默认为只读模式
    return DASHBOARD_MODES.READ_ONLY
  })
  
  /**
   * 是否为主动分析模式
   */
  const isInteractiveMode = computed(() => {
    return currentMode.value === DASHBOARD_MODES.INTERACTIVE
  })
  
  /**
   * 是否为只读模式
   */
  const isReadOnlyMode = computed(() => {
    return currentMode.value === DASHBOARD_MODES.READ_ONLY
  })
  
  /**
   * 功能权限检查
   */
  const permissions = computed(() => {
    const isInteractive = isInteractiveMode.value
    
    return {
      // 对话功能
      canChat: isInteractive,
      canSendMessage: isInteractive,
      canCompleteConversation: isInteractive,
      
      // 数据展示
      canViewAcousticFeatures: isInteractive,
      canViewRealtimeKPI: isInteractive,
      canViewHistoricalData: true,
      
      // 只读功能
      canViewLatestSuggestion: true,  // 两种模式都可以查看
      canRefreshSuggestion: !isInteractive // 只有只读模式才需要手动刷新
    }
  })
  
  /**
   * 激活主动分析模式
   * @param {Object} options 配置选项
   */
  const activateInteractiveMode = (options = {}) => {
    const state = {
      isActive: true,
      isCompleted: false,
      startTime: Date.now(),
      sessionId: options.sessionId || null,
      fromUpload: options.fromUpload || false
    }
    
    localStorage.setItem(SESSION_STATE_KEY, JSON.stringify(state))
    storageVersion.value++
    
    console.log('✅ 已激活主动分析模式', state)
  }
  
  /**
   * 完成对话，切换到只读模式
   */
  const completeConversation = () => {
    // 清除对话历史
    localStorage.removeItem(CONVERSATION_STORAGE_KEY)
    
    // 更新会话状态
    try {
      const sessionState = localStorage.getItem(SESSION_STATE_KEY)
      if (sessionState) {
        const state = JSON.parse(sessionState)
        state.isCompleted = true
        state.completedTime = Date.now()
        localStorage.setItem(SESSION_STATE_KEY, JSON.stringify(state))
      }
    } catch (error) {
      // 如果没有状态，创建一个已完成的状态
      const state = {
        isActive: false,
        isCompleted: true,
        completedTime: Date.now()
      }
      localStorage.setItem(SESSION_STATE_KEY, JSON.stringify(state))
    }
    
    storageVersion.value++
    console.log('✅ 对话已完成，切换到只读模式')
  }
  
  /**
   * 重置到只读模式
   */
  const resetToReadOnlyMode = () => {
    localStorage.removeItem(CONVERSATION_STORAGE_KEY)
    localStorage.removeItem(SESSION_STATE_KEY)
    storageVersion.value++
    
    console.log('✅ 已重置到只读模式')
  }
  
  /**
   * 手动刷新模式状态
   */
  const refreshMode = () => {
    storageVersion.value++
  }
  
  /**
   * 获取模式描述文本
   */
  const getModeDescription = () => {
    if (isInteractiveMode.value) {
      return {
        title: '实时分析模式',
        description: '您可以查看声学特征分析并与AI助手对话',
        color: 'success'
      }
    } else {
      return {
        title: '历史查看模式',
        description: '显示最近一次的诊断建议，点击"开始新的分析"进行语音诊断',
        color: 'info'
      }
    }
  }
  
  return {
    // 模式状态
    currentMode,
    isInteractiveMode,
    isReadOnlyMode,
    permissions,
    
    // 模式管理
    activateInteractiveMode,
    completeConversation,
    resetToReadOnlyMode,
    refreshMode,
    cleanupExpiredSessions,
    
    // 工具函数
    getModeDescription,
    
    // 常量
    DASHBOARD_MODES
  }
} 