<template>
  <div class="chart-wrapper">
    <canvas ref="chartCanvas"></canvas>
  </div>
</template>

<script>
import { ref, onMounted, watch } from 'vue'
import Chart from 'chart.js/auto'

export default {
  name: 'LineChart',
  props: {
    data: {
      type: Array,
      required: true
    },
    labels: {
      type: Array,
      required: true
    },
    title: {
      type: String,
      default: ''
    }
  },
  
  setup(props) {
    const chartCanvas = ref(null)
    let chart = null
    
    const createChart = () => {
      if (chart) {
        chart.destroy()
      }
      
      const ctx = chartCanvas.value.getContext('2d')
      chart = new Chart(ctx, {
        type: 'line',
        data: {
          labels: props.labels,
          datasets: [{
            label: props.title,
            data: props.data,
            borderColor: '#1976d2',
            backgroundColor: 'rgba(25, 118, 210, 0.1)',
            tension: 0.4,
            fill: true
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: !!props.title
            }
          },
          scales: {
            y: {
              beginAtZero: true
            }
          }
        }
      })
    }
    
    watch(() => props.data, () => {
      createChart()
    }, { deep: true })
    
    watch(() => props.labels, () => {
      createChart()
    }, { deep: true })
    
    onMounted(() => {
      createChart()
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
  height: 200px;
  position: relative;
}
</style> 