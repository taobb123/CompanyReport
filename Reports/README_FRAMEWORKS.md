# 爬虫框架推荐与反爬虫解决方案

## 问题分析

当前遇到的问题是：即使添加了Referer头，东方财富服务器仍然返回JavaScript代码而不是PDF文件。这说明：

1. **需要完整的浏览器环境**：服务器可能检测浏览器指纹
2. **需要Cookie/Session**：可能需要先访问详情页建立会话
3. **需要JavaScript执行**：PDF链接可能是动态生成的

## 推荐的爬虫框架

### 1. **Playwright（强烈推荐）** ⭐⭐⭐⭐⭐

**优势：**
- 更现代、更强大的浏览器自动化工具
- 原生支持下载拦截和文件下载
- 更好的反检测能力（隐藏自动化特征）
- 支持多浏览器（Chromium、Firefox、WebKit）
- 更快的执行速度

**安装：**
```bash
pip install playwright
playwright install chromium
```

**使用示例：**
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    # 访问详情页建立会话
    page.goto(detail_url)
    
    # 等待PDF下载
    with page.expect_download() as download_info:
        page.goto(pdf_url)
    
    download = download_info.value
    download.save_as(save_path)
```

### 2. **Selenium（当前使用）** ⭐⭐⭐⭐

**优势：**
- 成熟稳定，社区支持好
- 支持多种浏览器
- 可以完全模拟浏览器行为

**劣势：**
- 容易被检测为自动化工具
- 需要额外的驱动管理

**改进建议：**
- 使用 `undetected-chromedriver` 隐藏自动化特征
- 添加随机延迟和人类行为模拟

### 3. **Scrapy + Selenium/Playwright** ⭐⭐⭐⭐

**优势：**
- 强大的爬虫框架
- 支持分布式爬取
- 内置去重、重试等机制

**适用场景：**
- 大规模数据采集
- 需要调度和监控

## 当前实现的解决方案

### 方案1：Selenium浏览器下载（已实现）

在 `infrastructure/selenium_downloader.py` 中实现了：
- 通过浏览器直接访问PDF URL
- 自动处理Cookie和Session
- 从浏览器网络日志中提取PDF

### 方案2：Playwright下载（已实现）

在 `infrastructure/playwright_client.py` 中实现了：
- 使用Playwright的下载拦截功能
- 更可靠的文件下载

## 使用建议

### 当前系统（推荐）

系统已自动检测Selenium客户端，并优先使用浏览器方式下载PDF：

```python
# 系统会自动使用Selenium下载器
crawler = create_crawler_service()
crawler.crawl_reports('strategy', limit=6)
```

### 切换到Playwright（可选）

如果需要更好的反检测能力，可以修改 `main.py`：

```python
from infrastructure.playwright_client import PlaywrightHttpClient

# 使用Playwright替代Selenium
http_client = PlaywrightHttpClient(timeout=30, headless=True)
```

## 其他反爬虫策略

### 1. **请求头伪装**
- ✅ 已实现：完整的User-Agent、Accept等
- ✅ 已实现：Referer头

### 2. **Cookie管理**
- ✅ Selenium自动处理Cookie
- 可以手动添加Cookie（如果需要）

### 3. **请求频率控制**
- ✅ 已实现：并发控制（max_workers=6）
- 可以添加随机延迟

### 4. **代理IP池**（可选）
```python
# 如果需要，可以添加代理
chrome_options.add_argument('--proxy-server=http://proxy:port')
```

### 5. **undetected-chromedriver**（可选）
```bash
pip install undetected-chromedriver
```

可以更好地隐藏自动化特征。

## 最佳实践

1. **优先使用Playwright**：更现代、更可靠
2. **保持会话**：先访问详情页，再下载PDF
3. **验证文件**：检查PDF文件头（%PDF-）
4. **错误处理**：详细的日志和错误信息
5. **合理频率**：避免过于频繁的请求

## 故障排查

如果仍然下载失败：

1. **检查网络日志**：查看实际返回的内容
2. **手动测试**：在浏览器中手动访问PDF URL
3. **检查Cookie**：可能需要登录或特定Cookie
4. **尝试非无头模式**：`headless=False` 查看实际行为

## 总结

当前系统已经实现了：
- ✅ Selenium浏览器下载（自动检测）
- ✅ Playwright支持（可选）
- ✅ Referer头处理
- ✅ PDF文件验证

**推荐使用当前的Selenium方案**，如果仍有问题，可以切换到Playwright。

