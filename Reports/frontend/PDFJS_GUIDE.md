# PDF.js 集成指南

## 概述

我们已经将 PDF 查看器从 iframe 方案升级为 **PDF.js** 方案，这是一个更强大、更灵活的 PDF 渲染解决方案。

## 优势

### ✅ 相比 iframe 的优势

1. **不受安全策略限制**：不依赖 iframe，绕过 X-Frame-Options 等安全策略
2. **完全控制**：可以自定义渲染、缩放、搜索等功能
3. **更好的性能**：按需渲染页面，支持虚拟滚动
4. **丰富的功能**：支持文本选择、搜索、注释等
5. **跨域支持**：通过 fetch 下载 PDF，支持 CORS（如果服务器允许）

### ⚠️ 注意事项

1. **CORS 限制**：如果 PDF 服务器不允许跨域访问，仍然无法加载
2. **文件大小**：大文件需要完全下载后才能显示
3. **内存占用**：所有页面都在内存中，大文件可能占用较多内存

## 功能特性

### 已实现功能

- ✅ PDF 加载和渲染
- ✅ 页面导航（上一页/下一页）
- ✅ 缩放控制（放大/缩小/适应）
- ✅ 自动滚动到当前页面
- ✅ 加载状态提示
- ✅ 错误处理和重试
- ✅ 全屏查看
- ✅ 下载功能

### 未来可扩展功能

- [ ] 文本搜索
- [ ] 文本选择复制
- [ ] 页面缩略图导航
- [ ] 打印功能
- [ ] 旋转页面
- [ ] 书签/注释

## 使用方法

### 安装依赖

```bash
cd frontend
npm install
```

PDF.js 已添加到 `package.json` 中：
```json
"pdfjs-dist": "^3.11.174"
```

### 基本使用

1. 从左侧目录选择报告
2. PDF 会自动加载并在右侧显示
3. 使用顶部控制栏进行导航和缩放

### 控制说明

- **页面导航**：使用 ← → 按钮或滚动页面
- **缩放**：使用 + - 按钮或"适应"按钮
- **下载**：点击下载按钮
- **全屏**：点击全屏按钮

## 技术实现

### PDF.js 配置

```javascript
import * as pdfjsLib from 'pdfjs-dist'

// 配置 worker（使用 CDN）
pdfjsLib.GlobalWorkerOptions.workerSrc = 
  `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.js`
```

### 加载流程

1. **获取 PDF 数据**：使用 `fetch` 下载 PDF 文件
2. **解析 PDF**：使用 `pdfjsLib.getDocument()` 解析
3. **渲染页面**：将每一页渲染到 Canvas 上
4. **显示**：在页面中显示所有 Canvas

### 代码结构

```javascript
// 加载 PDF
const loadPdf = async () => {
  const response = await fetch(pdfUrl)
  const arrayBuffer = await response.arrayBuffer()
  const pdfDoc = await pdfjsLib.getDocument({ data: arrayBuffer }).promise
  
  // 渲染所有页面
  for (let pageNum = 1; pageNum <= pdfDoc.numPages; pageNum++) {
    const page = await pdfDoc.getPage(pageNum)
    await renderPageToCanvas(page, canvas)
  }
}
```

## 故障排除

### 问题：PDF 无法加载

**可能原因**：
1. CORS 跨域限制
2. 网络连接问题
3. PDF 文件不存在

**解决方案**：
- 检查浏览器控制台的错误信息
- 如果显示 CORS 错误，使用"在新窗口打开"功能
- 检查网络连接

### 问题：PDF 加载很慢

**可能原因**：
- PDF 文件很大
- 网络速度慢

**解决方案**：
- 等待加载完成（会显示加载进度）
- 考虑实现分页加载（只加载可见页面）

### 问题：页面显示不完整

**可能原因**：
- 缩放比例不合适

**解决方案**：
- 点击"适应"按钮自动调整缩放
- 手动调整缩放比例

## 性能优化建议

### 当前实现

- 所有页面一次性渲染（适合小文件）
- 使用 Canvas 渲染（性能好）

### 未来优化

1. **虚拟滚动**：只渲染可见页面
2. **懒加载**：按需加载页面
3. **缓存**：缓存已渲染的页面
4. **Web Worker**：在后台线程处理 PDF 解析

## 与 iframe 方案对比

| 特性 | iframe | PDF.js |
|------|--------|--------|
| 安全策略限制 | ❌ 受限制 | ✅ 不受限制 |
| 跨域支持 | ⚠️ 部分支持 | ⚠️ 需要 CORS |
| 功能控制 | ❌ 有限 | ✅ 完全控制 |
| 性能 | ✅ 好 | ✅ 好 |
| 文件大小限制 | ✅ 无限制 | ⚠️ 受内存限制 |
| 实现复杂度 | ✅ 简单 | ⚠️ 较复杂 |

## 更新日志

### v2.0.0 (当前版本)
- ✅ 集成 PDF.js 替代 iframe
- ✅ 实现页面导航
- ✅ 实现缩放控制
- ✅ 添加加载状态和错误处理
- ✅ 优化用户体验

### v1.0.0
- ✅ 基础 iframe PDF 查看功能

