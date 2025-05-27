import { ref, onMounted, onUnmounted } from 'vue'
import { useUserStore } from '../stores/user'

export function useWebSocket() {
    const ws = ref(null)
    const isConnected = ref(false)
    const userStore = useUserStore()

    const connect = () => {
        const userId = userStore.user?.id
        if (!userId) return

        const wsUrl = `ws://${window.location.host}/api/ws/${userId}`
        ws.value = new WebSocket(wsUrl)

        ws.value.onopen = () => {
            console.log('WebSocket连接已建立')
            isConnected.value = true
        }

        ws.value.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data)
                handleMessage(message)
            } catch (error) {
                console.error('处理WebSocket消息失败:', error)
            }
        }

        ws.value.onclose = () => {
            console.log('WebSocket连接已关闭')
            isConnected.value = false
            // 尝试重新连接
            setTimeout(connect, 3000)
        }

        ws.value.onerror = (error) => {
            console.error('WebSocket错误:', error)
            isConnected.value = false
        }
    }

    const handleMessage = (message) => {
        switch (message.type) {
            case 'llm_analysis_complete':
                // 处理LLM分析完成的消息
                const { data } = message
                // 更新仪表盘数据
                updateDashboard(data)
                break
            default:
                console.log('未知消息类型:', message.type)
        }
    }

    const updateDashboard = (data) => {
        // 这里可以触发事件或更新状态
        // 例如：使用事件总线或状态管理
        window.dispatchEvent(new CustomEvent('llm-analysis-complete', {
            detail: data
        }))
    }

    onMounted(() => {
        connect()
    })

    onUnmounted(() => {
        if (ws.value) {
            ws.value.close()
        }
    })

    return {
        isConnected
    }
} 