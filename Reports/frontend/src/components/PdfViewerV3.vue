<template>
  <div class="pdf-viewer-v3">
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
      
      <!-- PDF 内容区域 -->
      <div class="pdf-content" ref="pdfContentRef">
        <!-- 下载状态 -->
        <div v-if="downloading" class="downloading-state">
          <el-progress 
            :percentage="downloadProgress" 
            :status="downloadStatus"
            :stroke-width="8"
          />
          <p class="download-text">{{ downloadText }}</p>
          <el-button 
            v-if="downloadError" 
            type="primary" 
            @click="retryDownload"
            style="margin-top: 20px;"
          >
            重试下载
          </el-button>
        </div>
        
        <!-- 错误状态 -->
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
                <el-button type="primary" @click="retryDownload">
                  重试下载
                </el-button>
                <el-button @click="openInNewWindow">
                  在新窗口打开
                </el-button>
              </div>
            </template>
          </el-alert>
        </div>
        
        <!-- PDF 显示 - 使用 iframe -->
        <iframe
          v-else
          :src="localPdfUrl"
          class="pdf-iframe"
          frameborder="0"
          @load="handleIframeLoad"
          @error="handleIframeError"
          ref="iframeRef"
        ></iframe>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { Document, Download, FullScreen, Link } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

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
const iframeRef = ref(null)
const downloading = ref(false)
const downloadProgress = ref(0)
const downloadStatus = ref('')
const downloadText = ref('')
const downloadError = ref(false)
const error = ref('')
const errorDetails = ref('')
const localPdfUrl = ref('')

// 静态服务器地址
const STATIC_SERVER_URL = import.meta.env.VITE_STATIC_SERVER_URL || 'http://localhost:5001'

// 下载 PDF 到本地并获取 URL
const downloadPdfToLocal = async () => {
  if (!props.pdfUrl) return
  
  downloading.value = true
  downloadProgress.value = 0
  downloadStatus.value = ''
  downloadText.value = '正在检查缓存...'
  downloadError.value = false
  error.value = ''
  
  try {
    // 检查静态服务器
    const healthResponse = await fetch(`${STATIC_SERVER_URL}/health`)
    if (!healthResponse.ok) {
      throw new Error('静态服务器未运行')
    }
    
    downloadProgress.value = 20
    downloadText.value = '正在下载 PDF...'
    
    // 获取原始 URL 的 referer（如果有）
    const referer = props.pdfUrl.includes('dfcfw.com') 
      ? 'https://data.eastmoney.com/report/' 
      : ''
    
    // 请求下载
    const downloadUrl = `${STATIC_SERVER_URL}/download-and-serve?url=${encodeURIComponent(props.pdfUrl)}${referer ? '&referer=' + encodeURIComponent(referer) : ''}`
    
    const response = await fetch(downloadUrl)
    const data = await response.json()
    
    if (data.success) {
      downloadProgress.value = 100
      downloadStatus.value = 'success'
      downloadText.value = data.cached ? '使用缓存文件' : '下载完成'
      
      // 获取本地 PDF URL
      localPdfUrl.value = `${STATIC_SERVER_URL}${data.url}`
      
      console.log('✅ PDF 已准备就绪:', localPdfUrl.value)
      
      // 延迟隐藏下载状态
      setTimeout(() => {
        downloading.value = false
      }, 1000)
    } else {
      throw new Error(data.error || '下载失败')
    }
  } catch (err) {
    console.error('下载 PDF 失败:', err)
    downloading.value = false
    downloadError.value = true
    error.value = 'PDF 下载失败'
    errorDetails.value = err.message || '无法下载 PDF 文件，请检查静态服务器是否运行'
    downloadStatus.value = 'exception'
    ElMessage.error('PDF 下载失败')
  }
}

// 重试下载
const retryDownload = () => {
  downloadError.value = false
  error.value = ''
  errorDetails.value = ''
  downloadPdfToLocal()
}

// iframe 加载完成
const handleIframeLoad = () => {
  console.log('PDF iframe 加载完成')
}

// iframe 加载错误
const handleIframeError = () => {
  console.error('PDF iframe 加载失败')
  error.value = 'PDF 显示失败'
  errorDetails.value = '无法在 iframe 中显示 PDF，请尝试在新窗口打开'
}

// 在新窗口打开 PDF
const openInNewWindow = () => {
  if (localPdfUrl.value) {
    window.open(localPdfUrl.value, '_blank')
  } else if (props.pdfUrl) {
    window.open(props.pdfUrl, '_blank')
  }
}

// 下载 PDF
const downloadPdf = async () => {
  if (localPdfUrl.value) {
    const link = document.createElement('a')
    link.href = localPdfUrl.value
    link.download = props.reportTitle || 'report.pdf'
    link.click()
  } else {
    openInNewWindow()
  }
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
    // 重置状态
    localPdfUrl.value = ''
    error.value = ''
    errorDetails.value = ''
    
    // 下载 PDF 到本地
    downloadPdfToLocal()
  }
}, { immediate: true })
</script>

<style scoped>
.pdf-viewer-v3 {
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

.downloading-state {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  background: #fafafa;
}

.download-text {
  margin-top: 20px;
  color: #606266;
  font-size: 14px;
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

.pdf-iframe {
  width: 100%;
  height: 100%;
  border: none;
  background: white;
}
</style>

