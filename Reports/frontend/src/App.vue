<template>
  <div id="app">
    <el-container class="app-container">
      <el-header class="app-header">
        <h1>
          <el-icon><Document /></el-icon>
          证券研究报告查看器
        </h1>
        <div class="header-actions">
          <el-dropdown @command="handleRefreshCommand" trigger="click">
            <el-button 
              type="primary" 
              :icon="Refresh" 
              :loading="loading"
            >
              刷新报告
              <el-icon class="el-icon--right"><arrow-down /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="normal">
                  <el-icon><Refresh /></el-icon>
                  普通刷新（使用缓存）
                </el-dropdown-item>
                <el-dropdown-item command="force">
                  <el-icon><RefreshRight /></el-icon>
                  强制刷新（忽略缓存）
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      
      <el-container class="main-container">
        <!-- 左侧：报告目录（简化版：原生链接，直接在新窗口打开） -->
        <el-aside width="400px" class="sidebar">
          <!-- 类型选择器 -->
          <ReportTypeSelector 
            ref="typeSelectorRef"
            @change="handleTypeChange"
            @type-selected="handleTypeSelected"
            @refresh="handleTypeRefresh"
          />
          <ReportDirectorySimple 
            ref="directoryRef"
            :reports="reports"
            :loading="loading"
            :selectedReport="selectedReport"
            @select-report="handleSelectReport"
          />
        </el-aside>
        
        <!-- 右侧：报告详情查看器（结构化展示） -->
        <el-main class="detail-viewer-container">
          <ReportDetailViewer 
            :report="selectedReport"
          />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Document, Refresh, ArrowDown, RefreshRight } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
// 使用简化版目录（原生链接，直接在新窗口打开）
import ReportDirectorySimple from './components/ReportDirectorySimple.vue'
import ReportTypeSelector from './components/ReportTypeSelector.vue'
import ReportDetailViewer from './components/ReportDetailViewer.vue'
// 或使用原版目录（尝试下载后显示）
// import ReportDirectory from './components/ReportDirectory.vue'
// 简化版不需要 PDF 查看器（直接在新窗口打开）
// import PdfViewerV3 from './components/PdfViewerV3.vue'
// import PdfViewerV2 from './components/PdfViewerV2.vue'

const reports = ref([])
const loading = ref(false)
const typeSelectorRef = ref(null)
const directoryRef = ref(null)
const selectedReport = ref(null)  // 当前选中的报告

// 当前选择的类型和数量（单选模式）
const currentTypes = ref(['strategy'])  // 默认选中第一个类型
const currentLimit = ref(6)

// API基础URL
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000'

// 类型变化处理
const handleTypeChange = ({ types, limit }) => {
  currentTypes.value = types
  currentLimit.value = limit
  // 不自动加载，让用户点击刷新按钮
}

// 类型选择联动（选择类型时自动展开目录）
const handleTypeSelected = (types) => {
  if (directoryRef.value) {
    directoryRef.value.highlightTypes(types)
  }
}

// 选择报告
const handleSelectReport = (report) => {
  selectedReport.value = report
}

// 处理类型选择器触发的刷新
const handleTypeRefresh = ({ types, limit, force }) => {
  if (types && types.length > 0) {
    const typesParam = types.join(',')
    fetchReports(typesParam, limit, force)
  }
}

// 刷新命令处理
const handleRefreshCommand = (command) => {
  if (command === 'force') {
    loadReports(true)
  } else {
    loadReports(false)
  }
}

// 加载报告数据
const loadReports = async (force = false) => {
  // 检查是否选择了类型
  if (!typeSelectorRef.value) {
    // 如果组件还没加载，使用默认值
    const types = currentTypes.value.length > 0 
      ? currentTypes.value.join(',') 
      : 'all'
    const limit = currentLimit.value || 6
    await fetchReports(types, limit, force)
    return
  }
  
  const selectedTypes = typeSelectorRef.value.getSelectedTypes()
  const limit = typeSelectorRef.value.getLimit()
  
  if (selectedTypes.length === 0) {
    ElMessage.warning('请选择一个报告类型')
    return
  }
  
  const typesParam = selectedTypes.join(',')
  await fetchReports(typesParam, limit, force)
}

// 获取报告数据
const fetchReports = async (types, limit, force = false) => {
  loading.value = true
  try {
    // 从API获取数据
    const forceParam = force ? '&force=true' : ''
    const url = `${API_BASE_URL}/api/reports?type=${types}&limit=${limit}${forceParam}`
    console.log('请求URL:', url)
    
    const response = await fetch(url)
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.error || `HTTP错误: ${response.status}`)
    }
    
    const result = await response.json()
    
    if (result.success && result.data) {
      reports.value = result.data
      
      if (result.data.length === 0) {
        ElMessage.warning('未找到报告数据')
      } else {
        // 显示缓存状态信息
        const cacheInfo = []
        if (result.cache_status) {
          const statusMap = {
            'cached': '使用缓存',
            'fetched': '新抓取',
            'force_refresh': '强制刷新'
          }
          Object.entries(result.cache_status).forEach(([type, status]) => {
            if (statusMap[status]) {
              cacheInfo.push(`${getTypeName(type)}: ${statusMap[status]}`)
            }
          })
        }
        
        const typeCounts = Object.entries(result.by_type || {})
          .map(([type, count]) => `${getTypeName(type)}: ${count}`)
          .join(', ')
        
        const message = force 
          ? `强制刷新完成，加载 ${result.data.length} 篇报告 (${typeCounts})`
          : `成功加载 ${result.data.length} 篇报告 (${typeCounts})${cacheInfo.length > 0 ? ' [' + cacheInfo.join(', ') + ']' : ''}`
        
        ElMessage.success(message)
        console.log('按类型统计:', result.by_type)
        console.log('缓存状态:', result.cache_status)
      }
      
      // 触发类型联动
      if (typeSelectorRef.value) {
        const selectedTypes = typeSelectorRef.value.getSelectedTypes()
        triggerTypeLinkage(selectedTypes)
      }
    } else {
      throw new Error(result.error || '获取报告数据失败')
    }
    
    console.log('加载报告数据:', result.data)
  } catch (error) {
    console.error('加载报告失败:', error)
    ElMessage.error({
      message: `加载报告失败: ${error.message}`,
      duration: 5000,
      showClose: true
    })
  } finally {
    loading.value = false
  }
}

// 触发类型联动（自动展开和高亮）
const triggerTypeLinkage = (selectedTypes) => {
  // 通过事件通知目录组件展开和高亮
  if (directoryRef.value) {
    directoryRef.value.highlightTypes(selectedTypes)
  }
}

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

// 简化版不需要选择报告处理（直接在新窗口打开）
// const handleSelectReport = (report) => {
//   selectedReport.value = report
//   selectedPdfUrl.value = report.url
// }

// 组件挂载时不需要手动加载数据
// 类型选择器会在挂载时自动触发刷新
// onMounted(() => {
//   loadReports()
// })
</script>

<style scoped>
#app {
  height: 100vh;
  overflow: hidden;
}

.app-container {
  height: 100vh;
}

.app-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 30px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.app-header h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.main-container {
  height: calc(100vh - 60px);
}

.sidebar {
  background: #f5f7fa;
  border-right: 1px solid #e4e7ed;
  overflow-y: auto;
  padding: 0;
  display: flex;
  flex-direction: column;
}

.detail-viewer-container {
  padding: 0;
  background: #fafafa;
  overflow: hidden;
}
</style>

