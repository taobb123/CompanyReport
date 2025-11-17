# 研报数据API使用说明

## 功能概述

本系统实现了从东方财富网站动态获取研报数据的功能，**支持缓存机制**，避免重复爬取，提升性能。

### 核心特性

1. **智能缓存**：每个报告类型独立缓存，有效期24小时
2. **混合返回**：部分类型使用缓存，部分类型重新爬取
3. **强制刷新**：支持忽略缓存强制重新爬取
4. **前端联动**：类型选择器与报告目录联动，自动展开和高亮

### 支持的研报类型

- **策略报告** (strategy): https://data.eastmoney.com/report/strategyreport.jshtml
- **行业研报** (industry): https://data.eastmoney.com/report/industry.jshtml
- **宏观研究** (macro): https://data.eastmoney.com/report/macresearch.jshtml
- **个股研报** (stock): https://data.eastmoney.com/report/stock.jshtml

## 实现步骤

### 第一步：找到对应标题
系统使用 Playwright 动态爬取网页，解析 HTML 结构，提取报告标题。

### 第二步：获取PDF链接
系统访问每个报告的详情页，提取 PDF 链接。

### 第三步：展示在前端
前端通过 API 获取数据，按类型分类展示，支持点击在新窗口打开 PDF。

## 后端API

### 启动后端服务

```bash
python backend_proxy.py
```

服务将在 `http://localhost:5000` 启动。

### API端点

#### 获取报告数据

**URL**: `/api/reports`

**方法**: `GET`

**参数**:
- `type` (可选): 报告类型，支持：
  - `all`: 获取所有类型（默认）
  - 单个类型: `strategy`, `industry`, `macro`, `stock`
  - 多个类型（逗号分隔）: `strategy,industry` 或 `strategy,industry,macro`
- `limit` (可选): 每种类型获取的数量，默认 `6`，范围：1-50
- `force` (可选): 是否强制刷新（忽略缓存），默认 `false`

**示例**:
```bash
# 获取所有类型的报告，每种类型6篇
curl http://localhost:5000/api/reports?type=all&limit=6

# 只获取行业研报，10篇
curl http://localhost:5000/api/reports?type=industry&limit=10

# 只获取个股研报，5篇
curl http://localhost:5000/api/reports?type=stock&limit=5

# 获取多个类型：策略报告和行业研报，每种8篇
curl http://localhost:5000/api/reports?type=strategy,industry&limit=8

# 获取三个类型：策略、行业、宏观，每种5篇
curl http://localhost:5000/api/reports?type=strategy,industry,macro&limit=5

# 强制刷新（忽略缓存）
curl http://localhost:5000/api/reports?type=industry&limit=10&force=true
```

**响应格式**:
```json
{
  "success": true,
  "data": [
    {
      "url": "https://pdf.dfcfw.com/...",
      "filename": "report_xxx.pdf",
      "report_info": {
        "title": "报告标题",
        "date": "2024-01-01",
        "detail_url": "https://data.eastmoney.com/report/...",
        "report_type": "industry"
      }
    }
  ],
  "count": 30,
  "by_type": {
    "strategy": 6,
    "industry": 6,
    "macro": 6,
    "stock": 6
  },
  "requested_types": ["strategy", "industry", "macro", "stock"],
  "limit": 6,
  "cache_status": {
    "strategy": "cached",
    "industry": "fetched",
    "macro": "cached",
    "stock": "fetched",
    "profit": "cached"
  },
  "force_refresh": false
}
```

**缓存状态说明**:
- `cached`: 使用缓存数据
- `fetched`: 新抓取的数据
- `force_refresh`: 强制刷新抓取
- `fetching`: 正在抓取中
- `error`: 抓取失败
```

## 前端使用

### 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端将在 `http://localhost:5173` 启动（或 Vite 配置的端口）。

### 配置API地址

在 `frontend/.env` 或 `frontend/.env.local` 中配置：

```
VITE_API_URL=http://localhost:5000
```

如果不配置，默认使用 `http://localhost:5000`。

### 功能说明

1. **类型选择**: 页面顶部提供类型选择器，支持：
   - 选择单个或多个报告类型
   - 全选/清空快捷操作
   - 设置每种类型的获取数量（1-20篇）
   - **联动功能**：选择类型时，目录自动展开并高亮对应分类
2. **智能刷新**: 刷新按钮支持两种模式：
   - **普通刷新**：使用缓存（如果有效），只抓取过期类型
   - **强制刷新**：忽略缓存，重新抓取所有类型
3. **缓存机制**：
   - 每个类型+数量组合独立缓存
   - 缓存有效期：24小时
   - 自动检测缓存有效性
   - 混合返回：部分使用缓存，部分重新抓取
4. **分类展示**: 报告按类型分组展示，支持折叠/展开
5. **点击打开**: 点击报告链接，在新窗口打开 PDF（避免反爬虫拦截）

### 使用流程

1. **选择类型**: 在左侧类型选择器中勾选需要的报告类型（会自动展开对应目录）
2. **设置数量**: 调整"篇/类型"输入框，设置每种类型获取的数量
3. **刷新数据**: 
   - 点击"刷新报告"按钮选择"普通刷新"：使用缓存（如果有效）
   - 点击"刷新报告"按钮选择"强制刷新"：忽略缓存，重新抓取
4. **查看报告**: 在左侧目录中按类型查看报告，点击链接在新窗口打开
5. **缓存提示**: 刷新后会显示哪些类型使用了缓存，哪些是新抓取的

## 技术实现

### 后端
- 使用 **Playwright** 处理 JavaScript 动态内容
- 使用 **BeautifulSoup** 解析 HTML
- 使用 **Flask** 提供 RESTful API

### 前端
- 使用 **Vue 3** + **Element Plus** 构建界面
- 使用 **fetch API** 获取数据
- 响应式设计，支持分类展示

## 缓存机制

### 缓存存储
- 缓存文件位置：`cache/reports_cache.json`
- 缓存格式：JSON文件
- 缓存键格式：`{report_type}_{limit}`（如：`strategy_6`）

### 缓存策略
- **有效期**：24小时（从首次抓取时间开始计算）
- **自动清理**：后端启动时自动清理过期缓存
- **混合返回**：如果请求多个类型，部分过期、部分有效，只抓取过期类型，有效类型使用缓存

### 缓存管理API

#### 获取缓存状态
```bash
curl http://localhost:5000/api/cache/status
```

#### 清除缓存
```bash
# 清除所有缓存
curl -X POST http://localhost:5000/api/cache/clear

# 清除特定类型的缓存（需要传递JSON）
curl -X POST http://localhost:5000/api/cache/clear \
  -H "Content-Type: application/json" \
  -d '{"type": "industry"}'
```

## 注意事项

1. **反爬虫**: 系统使用 Playwright 模拟浏览器，可以绕过大部分反爬虫机制
2. **性能**: 
   - 使用缓存时响应速度很快（毫秒级）
   - 需要抓取时，每次 API 请求都会创建新的浏览器实例，可能需要几秒到几十秒
3. **缓存目录**: 缓存文件存储在 `cache/` 目录，建议添加到 `.gitignore`
4. **稳定性**: 如果网站结构变化，可能需要更新解析逻辑或清除缓存
5. **合规性**: 请遵守网站的使用条款，仅用于学习和研究目的

## 故障排除

### 后端无法启动
- 确保已安装 Playwright: `pip install playwright && playwright install chromium`
- 检查端口 5000 是否被占用

### 前端无法获取数据
- 确保后端服务正在运行
- 检查浏览器控制台的错误信息
- 确认 API 地址配置正确

### 无法获取PDF链接
- 检查网络连接
- 查看后端日志，确认爬取过程
- 可能需要更新解析逻辑以适应网站结构变化

