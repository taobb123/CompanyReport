<template>
  <div class="report-detail-viewer">
    <div v-if="!report" class="empty-state">
      <el-empty 
        description="请从左侧目录选择报告查看详情"
        :image-size="150"
      >
        <template #image>
          <el-icon :size="150" color="#c0c4cc"><Document /></el-icon>
        </template>
      </el-empty>
    </div>
    
    <div v-else class="report-detail">
      <!-- 报告头部信息 -->
      <div class="report-header">
        <div class="report-title-section">
          <h2 class="report-title">
            <el-icon><Document /></el-icon>
            {{ report.report_info.title }}
          </h2>
          <div class="report-meta-info">
            <el-tag :type="getTypeTagType(report.report_info.report_type)" size="small">
              {{ getTypeName(report.report_info.report_type) }}
            </el-tag>
            <span class="report-date">
              <el-icon><Calendar /></el-icon>
              {{ report.report_info.date || '未知日期' }}
            </span>
          </div>
        </div>
        <div class="report-actions">
          <a 
            :href="report.url"
            target="_blank"
            rel="noopener noreferrer"
            class="pdf-link"
          >
            <el-icon><Link /></el-icon>
            打开PDF
          </a>
        </div>
      </div>
      
      <!-- 信息笔记区域 -->
      <div class="note-summary-section" v-if="noteContent">
        <div class="section-title">
          <el-icon><Document /></el-icon>
          <span>信息笔记</span>
          <el-button 
            size="small" 
            :icon="Document" 
            @click="copyNoteContent"
            style="margin-left: auto;"
          >
            复制全部
          </el-button>
        </div>
        <pre class="note-summary">{{ noteContent }}</pre>
      </div>
      
      <!-- 关键词区域 -->
      <div class="keywords-section">
        <div class="section-title">
          <el-icon><PriceTag /></el-icon>
          <span>关键词</span>
          <el-button 
            text 
            size="small" 
            @click="editMode = !editMode"
            style="margin-left: auto;"
          >
            {{ editMode ? '完成' : '编辑' }}
          </el-button>
        </div>
        
        <!-- 个股关键词 - 仅个股研报显示 -->
        <div class="keyword-group" v-if="report?.report_info?.report_type === 'stock'">
          <div class="keyword-label">
            <el-icon><Document /></el-icon>
            <span>个股</span>
          </div>
          <div class="keyword-tags">
            <el-tag
              v-for="(stock, index) in editedKeywords.stocks"
              :key="`stock-${index}`"
              closable
              :disable-transitions="false"
              @close="removeKeyword('stocks', index)"
              class="keyword-tag"
              effect="plain"
            >
              {{ stock }}
            </el-tag>
            <el-input
              v-if="editMode"
              v-model="newStockKeyword"
              size="small"
              placeholder="添加个股"
              style="width: 120px;"
              @keyup.enter="addKeyword('stocks', newStockKeyword)"
              @blur="addKeyword('stocks', newStockKeyword)"
            />
          </div>
        </div>
        
        <!-- 行业关键词 - 仅行业研报显示 -->
        <div class="keyword-group" v-if="report?.report_info?.report_type === 'industry'">
          <div class="keyword-label">
            <el-icon><Document /></el-icon>
            <span>行业</span>
          </div>
          <div class="keyword-tags">
            <el-tag
              v-for="(industry, index) in editedKeywords.industries"
              :key="`industry-${index}`"
              closable
              :disable-transitions="false"
              @close="removeKeyword('industries', index)"
              class="keyword-tag"
              effect="plain"
            >
              {{ industry }}
            </el-tag>
            <el-input
              v-if="editMode"
              v-model="newIndustryKeyword"
              size="small"
              placeholder="添加行业"
              style="width: 120px;"
              @keyup.enter="addKeyword('industries', newIndustryKeyword)"
              @blur="addKeyword('industries', newIndustryKeyword)"
            />
          </div>
        </div>
        
        <!-- 策略关键词 - 仅策略报告显示 -->
        <div class="keyword-group" v-if="report?.report_info?.report_type === 'strategy'">
          <div class="keyword-label">
            <el-icon><Document /></el-icon>
            <span>策略</span>
          </div>
          <div class="keyword-tags">
            <el-tag
              v-for="(strategy, index) in editedKeywords.strategies"
              :key="`strategy-${index}`"
              closable
              :disable-transitions="false"
              @close="removeKeyword('strategies', index)"
              class="keyword-tag"
              effect="plain"
            >
              {{ strategy }}
            </el-tag>
            <el-input
              v-if="editMode"
              v-model="newStrategyKeyword"
              size="small"
              placeholder="添加策略"
              style="width: 120px;"
              @keyup.enter="addKeyword('strategies', newStrategyKeyword)"
              @blur="addKeyword('strategies', newStrategyKeyword)"
            />
          </div>
        </div>
        
        <!-- 宏观关键词 - 仅宏观研究显示 -->
        <div class="keyword-group" v-if="report?.report_info?.report_type === 'macro'">
          <div class="keyword-label">
            <el-icon><Document /></el-icon>
            <span>宏观</span>
          </div>
          <div class="keyword-tags">
            <el-tag
              v-for="(macro, index) in editedKeywords.macro"
              :key="`macro-${index}`"
              closable
              :disable-transitions="false"
              @close="removeKeyword('macro', index)"
              class="keyword-tag"
              effect="plain"
            >
              {{ macro }}
            </el-tag>
            <el-input
              v-if="editMode"
              v-model="newMacroKeyword"
              size="small"
              placeholder="添加宏观"
              style="width: 120px;"
              @keyup.enter="addKeyword('macro', newMacroKeyword)"
              @blur="addKeyword('macro', newMacroKeyword)"
            />
          </div>
        </div>
      </div>
      
      <!-- 备注区域 -->
      <div class="notes-section">
        <div class="section-title">
          <el-icon><Edit /></el-icon>
          <span>备注</span>
        </div>
        <el-input
          v-model="editedNotes"
          type="textarea"
          :rows="4"
          placeholder="添加备注信息..."
          @blur="saveNotes"
        />
      </div>
      
      <!-- 元信息区域 -->
      <div class="metadata-section">
        <div class="section-title">
          <el-icon><InfoFilled /></el-icon>
          <span>元信息</span>
        </div>
        <div class="metadata-content">
          <div class="metadata-item">
            <span class="metadata-label">数据来源：</span>
            <span class="metadata-value">{{ report.metadata?.source || '未知' }}</span>
          </div>
          <div class="metadata-item" v-if="report.metadata?.extracted_at">
            <span class="metadata-label">提取时间：</span>
            <span class="metadata-value">{{ formatDate(report.metadata.extracted_at) }}</span>
          </div>
          <div class="metadata-item">
            <span class="metadata-label">PDF链接：</span>
            <a :href="report.url" target="_blank" rel="noopener noreferrer" class="pdf-url-link">
              {{ report.url }}
            </a>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { 
  Document, Calendar, Link, PriceTag, Edit, InfoFilled 
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  report: {
    type: Object,
    default: null
  }
})

const editMode = ref(false)
const editedKeywords = ref({
  stocks: [],
  industries: [],
  strategies: [],
  macro: []
})

const editedNotes = ref('')
const newStockKeyword = ref('')
const newIndustryKeyword = ref('')
const newStrategyKeyword = ref('')
const newMacroKeyword = ref('')

const getTypeName = (type) => {
  const typeMap = {
    'strategy': '策略报告',
    'industry': '行业研报',
    'macro': '宏观研究',
    'stock': '个股研报'
  }
  return typeMap[type] || type
}

// 从localStorage加载
const loadFromLocalStorage = (url) => {
  if (!url) return null
  
  try {
    const data = localStorage.getItem(`report_${url}`)
    return data ? JSON.parse(data) : null
  } catch (e) {
    console.error('加载本地数据失败:', e)
    return null
  }
}

// 加载报告数据（包括本地编辑的内容）
const loadReportData = (report) => {
  if (!report) return
  
  // 从localStorage加载编辑内容
  const savedData = loadFromLocalStorage(report.url)
  
  // 合并关键词（优先使用编辑后的，否则使用元数据）
  editedKeywords.value = {
    stocks: savedData?.keywords?.stocks || report.metadata?.keywords?.stocks || [],
    industries: savedData?.keywords?.industries || report.metadata?.keywords?.industries || [],
    strategies: savedData?.keywords?.strategies || report.metadata?.keywords?.strategies || [],
    macro: savedData?.keywords?.macro || report.metadata?.keywords?.macro || []
  }
  
  // 加载备注
  editedNotes.value = savedData?.notes || ''
}

// 监听报告变化，加载数据
watch(() => props.report, (newReport) => {
  if (newReport) {
    loadReportData(newReport)
  }
}, { immediate: true })

// 添加关键词
const addKeyword = (category, keyword) => {
  if (!keyword || !keyword.trim()) return
  
  const trimmedKeyword = keyword.trim()
  if (!editedKeywords.value[category].includes(trimmedKeyword)) {
    editedKeywords.value[category].push(trimmedKeyword)
    saveToLocalStorage()
    
    // 清空输入框
    if (category === 'stocks') newStockKeyword.value = ''
    else if (category === 'industries') newIndustryKeyword.value = ''
    else if (category === 'strategies') newStrategyKeyword.value = ''
    else if (category === 'macro') newMacroKeyword.value = ''
  }
}

// 删除关键词
const removeKeyword = (category, index) => {
  editedKeywords.value[category].splice(index, 1)
  saveToLocalStorage()
}

// 保存备注
const saveNotes = () => {
  saveToLocalStorage()
  ElMessage.success('备注已保存')
}

// 保存到localStorage
const saveToLocalStorage = () => {
  if (!props.report) return
  
  const data = {
    keywords: { ...editedKeywords.value },
    notes: editedNotes.value,
    updated_at: new Date().toISOString()
  }
  
  localStorage.setItem(`report_${props.report.url}`, JSON.stringify(data))
}

// 不再需要openInNewWindow函数，使用纯HTML链接

const noteContent = computed(() => {
  if (!props.report) return ''
  const reportInfo = props.report.report_info || {}
  const metadata = props.report.metadata || {}
  const keywordsData = editedKeywords.value
  
  const lines = []
  lines.push(`标题：${reportInfo.title || ''}`)
  lines.push(`类型：${getTypeName(reportInfo.report_type)}`)
  lines.push(`日期：${reportInfo.date || '未知日期'}`)
  
  if (metadata.extracted_at) {
    lines.push(`提取时间：${formatDate(metadata.extracted_at)}`)
  }
  
  const formatCategory = (label, items = []) => {
    return `${label}：${items.length ? items.join('、') : '无'}`
  }
  
  // 根据报告类型只显示对应类型的关键词
  const reportType = reportInfo.report_type || 'strategy'
  
  // 根据报告类型只显示匹配的关键词类别
  if (reportType === 'strategy') {
    // 策略报告：只显示策略关键词
    lines.push('关键词：')
    lines.push(formatCategory('策略', keywordsData.strategies))
  } else if (reportType === 'industry') {
    // 行业研报：只显示行业关键词
    lines.push('关键词：')
    lines.push(formatCategory('行业', keywordsData.industries))
  } else if (reportType === 'macro') {
    // 宏观研究：只显示宏观关键词
    lines.push('关键词：')
    lines.push(formatCategory('宏观', keywordsData.macro))
  } else if (reportType === 'stock') {
    // 个股研报：只显示个股关键词
    lines.push('关键词：')
    lines.push(formatCategory('个股', keywordsData.stocks))
  } else {
    // 默认：显示所有关键词
    lines.push('关键词：')
    lines.push(formatCategory('个股', keywordsData.stocks))
    lines.push(formatCategory('行业', keywordsData.industries))
    lines.push(formatCategory('策略', keywordsData.strategies))
    lines.push(formatCategory('宏观', keywordsData.macro))
  }
  
  if (props.report.url) {
    lines.push(`PDF：${props.report.url}`)
  }
  if (reportInfo.detail_url) {
    lines.push(`详情页：${reportInfo.detail_url}`)
  }
  
  return lines.join('\n')
})

const copyNoteContent = async () => {
  if (!noteContent.value) {
    ElMessage.warning('暂无可复制内容')
    return
  }
  try {
    await navigator.clipboard.writeText(noteContent.value)
    ElMessage.success('信息已复制')
  } catch (error) {
    try {
      const textarea = document.createElement('textarea')
      textarea.value = noteContent.value
      textarea.style.position = 'fixed'
      textarea.style.opacity = '0'
      document.body.appendChild(textarea)
      textarea.select()
      document.execCommand('copy')
      document.body.removeChild(textarea)
      ElMessage.success('信息已复制')
    } catch (err) {
      console.error('复制失败:', err)
      ElMessage.error('复制失败，请手动复制')
    }
  }
}

// 获取类型标签样式
const getTypeTagType = (type) => {
  const typeMap = {
    'strategy': 'success',
    'industry': 'warning',
    'macro': 'info',
    'stock': 'danger'
  }
  return typeMap[type] || ''
}

// 格式化日期
function formatDate(dateString) {
  if (!dateString) return ''
  try {
    const date = new Date(dateString)
    return date.toLocaleString('zh-CN')
  } catch (e) {
    return dateString
  }
}
</script>

<style scoped>
.report-detail-viewer {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: white;
}

.empty-state {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fafafa;
}

.report-detail {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  padding: 20px;
}

.report-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid #e4e7ed;
}

.report-title-section {
  flex: 1;
}

.report-title {
  margin: 0 0 12px 0;
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  line-height: 1.5;
  display: flex;
  align-items: center;
  gap: 8px;
}

.report-meta-info {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
  color: #909399;
}

.report-date {
  display: flex;
  align-items: center;
  gap: 4px;
}

.report-actions {
  margin-left: 20px;
}

.pdf-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: #409eff;
  color: white;
  text-decoration: none;
  border-radius: 4px;
  font-size: 14px;
  transition: background 0.3s;
}

.pdf-link:hover {
  background: #66b1ff;
}

.pdf-url-link {
  color: #409eff;
  text-decoration: none;
  word-break: break-all;
}

.pdf-url-link:hover {
  text-decoration: underline;
}

.note-summary-section,
.keywords-section,
.notes-section,
.metadata-section {
  margin-bottom: 24px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.note-summary {
  white-space: pre-wrap;
  font-family: 'SFMono-Regular', Menlo, Consolas, 'Liberation Mono', monospace;
  font-size: 13px;
  line-height: 1.8;
  color: #303133;
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  padding: 16px;
  margin: 0;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 16px;
}

.keyword-group {
  margin-bottom: 16px;
}

.keyword-group:last-child {
  margin-bottom: 0;
}

.keyword-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 500;
  color: #606266;
  margin-bottom: 8px;
}

.keyword-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.keyword-tag {
  margin: 0;
}

.metadata-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.metadata-item {
  display: flex;
  align-items: flex-start;
  font-size: 14px;
}

.metadata-label {
  font-weight: 500;
  color: #606266;
  min-width: 80px;
}

.metadata-value {
  color: #303133;
  flex: 1;
  word-break: break-all;
}

.notes-section :deep(.el-textarea__inner) {
  font-size: 14px;
  line-height: 1.6;
}
</style>

