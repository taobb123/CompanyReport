<template>
  <div class="report-directory-simple">
    <div class="directory-header">
      <h2>
        <el-icon><FolderOpened /></el-icon>
        报告目录
      </h2>
      <div class="stats">
        共 {{ totalReports }} 篇报告
      </div>
    </div>
    
    <div v-loading="loading" class="directory-content" ref="directoryContentRef">
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
          :class="{ 'highlighted': highlightedTypes.includes(type) }"
          :ref="(el) => setTypeRef(el, type)"
          :data-type="type"
        >
          <template #title>
            <div class="collapse-title">
              <el-icon><Document /></el-icon>
              <span class="type-name">{{ getTypeName(type) }}</span>
              <el-badge :value="typeReports.length" class="type-badge" />
            </div>
          </template>
          
          <div class="report-list">
            <!-- 报告项：点击显示详情，右键在新窗口打开 -->
            <div
              v-for="report in typeReports"
              :key="report.url"
              class="report-item"
              :class="{ 'active': selectedReport?.url === report.url }"
              @click="handleReportClick(report)"
              @contextmenu.prevent="openInNewWindow(report)"
            >
              <div class="report-title">{{ report.report_info.title }}</div>
              <div class="report-meta">
                <el-icon><Calendar /></el-icon>
                <span>{{ report.report_info.date || '未知日期' }}</span>
                <!-- 显示关键词数量提示 -->
                <span v-if="report.metadata?.keywords" class="keyword-badge">
                  <el-icon><PriceTag /></el-icon>
                  {{ getKeywordCount(report.metadata.keywords) }}
                </span>
              </div>
              <div class="report-link-hint">
                <el-icon><Link /></el-icon>
                <span>左键查看详情，右键在新窗口打开</span>
              </div>
            </div>
          </div>
        </el-collapse-item>
      </el-collapse>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, nextTick } from 'vue'
import { FolderOpened, Document, Calendar, Link, PriceTag } from '@element-plus/icons-vue'

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
const highlightedTypes = ref([])
const typeRefs = ref({})  // 存储每个类型的DOM引用
const directoryContentRef = ref(null)  // 目录内容区域的引用

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
  if (activeTypes.value.length === 0 && Object.keys(grouped).length > 0) {
    activeTypes.value = Object.keys(grouped)
  }
  
  return grouped
})

// 设置类型引用
const setTypeRef = (el, type) => {
  if (el) {
    typeRefs.value[type] = el
  }
}

// 高亮类型（联动功能）
const highlightTypes = (types) => {
  highlightedTypes.value = types
  
  // 自动展开选中的类型
  const newActiveTypes = [...new Set([...activeTypes.value, ...types])]
  activeTypes.value = newActiveTypes
  
  // 等待DOM更新后滚动到第一个选中的类型
  nextTick(() => {
    if (types.length > 0) {
      scrollToType(types[0])
    }
  })
  
  // 3秒后取消高亮
  setTimeout(() => {
    highlightedTypes.value = []
  }, 3000)
}

// 滚动到指定类型的标题位置
const scrollToType = (type) => {
  // 等待一小段时间确保DOM已完全渲染
  setTimeout(() => {
    const typeRef = typeRefs.value[type]
    if (!typeRef) {
      console.warn(`未找到类型 ${type} 的DOM引用`)
      return
    }
    
    // Element Plus的el-collapse-item组件，需要获取其根DOM元素
    let collapseItem = null
    if (typeRef.$el) {
      // Vue组件实例，获取其根元素
      collapseItem = typeRef.$el
    } else if (typeRef instanceof HTMLElement) {
      // 直接是DOM元素
      collapseItem = typeRef
    } else if (typeRef.el) {
      // 某些情况下可能是 { el: HTMLElement }
      collapseItem = typeRef.el
    }
    
    if (!collapseItem) {
      // 尝试通过data-type属性查找
      const selector = `.report-type-section[data-type="${type}"]`
      collapseItem = document.querySelector(selector)
      if (!collapseItem) {
        console.warn(`类型 ${type} 的DOM元素不存在`)
        return
      }
    }
    
    // 查找标题元素（el-collapse-item__header）
    const headerElement = collapseItem.querySelector('.el-collapse-item__header')
    const targetElement = headerElement || collapseItem
    
    // 确保在目录内容区域内滚动
    const scrollContainer = directoryContentRef.value || document.querySelector('.directory-content')
    if (scrollContainer) {
      // 计算目标元素相对于滚动容器的位置
      // 滚动到标题位置，使其在容器顶部显示
      const containerRect = scrollContainer.getBoundingClientRect()
      const targetRect = targetElement.getBoundingClientRect()
      const scrollTop = scrollContainer.scrollTop + (targetRect.top - containerRect.top) - 20  // 留20px间距
      
      // 平滑滚动到标题位置
      scrollContainer.scrollTo({
        top: Math.max(0, scrollTop),  // 确保不为负数
        behavior: 'smooth'
      })
    } else {
      // 如果没有找到滚动容器，使用默认的scrollIntoView，滚动到顶部
      targetElement.scrollIntoView({
        behavior: 'smooth',
        block: 'start',  // 滚动到顶部
        inline: 'nearest'
      })
    }
  }, 150)  // 延迟150ms确保DOM更新和展开动画完成
}

// 暴露方法供父组件调用
defineExpose({
  highlightTypes
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
const handleReportClick = (report) => {
  emit('select-report', report)
}

// 在新窗口打开
const openInNewWindow = (report) => {
  if (!report || !report.url) return
  const newWindow = window.open(report.url, '_blank')
  if (!newWindow) {
    console.warn('弹窗被阻止')
  }
}

// 获取关键词数量
const getKeywordCount = (keywords) => {
  if (!keywords) return 0
  const count = (keywords.stocks?.length || 0) + 
                (keywords.industries?.length || 0) + 
                (keywords.strategies?.length || 0) + 
                (keywords.macro?.length || 0)
  return count
}
</script>

<style scoped>
.report-directory-simple {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;
  overflow: hidden;
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
  transition: all 0.3s;
}

.report-type-section.highlighted :deep(.el-collapse-item__header) {
  background: #ecf5ff;
  border: 2px solid #409eff;
  box-shadow: 0 0 8px rgba(64, 158, 255, 0.3);
  animation: highlight-pulse 0.5s ease-in-out;
}

@keyframes highlight-pulse {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.02);
  }
  100% {
    transform: scale(1);
  }
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
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 8px;
}

.report-item:hover {
  border-color: #667eea;
  background: #f0f4ff;
  transform: translateX(4px);
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.2);
}

.report-item.active {
  border-color: #667eea;
  background: #ecf5ff;
  border-width: 2px;
}

.report-title {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.report-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #909399;
}

.keyword-badge {
  display: flex;
  align-items: center;
  gap: 2px;
  padding: 2px 6px;
  background: #f0f9ff;
  border-radius: 10px;
  color: #409eff;
  font-size: 11px;
}

.report-link-hint {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #667eea;
  margin-top: 4px;
  opacity: 0.7;
}

.report-link:hover .report-link-hint {
  opacity: 1;
}
</style>


