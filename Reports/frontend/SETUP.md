# 前端项目设置说明

## 快速开始

### 1. 安装依赖

```bash
cd frontend
npm install
```

### 2. 准备 reports.html 文件

将 Python 后端生成的 `reports.html` 文件放在以下位置之一：

- **推荐**：放在 `frontend/public/reports.html`
- 或者：放在项目根目录 `frontend/reports.html`

### 3. 处理 PDF 文件

由于浏览器安全限制，无法直接访问本地文件系统（如 `D:\Books\证券`）。有以下几种方案：

#### 方案 A：使用网络链接（推荐）

如果 `reports.html` 中的 PDF 链接是网络 URL（如 `https://...`），则可以直接使用，无需额外配置。

#### 方案 B：将 PDF 文件放在 public 目录

1. 在 `frontend/public` 目录下创建 `pdfs` 文件夹
2. 将 PDF 文件复制到 `frontend/public/pdfs/` 目录
3. 修改 `reports.html` 中的链接为相对路径，如 `/pdfs/报告名称.pdf`

#### 方案 C：使用后端 API（未来扩展）

可以创建一个简单的后端服务来提供 PDF 文件，这样就不需要移动文件了。

### 4. 启动开发服务器

```bash
npm run dev
```

应用将在 http://localhost:3000 启动

## 项目结构

```
frontend/
├── public/           # 静态文件目录
│   ├── reports.html  # 报告 HTML 文件（需要手动放置）
│   └── pdfs/         # PDF 文件目录（可选）
├── src/
│   ├── components/   # Vue 组件
│   │   ├── ReportDirectory.vue  # 左侧报告目录
│   │   └── PdfViewer.vue        # 右侧 PDF 查看器
│   ├── utils/        # 工具函数
│   │   └── reportParser.js      # HTML 解析器
│   ├── App.vue       # 主应用组件
│   └── main.js       # 入口文件
├── index.html        # HTML 模板
├── package.json      # 项目配置
└── vite.config.js    # Vite 配置
```

## 功能说明

### 左侧报告目录

- 按类型分类显示报告（策略、行业、宏观、盈利预测）
- 点击报告项可在右侧查看 PDF
- 支持折叠/展开不同类型
- 显示报告标题和日期

### 右侧 PDF 查看器

- 使用 iframe 内嵌显示 PDF
- 支持下载 PDF 文件
- 支持全屏查看
- 显示当前查看的报告标题

## 注意事项

1. **文件路径问题**：浏览器无法直接访问本地文件系统，必须通过 HTTP 服务器访问
2. **CORS 问题**：如果 PDF 链接来自其他域名，可能遇到跨域问题
3. **文件大小**：大型 PDF 文件加载可能需要时间

## 故障排除

### 问题：无法加载 reports.html

**解决方案**：
- 确保文件在 `public` 目录下
- 检查文件名是否正确
- 尝试手动选择文件（应用会提示）

### 问题：PDF 无法显示

**可能原因**：
1. PDF 链接无效或文件不存在
2. 跨域问题（网络链接）
3. 文件路径错误（本地文件）

**解决方案**：
- 检查 PDF 链接是否可访问
- 将 PDF 文件放在 `public/pdfs` 目录
- 使用网络链接而不是本地路径

