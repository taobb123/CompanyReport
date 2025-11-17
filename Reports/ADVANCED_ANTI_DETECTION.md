# 高级反检测方案

如果优化版服务器仍然无法绕过反爬虫，可以尝试以下高级方案：

## 方案 1：使用 undetected-playwright

### 安装

```bash
pip install undetected-playwright
```

### 使用

创建一个新的服务器文件 `backend_static_server_undetected.py`：

```python
import undetected_playwright as up

# 使用 undetected-playwright
browser = up.chromium.launch(headless=True)
```

## 方案 2：使用 playwright-stealth

### 安装

```bash
pip install playwright-stealth
```

### 使用

```python
from playwright_stealth import stealth_sync

# 在创建页面后
stealth_sync(page)
```

## 方案 3：手动 Cookie 管理

### 步骤

1. **在浏览器中手动访问**：
   - 打开 `https://data.eastmoney.com/report/`
   - 等待页面完全加载
   - 打开开发者工具（F12）
   - 在 Application/Storage > Cookies 中导出 Cookie

2. **在代码中使用**：

```python
# 从浏览器导出的 Cookie
cookies = [
    {'name': 'cookie1', 'value': 'value1', 'domain': '.eastmoney.com'},
    # ... 更多 Cookie
]

# 在 Playwright 中使用
context.add_cookies(cookies)
```

## 方案 4：使用代理 IP 轮换

### 配置代理池

```python
proxies = [
    {"server": "http://proxy1.example.com:8080"},
    {"server": "http://proxy2.example.com:8080"},
    # ... 更多代理
]

# 随机选择代理
import random
proxy = random.choice(proxies)

browser = playwright.chromium.launch(
    headless=True,
    proxy=proxy
)
```

## 方案 5：使用 CDP (Chrome DevTools Protocol)

### 启用 CDP

```python
# 启动浏览器时启用 CDP
browser = playwright.chromium.launch(
    headless=True,
    args=['--remote-debugging-port=9222']
)

# 使用 CDP 命令隐藏自动化特征
context = browser.new_context()
cdp_session = context.new_cdp_session(page)
cdp_session.execute('Page.addScriptToEvaluateOnNewDocument', {
    'source': '''
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    '''
})
```

## 方案 6：模拟完整用户流程

### 完整流程

```python
# 1. 访问首页
page.goto('https://data.eastmoney.com/')

# 2. 等待并模拟用户行为
time.sleep(2)
page.mouse.move(100, 100)  # 模拟鼠标移动
time.sleep(1)

# 3. 访问报告列表页
page.goto('https://data.eastmoney.com/report/')
time.sleep(3)

# 4. 滚动页面（模拟浏览）
page.evaluate("window.scrollTo(0, 500)")
time.sleep(1)
page.evaluate("window.scrollTo(0, 1000)")
time.sleep(1)

# 5. 访问详情页
page.goto(detail_url)
time.sleep(5)

# 6. 点击 PDF 链接（如果存在）
try:
    pdf_link = page.query_selector('a[href*="pdf.dfcfw.com"]')
    if pdf_link:
        pdf_link.click()
        time.sleep(3)
except:
    pass

# 7. 访问 PDF URL
page.goto(pdf_url)
```

## 方案 7：使用专业反爬虫服务

### ScraperAPI

```python
import requests

# 使用 ScraperAPI
response = requests.get(
    'http://api.scraperapi.com',
    params={
        'api_key': 'YOUR_API_KEY',
        'url': pdf_url
    }
)
```

### Bright Data

```python
# 使用 Bright Data 代理
browser = playwright.chromium.launch(
    headless=True,
    proxy={
        "server": "http://brd-customer-xxx:xxx@zproxy.lum-superproxy.io:22225"
    }
)
```

## 方案 8：延迟和重试策略

### 智能重试

```python
import random
import time

def download_with_retry(pdf_url, max_retries=3):
    for attempt in range(max_retries):
        try:
            # 随机延迟（模拟人类行为）
            delay = random.uniform(2, 5)
            time.sleep(delay)
            
            # 尝试下载
            success = download_pdf(pdf_url)
            if success:
                return True
        except Exception as e:
            print(f"尝试 {attempt + 1} 失败: {e}")
        
        # 指数退避
        time.sleep(2 ** attempt)
    
    return False
```

## 方案 9：使用浏览器指纹管理

### 随机化指纹

```python
import random

# 随机 User-Agent
user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36...',
    # ... 更多 User-Agent
]

user_agent = random.choice(user_agents)

# 随机视口大小
viewport = {
    'width': random.randint(1280, 1920),
    'height': random.randint(720, 1080)
}

context = browser.new_context(
    user_agent=user_agent,
    viewport=viewport
)
```

## 方案 10：组合使用

### 最佳实践

结合多个方案：

```python
# 1. 使用 undetected-playwright
import undetected_playwright as up

# 2. 使用代理
proxy = get_random_proxy()

# 3. 使用 Cookie
cookies = load_cookies()

# 4. 模拟用户行为
simulate_user_behavior(page)

# 5. 使用 CDP 隐藏特征
hide_automation_features(page)

# 6. 智能重试
download_with_retry(pdf_url)
```

## 推荐实施顺序

1. **首先尝试**：优化版服务器（`backend_static_server_optimized.py`）
2. **如果失败**：使用非无头模式调试，观察问题
3. **如果仍然失败**：尝试 `undetected-playwright`
4. **如果还是失败**：使用手动 Cookie + 代理 IP
5. **最后手段**：使用专业反爬虫服务

## 注意事项

- 不要过于频繁地请求，避免 IP 被封
- 定期更新反检测脚本
- 监控成功率，及时调整策略
- 遵守网站的 robots.txt 和使用条款

