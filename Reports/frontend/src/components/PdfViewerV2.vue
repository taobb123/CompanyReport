<template>
  <div class="pdf-viewer-v2">
    <div v-if="!pdfUrl" class="empty-state">
      <el-empty 
        description="请从左侧目录选择报告查看"
        :image-size="150"
      >
        <template #image>
          <el-icon :size="150" color="#c0c4cc"><Document /></el-icon>
        </template>
      </el-empty>
    </div>
    
    <div v-else class="pdf-container">
      <div class="pdf-header">
        <div class="pdf-title">
          <el-icon><Document /></el-icon>
          <span>{{ reportTitle || 'PDF 报告' }}</span>
        </div>
        <div class="pdf-actions">
          <el-button 
            :icon="Link" 
            @click="openInNewWindow"
            size="small"
            type="primary"
          >
            新窗口打开
          </el-button>
          <el-button 
            :icon="Download" 
            @click="downloadPdf"
            size="small"
          >
            下载
          </el-button>
          <el-button 
            :icon="FullScreen" 
            @click="toggleFullscreen"
            size="small"
          >
            全屏
          </el-button>
        </div>
      </div>
      
      <!-- PDF 内容区域 - 使用 vue3-pdf-app -->
      <div class="pdf-content" ref="pdfContentRef">
        <div v-if="loading" class="loading-state">
          <el-loading text="正在加载 PDF..." />
        </div>
        
        <div v-else-if="error" class="error-state">
          <el-alert
            :title="error"
            type="error"
            :closable="false"
            show-icon
          >
            <template #default>
              <p>{{ errorDetails }}</p>
              <div class="error-actions">
                <el-button type="primary" @click="retryLoad">
                  重试
                </el-button>
                <el-button @click="openInNewWindow">
                  在新窗口打开
                </el-button>
              </div>
            </template>
          </el-alert>
        </div>
        
        <!-- 使用 vue3-pdf-app 组件 -->
        <vue-pdf-app
          v-else
          :pdf="proxyUrl"
          :config="pdfConfig"
          @pages-rendered="onPagesRendered"
          @error="onPdfError"
          class="pdf-app"
        ></vue-pdf-app>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { Document, Download, FullScreen, Link } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import VuePdfApp from 'vue3-pdf-app'
import 'vue3-pdf-app/dist/icons/main.css'

const props = defineProps({
  pdfUrl: {
    type: String,
    default: ''
  },
  reportTitle: {
    type: String,
    default: ''
  }
})

const pdfContentRef = ref(null)
const loading = ref(false)
const error = ref('')
const errorDetails = ref('')

// 代理服务器地址
const PROXY_BASE_URL = import.meta.env.VITE_PROXY_URL || 'http://localhost:5000'

// 计算代理 URL
const proxyUrl = computed(() => {
  if (!props.pdfUrl) return ''
  
  // 如果是本地文件路径，直接返回
  if (props.pdfUrl.startsWith('/')) {
    return window.location.origin + props.pdfUrl
  }
  
  // 如果是网络 URL，使用代理
  return `${PROXY_BASE_URL}/pdf-proxy?url=${encodeURIComponent(props.pdfUrl)}`
})

// PDF 配置
const pdfConfig = {
  sidebar: {
    viewOutline: false,
    viewThumbnail: false,
    viewAttachments: false
  },
  secondaryToolbar: {
    secondaryOpenFile: false,
    secondaryPrint: true,
    secondaryDownload: true
  }
}

// PDF 页面渲染完成
const onPagesRendered = () => {
  loading.value = false
  error.value = ''
  console.log('✅ PDF 页面渲染完成')
}

// PDF 加载错误
const onPdfError = (err) => {
  console.error('PDF 加载错误:', err)
  loading.value = false
  error.value = 'PDF 加载失败'
  errorDetails.value = err.message || '无法加载 PDF 文件，请检查代理服务器或网络连接'
  ElMessage.error('PDF 加载失败')
}

// 在新窗口打开 PDF
const openInNewWindow = () => {
  if (!props.pdfUrl) return
  const newWindow = window.open(props.pdfUrl, '_blank')
  if (!newWindow) {
    ElMessage.warning('弹窗被阻止，请允许浏览器弹窗后重试')
  }
}

// 下载 PDF
const downloadPdf = async () => {
  if (!props.pdfUrl) return
  
  try {
    // 通过代理下载
    const link = document.createElement('a')
    link.href = proxyUrl.value
    link.download = props.reportTitle || 'report.pdf'
    link.target = '_blank'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  } catch (err) {
    console.error('下载失败:', err)
    ElMessage.error('下载失败，请尝试在新窗口打开')
  }
}

// 重试加载
const retryLoad = () => {
  error.value = ''
  errorDetails.value = ''
  loading.value = true
  // 强制重新加载（通过改变 key）
  // vue3-pdf-app 会重新加载
}

// 切换全屏
const toggleFullscreen = () => {
  if (!pdfContentRef.value) return
  
  if (!document.fullscreenElement) {
    pdfContentRef.value.requestFullscreen?.() || 
    pdfContentRef.value.webkitRequestFullscreen?.() ||
    pdfContentRef.value.mozRequestFullScreen?.() ||
    pdfContentRef.value.msRequestFullscreen?.()
  } else {
    document.exitFullscreen?.() ||
    document.webkitExitFullscreen?.() ||
    document.mozCancelFullScreen?.() ||
    document.msExitFullscreen?.()
  }
}

// 监听 PDF URL 变化
watch(() => props.pdfUrl, (newUrl) => {
  if (newUrl) {
    loading.value = true
    error.value = ''
    errorDetails.value = ''
    
    // 测试代理服务器
    fetch(`${PROXY_BASE_URL}/health`)
      .then(res => res.json())
      .then(data => {
        console.log('✅ 代理服务器健康检查通过:', data)
      })
      .catch(err => {
        console.error('❌ 代理服务器不可用:', err)
        ElMessage.warning('代理服务器可能未运行')
      })
  } else {
    loading.value = false
  }
}, { immediate: true })
</script>

<style scoped>
.pdf-viewer-v2 {
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

.pdf-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.pdf-header {
  padding: 16px 20px;
  background: white;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.pdf-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 500;
  color: #303133;
  flex: 1;
  overflow: hidden;
}

.pdf-title span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pdf-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.pdf-content {
  flex: 1;
  overflow: hidden;
  position: relative;
  background: #525252;
}

.loading-state {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fafafa;
}

.error-state {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  background: #fafafa;
}

.error-state :deep(.el-alert) {
  max-width: 600px;
}

.error-actions {
  margin-top: 15px;
  display: flex;
  gap: 10px;
  justify-content: center;
}

.pdf-app {
  width: 100%;
  height: 100%;
}
</style>

