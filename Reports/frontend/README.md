# 证券研究报告查看器

基于 Vite + Vue 3 + Element Plus 的前端应用，用于查看证券研究报告。

## 功能特点

- 📊 左右两列布局：左侧报告目录，右侧 PDF 查看器
- 📁 按类型分类展示报告（策略、行业、宏观、盈利预测）
- 📄 使用 PDF.js 直接渲染 PDF（不受 iframe 安全策略限制）
- 🔄 支持刷新报告列表
- 📥 支持下载 PDF 文件
- 🖥️ 支持全屏查看
- 🔍 支持页面导航和缩放控制
- ⚡ 自动检测当前页面并高亮显示

## 安装依赖

```bash
npm install
```

## 开发运行

```bash
npm run dev
```

应用将在 http://localhost:3000 启动

## 构建生产版本

```bash
npm run build
```

## 使用说明

1. 确保 Python 后端已生成 `reports.html` 文件
2. 将 `reports.html` 文件放在项目根目录或 `public` 目录下
3. 如果 PDF 文件是本地路径，需要：
   - 将 PDF 文件复制到 `public/pdfs` 目录，或
   - 配置后端 API 提供 PDF 文件服务

## 注意事项

- 浏览器安全限制，无法直接访问本地文件系统（如 `D:\Books\证券`）
- 如果 PDF 是网络链接，可以直接使用
- 如果 PDF 是本地文件，需要放在 `public` 目录下或通过服务器提供

