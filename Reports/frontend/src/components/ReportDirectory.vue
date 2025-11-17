<template>
  <div class="report-directory">
    <div class="directory-header">
      <h2>
        <el-icon><FolderOpened /></el-icon>
        报告目录
      </h2>
      <div class="stats">
        共 {{ totalReports }} 篇报告
      </div>
    </div>
    
    <div v-loading="loading" class="directory-content">
      <el-empty 
        v-if="!loading && reports.length === 0" 
        description="暂无报告数据"
        :image-size="100"
      />
      
      <el-collapse v-else v-model="activeTypes" class="report-collapse">
        <el-collapse-item
          v-for="(typeReports, type) in groupedReports"
          :key="type"
          :name="type"
          class="report-type-section"
        >
          <template #title>
            <div class="collapse-title">
              <el-icon><Document /></el-icon>
              <span class="type-name">{{ getTypeName(type) }}</span>
              <el-badge :value="typeReports.length" class="type-badge" />
            </div>
          </template>
          
          <div class="report-list">
            <div
              v-for="report in typeReports"
              :key="report.url"
              class="report-item"
              :class="{ active: selectedReport?.url === report.url }"
              @click="handleClick(report)"
              @contextmenu.prevent="handleRightClick(report, $event)"
            >
              <div class="report-title">{{ report.report_info.title }}</div>
              <div class="report-meta">
                <el-icon><Calendar /></el-icon>
                <span>{{ report.report_info.date || '未知日期' }}</span>
              </div>
              <div class="report-actions">
                <el-button
                  :icon="Link"
                  text
                  size="small"
                  @click.stop="openInNewWindow(report)"
                  title="在新窗口打开"
                >
                </el-button>
              </div>
            </div>
          </div>
        </el-collapse-item>
      </el-collapse>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { FolderOpened, Document, Calendar, Link } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  reports: {
    type: Array,
    default: () => []
  },
  selectedReport: {
    type: Object,
    default: null
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['select-report'])

const activeTypes = ref([])

// 按类型分组报告
const groupedReports = computed(() => {
  const grouped = {}
  props.reports.forEach(report => {
    const type = report.report_info.report_type
    if (!grouped[type]) {
      grouped[type] = []
    }
    grouped[type].push(report)
  })
  
  // 默认展开所有类型
  if (activeTypes.value.length === 0) {
    activeTypes.value = Object.keys(grouped)
  }
  
  return grouped
})

// 总报告数
const totalReports = computed(() => props.reports.length)

// 获取类型名称
const getTypeName = (type) => {
  const typeMap = {
    'strategy': '策略报告',
    'industry': '行业研报',
    'macro': '宏观研究',
    'stock': '个股研报'
  }
  return typeMap[type] || type
}

// 点击报告项
const handleClick = (report) => {
  emit('select-report', report)
}

// 右键点击（在新窗口打开）
const handleRightClick = (report, event) => {
  openInNewWindow(report)
}

// 在新窗口打开报告
const openInNewWindow = (report) => {
  if (!report || !report.url) return
  
  // 使用原始 URL（如果存在），否则使用转换后的 URL
  const url = report.originalUrl || report.url
  
  const newWindow = window.open(url, '_blank')
  if (!newWindow) {
    ElMessage.warning('弹窗被阻止，请允许浏览器弹窗后重试')
  }
}
</script>

<style scoped>
.report-directory {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: white;
}

.directory-header {
  padding: 20px;
  border-bottom: 1px solid #e4e7ed;
  background: white;
  position: sticky;
  top: 0;
  z-index: 10;
}

.directory-header h2 {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 8px;
}

.stats {
  font-size: 14px;
  color: #909399;
}

.directory-content {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
}

.report-collapse {
  border: none;
}

.report-collapse :deep(.el-collapse-item__header) {
  padding: 12px 16px;
  background: #f5f7fa;
  border-radius: 4px;
  margin-bottom: 8px;
  font-weight: 500;
}

.report-collapse :deep(.el-collapse-item__content) {
  padding: 8px 0;
}

.collapse-title {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}

.type-name {
  flex: 1;
}

.type-badge {
  margin-left: auto;
}

.report-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.report-item {
  padding: 12px 16px;
  background: white;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.report-item:hover {
  border-color: #667eea;
  background: #f0f4ff;
  transform: translateX(4px);
}

.report-item.active {
  border-color: #667eea;
  background: #e6f0ff;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.2);
}

.report-title {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 8px;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.report-meta {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #909399;
}

.report-actions {
  position: absolute;
  top: 8px;
  right: 8px;
  opacity: 0;
  transition: opacity 0.3s;
}

.report-item:hover .report-actions {
  opacity: 1;
}

.report-item .report-actions :deep(.el-button) {
  padding: 4px;
}
</style>

