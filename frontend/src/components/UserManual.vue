<template>
  <div v-if="shouldShowManual" class="user-manual-container">
    <el-button 
      type="primary" 
      class="floating-help-button" 
      circle 
      size="large" 
      @click="showUserManual = true"
    >
      <el-icon><Help /></el-icon>
    </el-button>

    <!-- 用户手册弹窗 -->
    <el-dialog
      v-model="showUserManual"
      title="声肺康智能分析系统 - 用户使用手册"
      width="80%"
    >
      <div class="user-manual-content">
        <el-tabs>
          <el-tab-pane label="快速入门">
            <h3>欢迎使用声肺康智能分析系统</h3>
            <p>本系统通过分析您的声音特征来评估肺部健康状况，以下是使用步骤：</p>
            
            <div class="manual-section">
              <h4>1. 录制语音</h4>
              <ul>
                <li>在首页点击"开始新的语音分析"按钮</li>
                <li>按照提示，点击麦克风按钮开始录音</li>
                <li>对着麦克风说一段10-15秒的话，或阅读屏幕上的文字</li>
                <li>点击按钮结束录音，系统会自动评估音频质量</li>
                <li>音频质量合格后，点击"开始分析"按钮上传声音</li>
              </ul>
            </div>
            
            <div class="manual-section">
              <h4>2. 查看分析结果</h4>
              <ul>
                <li>上传成功后，系统会自动跳转到仪表盘页面</li>
                <li>在"健康结论"部分查看您的诊断结果</li>
                <li>点击疾病名称旁的信息图标可查看详细说明</li>
                <li>在"AI诊断建议"部分查看更详细的健康分析</li>
              </ul>
            </div>
            
            <div class="manual-section">
              <h4>3. 与AI助手交流</h4>
              <ul>
                <li>在对话模式下，您可以向AI助手提问</li>
                <li>询问有关您的诊断结果的详细信息</li>
                <li>获取针对性的健康改善建议</li>
                <li>完成对话后，点击"完成对话"按钮生成最终诊断建议</li>
              </ul>
            </div>
          </el-tab-pane>
          
          <el-tab-pane label="功能详解">
            <div class="manual-section">
              <h4>健康结论</h4>
              <p>显示AI模型对您声音的诊断结果，包括：</p>
              <ul>
                <li><b>诊断结果</b>：根据声音特征预测的健康状况</li>
                <li><b>置信度</b>：反映上传音频质量评分，分数越低表示音频质量越差，分析结果越不可信</li>
              </ul>
            </div>
            
            <div class="manual-section">
              <h4>历史趋势分析</h4>
              <p>展示您历史检测数据的变化趋势，可查看：</p>
              <ul>
                <li><b>音量(RMS)</b>：反映声音的能量大小</li>
                <li><b>过零率(ZCR)</b>：与声音的频率特性相关</li>
                <li><b>置信度</b>：音频质量评分的历史变化</li>
                <li><b>诊断结果</b>：健康状况的历史变化</li>
              </ul>
            </div>
            
            <div class="manual-section">
              <h4>声学特征分析</h4>
              <p>展示详细的声学特征数据，包括：</p>
              <ul>
                <li><b>MFCC特征</b>：梅尔频率倒谱系数，反映声音的音色特征</li>
                <li><b>色度特征</b>：反映声音的音高分布</li>
                <li><b>时域特征</b>：包括音量(RMS)和过零率(ZCR)</li>
              </ul>
              <p>点击"查看详细特征"可获取更多声学特征信息。</p>
            </div>
            
            <div class="manual-section">
              <h4>AI诊断建议</h4>
              <p>AI助手基于您的声音特征给出的健康建议：</p>
              <ul>
                <li>在对话模式下，您可以与AI助手交流</li>
                <li>询问有关诊断结果的更多信息</li>
                <li>获取针对性的健康改善建议</li>
                <li>完成对话后，系统会生成最终诊断建议</li>
              </ul>
            </div>
          </el-tab-pane>
          
          <el-tab-pane label="注意事项">
            <div class="manual-section warning-section">
              <h4>医疗免责声明</h4>
              <p>声肺康智能分析系统提供的分析结果仅供参考，不能替代专业医生的诊断。如有健康问题，请咨询专业医疗机构。</p>
            </div>
            
            <div class="manual-section">
              <h4>录音质量建议</h4>
              <ul>
                <li>在安静环境下录音</li>
                <li>关闭风扇、空调等噪音源</li>
                <li>距离麦克风10-15厘米</li>
                <li>保持正常语速和音量</li>
                <li>录音时间最好在10-15秒</li>
              </ul>
            </div>
            
            <div class="manual-section">
              <h4>数据安全</h4>
              <p>我们重视您的隐私：</p>
              <ul>
                <li>您的语音数据仅用于健康分析</li>
                <li>所有数据均经过加密存储</li>
                <li>您可以随时删除您的历史数据</li>
              </ul>
            </div>
            
            <div class="manual-section">
              <h4>最佳使用频率</h4>
              <p>为获得最佳跟踪效果，建议：</p>
              <ul>
                <li>健康人群：每月1-2次</li>
                <li>有呼吸系统疾病：每周1-2次</li>
                <li>正在康复中：可每2-3天一次</li>
              </ul>
            </div>
          </el-tab-pane>
          
          <el-tab-pane label="常见问题">
            <div class="manual-section">
              <h4>常见问题解答</h4>
              
              <div class="faq-item">
                <h5>Q: 为什么我的录音提示质量不佳？</h5>
                <p>A: 可能是环境噪音过大、麦克风距离不适当或音量过小。请确保在安静环境中，距离麦克风10-15厘米，并以正常音量说话。</p>
              </div>
              
              <div class="faq-item">
                <h5>Q: 分析结果的"置信度"是什么意思？</h5>
                <p>A: 置信度反映上传音频的质量评分，分数越低表示音频质量越差，分析结果越不可信。为获得准确结果，请尽量保证录音质量。</p>
              </div>
              
              <div class="faq-item">
                <h5>Q: 系统能识别哪些肺部健康问题？</h5>
                <p>A: 目前系统可识别健康、哮喘、肺炎、支气管炎和慢阻肺(COPD)等常见呼吸系统状况。</p>
              </div>
              
              <div class="faq-item">
                <h5>Q: 我可以导出我的分析历史吗？</h5>
                <p>A: 目前暂不支持导出功能，未来版本将添加数据导出功能。</p>
              </div>
              
              <div class="faq-item">
                <h5>Q: 如何删除我的历史数据？</h5>
                <p>A: 请前往"设置"页面，在账户设置中找到"删除历史数据"选项。</p>
              </div>
              
              <div class="faq-item">
                <h5>Q: 我的诊断结果显示异常，但我感觉很健康，这正常吗？</h5>
                <p>A: 系统提供的是参考性结果，可能受多种因素影响。如您对结果有疑问，建议：1)重新录制高质量音频；2)连续多次测试比较结果；3)必要时咨询医生。</p>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button type="primary" @click="showUserManual = false">我知道了</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { Help } from '@element-plus/icons-vue'

const showUserManual = ref(false)
const route = useRoute()

// 在登录、注册和个人设置页面不显示
const excludedRoutes = ['/login', '/register', '/settings']

const shouldShowManual = computed(() => {
  return !excludedRoutes.includes(route.path)
})
</script>

<style scoped>
.user-manual-container {
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 1000;
}

.floating-help-button {
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

/* 用户手册样式 */
.user-manual-content {
  max-height: 70vh;
  overflow-y: auto;
  padding: 0 20px;
}

.manual-section {
  margin-bottom: 24px;
  padding: 16px;
  background-color: #f8f9fa;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.manual-section h4 {
  margin-top: 0;
  color: #1976d2;
  font-size: 18px;
  margin-bottom: 12px;
}

.manual-section ul {
  margin: 0;
  padding-left: 20px;
}

.manual-section li {
  margin-bottom: 8px;
}

.warning-section {
  background-color: #fff8e1;
  border-left: 4px solid #ffc107;
}

.faq-item {
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #ebeef5;
}

.faq-item h5 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 16px;
}

.faq-item p {
  margin: 0;
  color: #606266;
}

.faq-item:last-child {
  border-bottom: none;
}
</style> 