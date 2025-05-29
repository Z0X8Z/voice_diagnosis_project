<template>
  <div class="chart-wrapper">
    <canvas ref="chartCanvas"></canvas>
  </div>
</template>

<script>
import { ref, onMounted, watch, nextTick } from 'vue'
import Chart from 'chart.js/auto'

export default {
  name: 'LineChart',
  props: {
    // 支持两种使用方式：
    // 1. 传统方式：data, labels, title
    data: {
      type: Array,
      default: () => []
    },
    labels: {
      type: Array,
      default: () => []
    },
    title: {
      type: String,
      default: ''
    },
    // 2. Chart.js 原生方式：chartData, options
    chartData: {
      type: Object,
      default: null
    },
    options: {
      type: Object,
      default: () => ({})
    }
  },
  
  setup(props) {
    const chartCanvas = ref(null)
    let chart = null
    
    const createChart = async () => {
      try {
        if (!chartCanvas.value) {
          console.warn('Canvas元素未准备好，等待下一帧')
          return
        }
        
        // 确保DOM已更新
        await nextTick()
        
        if (chart) {
          chart.destroy()
        }
        
        const ctx = chartCanvas.value.getContext('2d')
        if (!ctx) {
          console.error('无法获取canvas上下文')
          return
        }
        
        // 使用 chartData 和 options（如果提供）
        if (props.chartData) {
          // 确保数据有效
          const validData = {
            ...props.chartData,
            datasets: props.chartData.datasets?.map(dataset => ({
              ...dataset,
              // 过滤掉无效数据点
              data: dataset.data?.map(value => 
                value === undefined || value === null || isNaN(value) ? null : value
              ) || []
            })) || []
          }
          
          chart = new Chart(ctx, {
            type: 'line',
            data: validData,
            options: {
              ...props.options,
              responsive: true,
              maintainAspectRatio: false,
              spanGaps: true, // 跨越空值绘制线条
              plugins: {
                ...(props.options?.plugins || {}),
                tooltip: {
                  ...(props.options?.plugins?.tooltip || {}),
                  callbacks: {
                    ...(props.options?.plugins?.tooltip?.callbacks || {}),
                    label: props.options?.plugins?.tooltip?.callbacks?.label || function(context) {
                      const label = context.dataset.label || '';
                      const value = context.parsed.y;
                      return value !== null ? `${label}: ${value}` : `${label}: 无数据`;
                    }
                  }
                }
              }
            }
          })
          return
        }
        
        // 使用传统方式
        const validData = props.data?.map(value => 
          value === undefined || value === null || isNaN(value) ? null : value
        ) || []
        
        chart = new Chart(ctx, {
          type: 'line',
          data: {
            labels: props.labels,
            datasets: [{
              label: props.title,
              data: validData,
              borderColor: '#1976d2',
              backgroundColor: 'rgba(25, 118, 210, 0.1)',
              tension: 0.4,
              fill: true
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            spanGaps: true, // 跨越空值绘制线条
            plugins: {
              legend: {
                display: !!props.title
              },
              tooltip: {
                callbacks: {
                  label: function(context) {
                    const value = context.parsed.y;
                    return value !== null ? `${props.title}: ${value}` : `${props.title}: 无数据`;
                  }
                }
              }
            },
            scales: {
              y: {
                beginAtZero: true
              }
            }
          }
        })
      } catch (error) {
        console.error('创建图表时出错:', error)
      }
    }
    
    watch(() => props.data, () => {
      if (!props.chartData) {
        nextTick(() => createChart())
      }
    }, { deep: true })
    
    watch(() => props.labels, () => {
      if (!props.chartData) {
        nextTick(() => createChart())
      }
    }, { deep: true })
    
    watch(() => props.chartData, () => {
      if (props.chartData) {
        nextTick(() => createChart())
      }
    }, { deep: true })
    
    watch(() => props.options, () => {
      if (props.chartData) {
        nextTick(() => createChart())
      }
    }, { deep: true })
    
    onMounted(() => {
      nextTick(() => createChart())
    })
    
    return {
      chartCanvas
    }
  }
}
</script>

<style scoped>
.chart-wrapper {
  width: 100%;
  height: 100%;
  position: relative;
}
</style> 