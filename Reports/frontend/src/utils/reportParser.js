/**
 * 从 HTML 报告中解析报告数据
 */

/**
 * 解析 reports.html 文件，提取报告信息
 * @returns {Promise<Array>} 报告数据数组
 */
export async function parseReportsFromHtml() {
  try {
    // 尝试从不同路径加载 reports.html
    // 注意：浏览器无法直接访问本地文件系统，需要将文件放在 public 目录或通过服务器提供
    const possiblePaths = [
      '/reports.html',  // public 目录
      './reports.html',  // 当前目录
      '../reports.html',  // 上级目录
    ]
    
    let htmlContent = null
    
    // 尝试通过 fetch 加载（适用于开发环境）
    for (const path of possiblePaths) {
      try {
        const response = await fetch(path)
        if (response.ok) {
          htmlContent = await response.text()
          console.log(`成功从 ${path} 加载 reports.html`)
          break
        }
      } catch (e) {
        // 继续尝试下一个路径
        console.log(`无法从 ${path} 加载:`, e.message)
        continue
      }
    }
    
    // 如果 fetch 失败，提示用户选择文件
    if (!htmlContent) {
      console.warn('无法自动加载 reports.html，尝试手动选择文件')
      const userChoice = confirm(
        '无法自动找到 reports.html 文件。\n\n' +
        '请选择：\n' +
        '1. 点击"确定"手动选择文件\n' +
        '2. 点击"取消"将文件放在 frontend/public/reports.html 后刷新页面'
      )
      
      if (userChoice) {
        htmlContent = await loadHtmlFromFile()
      } else {
        throw new Error('请将 reports.html 文件放在 public 目录下，然后刷新页面')
      }
    }
    
    if (!htmlContent) {
      throw new Error('无法加载 reports.html 文件。请确保文件在 public 目录下，或手动选择文件。')
    }
    
    // 解析 HTML
    const parser = new DOMParser()
    const doc = parser.parseFromString(htmlContent, 'text/html')
    
    // 提取报告数据
    const reports = []
    const sections = doc.querySelectorAll('.section')
    
    sections.forEach(section => {
      const sectionTitle = section.querySelector('.section-title')
      if (!sectionTitle) return
      
      // 提取报告类型
      const typeText = sectionTitle.textContent.trim()
      const reportType = getReportTypeFromName(typeText)
      
      // 提取报告列表
      const reportItems = section.querySelectorAll('.report-item')
      
      reportItems.forEach(item => {
        const titleEl = item.querySelector('.report-title')
        const dateEl = item.querySelector('.report-date')
        const linkEl = item.querySelector('.report-link')
        
        if (!titleEl || !linkEl) return
        
        const title = titleEl.textContent.trim()
        const date = dateEl ? dateEl.textContent.trim() : '未知日期'
        const url = linkEl.getAttribute('href')
        
        if (url) {
          // 转换本地路径为可访问的 URL
          const accessibleUrl = convertLocalPathToUrl(url)
          
          reports.push({
            url: accessibleUrl,
            originalUrl: url, // 保留原始 URL
            filename: extractFilenameFromUrl(url),
            report_info: {
              title: title,
              date: date,
              detail_url: url,
              report_type: reportType
            }
          })
        }
      })
    })
    
    return reports
  } catch (error) {
    console.error('解析报告失败:', error)
    throw error
  }
}

/**
 * 从类型名称获取报告类型代码
 */
function getReportTypeFromName(name) {
  if (name.includes('策略')) return 'strategy'
  if (name.includes('行业')) return 'industry'
  if (name.includes('宏观')) return 'macro'
  if (name.includes('个股')) return 'stock'
  return 'unknown'
}

/**
 * 从 URL 提取文件名
 */
function extractFilenameFromUrl(url) {
  try {
    const urlObj = new URL(url)
    const pathname = urlObj.pathname
    const filename = pathname.split('/').pop()
    return filename || 'report.pdf'
  } catch (e) {
    // 如果不是完整 URL，可能是相对路径
    const parts = url.split('/')
    return parts[parts.length - 1] || 'report.pdf'
  }
}

/**
 * 通过文件输入加载 HTML
 */
function loadHtmlFromFile() {
  return new Promise((resolve) => {
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = '.html'
    input.onchange = (e) => {
      const file = e.target.files[0]
      if (file) {
        const reader = new FileReader()
        reader.onload = (e) => resolve(e.target.result)
        reader.onerror = () => resolve(null)
        reader.readAsText(file)
      } else {
        resolve(null)
      }
    }
    input.click()
  })
}

/**
 * 将本地文件路径转换为可访问的 URL
 * 注意：浏览器安全限制，无法直接访问本地文件系统
 * 需要将 PDF 文件放在 public 目录或通过服务器提供
 */
export function convertLocalPathToUrl(localPath) {
  if (!localPath) return ''
  
  // 如果是网络 URL，直接返回
  if (localPath.startsWith('http://') || localPath.startsWith('https://')) {
    return localPath
  }
  
  // 如果已经是相对路径（以 / 开头），直接返回
  if (localPath.startsWith('/')) {
    return localPath
  }
  
  // 如果是本地文件路径（Windows 或 Unix 路径），尝试转换为相对路径
  // 假设 PDF 文件在 public/pdfs 目录下
  if (localPath.includes('\\') || localPath.includes('/')) {
    const filename = localPath.split(/[/\\]/).pop()
    // 移除可能的查询参数
    const cleanFilename = filename.split('?')[0]
    return `/pdfs/${cleanFilename}`
  }
  
  // 如果只是文件名，假设在 pdfs 目录下
  return `/pdfs/${localPath}`
}

