# 快速开始指南

## 第一步：安装依赖

```bash
cd frontend
npm install
```

## 第二步：准备数据文件

### 方式 1：自动加载（推荐）

将 Python 后端生成的 `reports.html` 文件复制到：

```
frontend/public/reports.html
```

### 方式 2：手动选择

如果文件在其他位置，应用启动后会提示你手动选择文件。

## 第三步：处理 PDF 文件（如果需要）

如果你的 PDF 是本地文件路径，需要：

1. 在 `frontend/public` 目录下创建 `pdfs` 文件夹
2. 将 PDF 文件复制到 `frontend/public/pdfs/` 目录
3. 确保文件名与 `reports.html` 中的链接匹配

**注意**：如果 PDF 链接是网络 URL（http:// 或 https://），则无需此步骤。

## 第四步：启动应用

```bash
npm run dev
```

浏览器会自动打开 http://localhost:3000

## 使用说明

1. **查看报告**：在左侧目录中点击任意报告，右侧会显示 PDF 内容
2. **刷新数据**：点击右上角的"刷新报告"按钮重新加载数据
3. **下载 PDF**：在 PDF 查看器中点击"下载"按钮
4. **全屏查看**：点击"全屏"按钮进入全屏模式

## 常见问题

### Q: 提示"无法加载 reports.html"

**A**: 确保文件在 `frontend/public/reports.html`，或点击提示手动选择文件。

### Q: PDF 无法显示

**A**: 
- 检查 PDF 链接是否有效
- 如果是本地文件，确保文件在 `public/pdfs` 目录
- 检查浏览器控制台是否有错误信息

### Q: 如何更新报告数据？

**A**: 
1. 运行 Python 后端生成新的 `reports.html`
2. 将新文件复制到 `frontend/public/reports.html`
3. 在前端应用中点击"刷新报告"按钮

## 项目结构说明

```
frontend/
├── public/              # 静态文件（需要放置 reports.html 和 pdfs/）
│   ├── reports.html     # 报告数据文件（从后端生成）
│   └── pdfs/           # PDF 文件目录（可选）
├── src/
│   ├── components/      # Vue 组件
│   ├── utils/          # 工具函数
│   └── App.vue         # 主应用
└── package.json        # 项目配置
```

