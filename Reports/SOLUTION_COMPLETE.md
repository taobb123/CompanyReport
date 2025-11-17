# 完整解决方案 - 使用现成的 PDF 查看器组件

## 问题总结

当前遇到的核心问题：
1. PDF 服务器返回 JavaScript 反爬虫页面，而不是真正的 PDF
2. 即使使用 Playwright，仍然无法完全绕过反爬虫
3. 需要更可靠的 PDF 查看方案

## 推荐方案：vue3-pdf-app

使用现成的 `vue3-pdf-app` 组件，这是一个功能完整的 Vue 3 PDF 查看器。

### 优势

1. ✅ **现成组件**：无需自己实现 PDF 渲染逻辑
2. ✅ **功能完整**：包含工具栏、缩放、搜索、打印等
3. ✅ **易于集成**：专为 Vue 3 设计
4. ✅ **支持代理**：可以通过代理 URL 加载 PDF
5. ✅ **错误处理**：内置错误处理机制

## 实施步骤

### 1. 安装依赖

```bash
cd frontend
npm install vue3-pdf-app
```

### 2. 更新组件

我已经创建了 `PdfViewerV2.vue`，使用 `vue3-pdf-app` 组件。

### 3. 替换组件

在 `App.vue` 中，将 `PdfViewer` 替换为 `PdfViewerV2`：

```vue
import PdfViewerV2 from './components/PdfViewerV2.vue'
```

### 4. 改进代理服务器

确保代理服务器能正确返回 PDF。如果 Playwright 仍然失败，考虑：

#### 方案 A：先下载到本地，再提供静态服务

修改代理服务器，先下载 PDF 到本地，然后提供静态文件服务：

```python
# 下载 PDF 到本地缓存
# 然后返回本地文件路径
```

#### 方案 B：使用更完善的 Playwright 配置

改进 Playwright 的使用方式，增加更多反检测措施。

## 备选方案

### 方案 1：vue-pdf-embed（简单轻量）

如果 `vue3-pdf-app` 有问题，可以使用更简单的 `vue-pdf-embed`：

```bash
npm install vue-pdf-embed
```

### 方案 2：本地部署 PDF.js 查看器

下载 PDF.js 查看器到本地，避免使用官方 CDN：

1. 下载 PDF.js 查看器
2. 放在 `public/pdfjs/` 目录
3. 使用本地查看器

### 方案 3：后端下载 + 静态服务

1. 后端先下载 PDF 到本地（使用现有的下载逻辑）
2. 将 PDF 保存到 `public/pdfs/` 目录
3. 前端直接访问本地 PDF 文件

## 推荐实施顺序

### 第一步：使用 vue3-pdf-app（最简单）

1. 安装 `vue3-pdf-app`
2. 使用 `PdfViewerV2.vue` 组件
3. 测试是否能正常显示

### 第二步：如果仍然失败，改进代理服务器

1. 确保 Playwright 正确初始化
2. 增加更多等待时间
3. 使用非无头模式调试

### 第三步：如果代理仍然失败，使用本地下载方案

1. 后端先下载 PDF 到本地
2. 提供静态文件服务
3. 前端访问本地文件

## 快速开始

### 使用 vue3-pdf-app

```bash
# 1. 安装
cd frontend
npm install vue3-pdf-app

# 2. 更新 App.vue
# 将 PdfViewer 改为 PdfViewerV2

# 3. 重启前端
npm run dev
```

### 使用本地下载方案

如果代理仍然失败，可以：

1. 运行 Python 爬虫下载 PDF 到本地
2. 将 PDF 复制到 `frontend/public/pdfs/` 目录
3. 前端直接访问本地文件

## 长期解决方案

### 方案 A：混合方案（推荐）

1. **优先使用代理**：尝试通过代理获取 PDF
2. **失败时使用本地**：如果代理失败，检查本地是否有缓存
3. **自动下载**：如果本地也没有，触发后台下载

### 方案 B：完全本地化

1. 定期运行爬虫下载 PDF
2. 所有 PDF 存储在本地
3. 前端直接访问本地文件
4. 无需代理服务器

## 下一步

1. **立即尝试**：安装 `vue3-pdf-app` 并使用 `PdfViewerV2.vue`
2. **如果成功**：问题解决
3. **如果失败**：考虑使用本地下载方案

让我知道你想先尝试哪个方案，我可以帮你实施。

