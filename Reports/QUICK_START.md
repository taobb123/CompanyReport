# 快速启动指南 - 彻底解决 PDF 查看问题

## 🎯 推荐方案：静态服务器（最可靠）

### 方案 A：优化版服务器（推荐，解决线程和反爬虫问题）

```bash
# 在项目根目录
python backend_static_server_optimized.py
```

**优化内容**：
- ✅ 解决线程问题（主线程运行）
- ✅ 增强反检测能力
- ✅ 模拟真实用户行为
- ✅ 改进会话管理

### 方案 B：原版服务器（备选）

```bash
# 在项目根目录
python backend_static_server.py
```

你应该看到：
```
============================================================
PDF 静态文件服务器
============================================================
服务地址: http://localhost:5001
缓存目录: ...\pdf_cache
============================================================
```

### 第二步：启动前端

```bash
cd frontend
npm install  # 如果还没安装依赖
npm run dev
```

### 第三步：测试

1. 打开浏览器访问前端（通常是 `http://localhost:3000`）
2. 从左侧目录选择一个报告
3. 前端会自动请求静态服务器下载 PDF
4. 下载完成后，PDF 会显示在右侧

## 🔄 工作流程

```
用户选择报告
    ↓
前端请求: GET /download-and-serve?url=PDF_URL
    ↓
静态服务器检查缓存
    ↓
如果不存在 → 使用 Playwright 下载到本地
    ↓
返回本地文件 URL: /pdf/filename.pdf
    ↓
前端用 iframe 显示本地 PDF ✅
```

## 📦 备选方案：vue3-pdf-app

如果静态服务器方案有问题，可以使用 `vue3-pdf-app`：

### 第一步：安装依赖

```bash
cd frontend
npm install vue3-pdf-app
```

### 第二步：更新 App.vue

```vue
// 注释掉 PdfViewerV3
// import PdfViewerV3 from './components/PdfViewerV3.vue'

// 使用 PdfViewerV2
import PdfViewerV2 from './components/PdfViewerV2.vue'
```

```vue
<!-- 替换组件 -->
<PdfViewerV2 
  :pdf-url="selectedPdfUrl"
  :report-title="selectedReport?.report_info?.title"
/>
```

### 第三步：启动前端

```bash
npm run dev
```

## 🛠️ 故障排除

### 问题 1：静态服务器启动失败

**错误**：`无法导入项目模块`

**解决**：
```bash
# 确保在项目根目录
cd C:\Users\111\Desktop\Reports

# 检查依赖
pip install flask flask-cors playwright

# 安装 Playwright 浏览器
playwright install chromium
```

### 问题 2：PDF 下载失败

**检查**：
- 查看静态服务器终端输出
- 确认原始 PDF URL 是否可访问

**解决**：
- 查看详细错误日志
- 尝试手动访问原始 PDF URL

### 问题 3：前端无法连接静态服务器

**检查**：
- 静态服务器是否运行在 5001 端口
- 浏览器控制台是否有 CORS 错误

**解决**：
```bash
# 检查端口占用
netstat -ano | findstr :5001

# 重启静态服务器
```

## 📝 环境变量配置（可选）

创建 `frontend/.env`：

```env
# 静态服务器地址
VITE_STATIC_SERVER_URL=http://localhost:5001

# 如果使用 vue3-pdf-app，配置代理服务器
VITE_PROXY_URL=http://localhost:5000
```

## ✅ 验证步骤

1. ✅ 静态服务器运行在 5001 端口
2. ✅ 前端运行在 3000 端口
3. ✅ 选择报告后，能看到下载进度
4. ✅ PDF 成功显示在右侧

## 🎉 成功标志

- 静态服务器显示：`[成功] ✅ PDF 下载成功`
- 前端显示：PDF 内容正常显示
- 浏览器控制台：无错误信息

## 📚 更多信息

- 详细方案说明：`COMPLETE_SOLUTION.md`
- 解决方案文档：`SOLUTION_COMPLETE.md`

