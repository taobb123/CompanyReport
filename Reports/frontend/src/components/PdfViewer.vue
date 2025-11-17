<template>
  <div class="pdf-viewer">
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
        <div v-if="!viewerUrl" class="loading-state">
          <el-loading text="正在准备 PDF 查看器..." />
        </div>
        
        <!-- 加载状态 -->
        <div v-else-if="loading" class="loading-state">
          <el-loading text="正在加载 PDF..." />
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
              <p>无法加载 PDF 文件。可能的原因：</p>
              <ul>
                <li>代理服务器未运行或无法访问</li>
                <li>PDF 文件被反爬虫拦截</li>
                <li>网络连接问题</li>
              </ul>
              <div class="error-actions">
                <el-button type="primary" @click="retryLoad">
                  重试
                </el-button>
                <el-button @click="openInNewWindow">
                  在新窗口打开
                </el-button>
                <el-button @click="testProxyUrl">
                  测试代理 URL
                </el-button>
              </div>
            </template>
          </el-alert>
        </div>
        
        <!-- PDF 显示 -->
        <iframe
          v-else
          :src="viewerUrl"
          class="pdf-iframe"
          frameborder="0"
          @load="handleIframeLoad"
          @error="handleIframeError"
          ref="iframeRef"
        ></iframe>
        
        <!-- 调试信息（开发环境） -->
        <div v-if="showDebugInfo" class="debug-info">
          <el-alert
            title="调试信息"
            type="info"
            :closable="true"
            @close="showDebugInfo = false"
          >
            <template #default>
              <p><strong>原始 URL:</strong> {{ pdfUrl }}</p>
              <p><strong>查看器 URL:</strong> {{ viewerUrl }}</p>
              <p><strong>代理地址:</strong> {{ PROXY_BASE_URL }}</p>
              <p><strong>使用 PDF.js 查看器:</strong> {{ USE_PDFJS_VIEWER ? '是' : '否' }}</p>
              <p><strong>加载状态:</strong> {{ loading ? '加载中' : error ? '错误' : '正常' }}</p>
              <p><small>按 F12 打开控制台查看详细日志</small></p>
              <el-button size="small" @click="testProxyUrl" style="margin-top: 10px;">
                测试代理 URL
              </el-button>
            </template>
          </el-alert>
        </div>
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
const showDebugInfo = ref(import.meta.env.DEV) // 开发环境显示调试信息
const loading = ref(false)
const error = ref('')
let loadTimeout = null

// PDF.js 官方查看器 URL
const PDFJS_VIEWER_URL = 'https://mozilla.github.io/pdf.js/web/viewer.html'

// 代理服务器地址（可在配置中修改）
const PROXY_BASE_URL = import.meta.env.VITE_PROXY_URL || 'http://localhost:5000'

// 使用 PDF.js 查看器的选项
// 注意：PDF.js 官方查看器可能无法通过 file 参数加载代理 URL
// 如果遇到问题，设置为 false 使用浏览器内置 PDF 查看器
const USE_PDFJS_VIEWER = false // 改为 false，直接使用代理 URL

// 计算查看器 URL
const viewerUrl = computed(() => {
  if (!props.pdfUrl) return ''
  
  // 如果是本地文件路径（以 / 开头）
  if (props.pdfUrl.startsWith('/')) {
    if (USE_PDFJS_VIEWER) {
      const url = `${PDFJS_VIEWER_URL}?file=${encodeURIComponent(window.location.origin + props.pdfUrl)}`
      console.log('本地文件查看器 URL:', url)
      return url
    } else {
      // 直接显示 PDF
      return window.location.origin + props.pdfUrl
    }
  }
  
  // 如果是网络 URL，使用代理
  const proxyUrl = `${PROXY_BASE_URL}/pdf-proxy?url=${encodeURIComponent(props.pdfUrl)}`
  
  if (USE_PDFJS_VIEWER) {
    // 方案 1：通过 PDF.js 查看器加载代理 URL
    // 注意：这可能不工作，因为 PDF.js 查看器可能无法加载跨域代理 URL
    const viewerUrl = `${PDFJS_VIEWER_URL}?file=${encodeURIComponent(proxyUrl)}`
    console.log('网络文件查看器 URL (通过 PDF.js):', viewerUrl)
    return viewerUrl
  } else {
    // 方案 2：直接使用代理 URL（浏览器内置 PDF 查看器）
    console.log('网络文件代理 URL (直接显示):', proxyUrl)
    return proxyUrl
  }
})

// iframe 加载完成
const handleIframeLoad = () => {
  console.log('iframe 加载完成')
  console.log('查看器 URL:', viewerUrl.value)
  console.log('原始 PDF URL:', props.pdfUrl)
  
  loading.value = false
  
  // 清除超时
  if (loadTimeout) {
    clearTimeout(loadTimeout)
    loadTimeout = null
  }
  
  // 延迟检查 iframe 内容（给 PDF 一些时间加载）
  setTimeout(() => {
    checkIframeContent()
  }, 2000)
}

// 检查 iframe 内容
const checkIframeContent = () => {
  if (!iframeRef.value) return
  
  try {
    const iframe = iframeRef.value
    // 尝试访问 iframe 内容（可能跨域，会失败）
    try {
      const iframeDoc = iframe.contentDocument || iframe.contentWindow.document
      const bodyText = iframeDoc.body?.innerText || ''
      
      // 检查是否包含错误信息
      if (bodyText.includes('错误') || bodyText.includes('error') || bodyText.includes('无法加载')) {
        error.value = 'PDF 加载失败，请检查代理服务器'
        loading.value = false
        return
      }
    } catch (e) {
      // 跨域错误是正常的，说明 PDF 可能正在加载
      console.log('无法访问 iframe 内容（可能是跨域）:', e.message)
    }
    
    // 如果没有错误，认为加载成功
    if (!error.value) {
      console.log('✅ PDF 可能已成功加载')
    }
  } catch (e) {
    console.error('检查 iframe 内容失败:', e)
  }
}

// iframe 加载错误
const handleIframeError = () => {
  console.error('iframe 加载失败')
  loading.value = false
  error.value = 'PDF 加载失败，请检查代理服务器是否运行'
  ElMessage.error('PDF 加载失败')
  
  if (loadTimeout) {
    clearTimeout(loadTimeout)
    loadTimeout = null
  }
}

// 重试加载
const retryLoad = () => {
  error.value = ''
  loading.value = true
  // 强制重新加载 iframe
  if (iframeRef.value) {
    iframeRef.value.src = viewerUrl.value
  }
}

// 在新窗口打开 PDF
const openInNewWindow = () => {
  if (!props.pdfUrl) return
  
  // 直接打开原始 URL
  const newWindow = window.open(props.pdfUrl, '_blank')
  if (!newWindow) {
    ElMessage.warning('弹窗被阻止，请允许浏览器弹窗后重试')
  }
}

// 下载 PDF
const downloadPdf = async () => {
  if (!props.pdfUrl) return
  
  try {
    // 如果是网络 URL，通过代理下载
    if (props.pdfUrl.startsWith('http://') || props.pdfUrl.startsWith('https://')) {
      const proxyUrl = `${PROXY_BASE_URL}/pdf-proxy?url=${encodeURIComponent(props.pdfUrl)}`
      const link = document.createElement('a')
      link.href = proxyUrl
      link.download = props.reportTitle || 'report.pdf'
      link.target = '_blank'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    } else {
      // 本地文件直接下载
      const link = document.createElement('a')
      link.href = props.pdfUrl
      link.download = props.reportTitle || 'report.pdf'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    }
  } catch (err) {
    console.error('下载失败:', err)
    ElMessage.error('下载失败，请尝试在新窗口打开')
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

// 测试代理 URL
const testProxyUrl = () => {
  if (!props.pdfUrl || props.pdfUrl.startsWith('/')) {
    ElMessage.info('本地文件无需测试代理')
    return
  }
  
  const proxyUrl = `${PROXY_BASE_URL}/pdf-proxy?url=${encodeURIComponent(props.pdfUrl)}`
  console.log('测试代理 URL:', proxyUrl)
  
  // 在新窗口打开代理 URL
  const newWindow = window.open(proxyUrl, '_blank')
  if (!newWindow) {
    ElMessage.warning('弹窗被阻止，请允许浏览器弹窗')
  } else {
    ElMessage.success('正在新窗口测试代理 URL...')
  }
}

// 监听 PDF URL 变化
watch(() => props.pdfUrl, (newUrl) => {
  if (newUrl) {
    console.log('='.repeat(60))
    console.log('PDF URL 已更新:', newUrl)
    console.log('代理服务器地址:', PROXY_BASE_URL)
    
    // 重置状态
    error.value = ''
    loading.value = true
    
    // 设置超时检测
    if (loadTimeout) {
      clearTimeout(loadTimeout)
    }
    loadTimeout = setTimeout(() => {
      if (loading.value) {
        console.warn('⚠️ PDF 加载超时')
        loading.value = false
        error.value = 'PDF 加载超时，请检查网络连接或代理服务器'
      }
    }, 30000) // 30秒超时
    
    if (newUrl.startsWith('/')) {
      console.log('使用本地文件路径')
      console.log('查看器 URL:', viewerUrl.value)
      loading.value = false
    } else {
      const proxyUrl = `${PROXY_BASE_URL}/pdf-proxy?url=${encodeURIComponent(newUrl)}`
      console.log('使用代理服务器')
      console.log('代理 URL:', proxyUrl)
      console.log('查看器 URL:', viewerUrl.value)
      
      // 测试代理服务器是否可用
      fetch(`${PROXY_BASE_URL}/health`)
        .then(res => res.json())
        .then(data => {
          console.log('✅ 代理服务器健康检查通过:', data)
          
          // 测试代理 URL 是否能返回 PDF
          fetch(proxyUrl, { method: 'HEAD' })
            .then(res => {
              const contentType = res.headers.get('content-type')
              console.log('✅ 代理 URL 响应:', {
                status: res.status,
                contentType: contentType,
                ok: res.ok
              })
              
              if (res.ok && contentType && contentType.includes('pdf')) {
                console.log('✅ 代理 URL 可以正常返回 PDF')
                // 继续加载，不设置错误
              } else {
                console.warn('⚠️ 代理 URL 可能无法返回 PDF')
                error.value = '代理服务器返回的不是 PDF 文件，可能被反爬虫拦截'
                loading.value = false
              }
            })
            .catch(err => {
              console.error('❌ 测试代理 URL 失败:', err)
              error.value = `无法访问代理 URL: ${err.message}`
              loading.value = false
            })
        })
        .catch(err => {
          console.error('❌ 代理服务器不可用:', err)
          error.value = '代理服务器不可用，请检查 http://localhost:5000'
          loading.value = false
          ElMessage.warning('代理服务器可能未运行，请检查 http://localhost:5000')
        })
    }
    console.log('='.repeat(60))
  } else {
    loading.value = false
    error.value = ''
  }
}, { immediate: true })
</script>

<style scoped>
.pdf-viewer {
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

.pdf-iframe {
  width: 100%;
  height: 100%;
  border: none;
  background: white;
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

.error-state ul {
  margin: 10px 0;
  padding-left: 20px;
  text-align: left;
}

.error-actions {
  margin-top: 15px;
  display: flex;
  gap: 10px;
  justify-content: center;
}

.debug-info {
  position: absolute;
  top: 10px;
  right: 10px;
  max-width: 400px;
  z-index: 1000;
}
</style>
