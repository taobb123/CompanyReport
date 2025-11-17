# 优化指南 - 彻底解决反爬虫问题

## 已实施的优化

### 1. 解决线程问题 ✅

**问题**：`Cannot switch to a different thread`

**解决方案**：
- 在主线程中初始化 Playwright（避免线程切换问题）
- 使用 Flask 单线程模式（`threaded=False`）
- 确保所有 Playwright 操作在同一线程中执行

### 2. 增强反检测能力 ✅

**优化措施**：

#### a) 浏览器参数优化
```python
browser_args = [
    '--disable-automation',  # 隐藏自动化特征
    '--disable-infobars',    # 隐藏"Chrome正在被自动化控制"提示
    '--disable-blink-features=AutomationControlled',
]
```

#### b) JavaScript 反检测脚本
```javascript
// 隐藏 webdriver 特征
Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined
});

// 覆盖 plugins、languages、permissions
```

#### c) 模拟真实用户行为
- 访问详情页前先访问列表页
- 增加等待时间（3-5秒）
- 模拟滚动操作
- 等待网络空闲状态

#### d) 完整的请求头
- 正确的 Referer
- 完整的 Accept 头
- 浏览器特征头（Accept-Language 等）

### 3. 改进下载策略 ✅

**新策略**：
1. **步骤1**：访问报告列表页建立基础会话
2. **步骤2**：访问详情页建立完整会话（如果提供）
3. **步骤3**：使用网络拦截获取 PDF 响应
4. **步骤4**：验证 PDF 内容并保存

**关键点**：
- 使用 `page.on('response')` 监听网络响应
- 从当前页面跳转到 PDF URL（保持会话连续性）
- 等待足够长时间让会话建立

## 使用方法

### 启动优化版服务器

```bash
python backend_static_server_optimized.py
```

### 对比原版

| 特性 | 原版 | 优化版 |
|------|------|--------|
| 线程安全 | ❌ 有线程问题 | ✅ 主线程运行 |
| 反检测 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 用户行为模拟 | ❌ | ✅ |
| 会话管理 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

## 如果仍然失败

### 方案 A：使用非无头模式调试

修改 `backend_static_server_optimized.py`：

```python
browser = playwright.chromium.launch(
    headless=False,  # 改为 False，观察浏览器行为
    args=browser_args
)
```

这样可以：
- 观察浏览器实际行为
- 查看是否被重定向到验证页面
- 检查 Cookie 是否正确设置

### 方案 B：增加更多等待时间

如果反爬虫检测更严格，可以增加等待时间：

```python
time.sleep(10)  # 增加到 10 秒
```

### 方案 C：使用 undetected-playwright

安装：
```bash
pip install undetected-playwright
```

使用：
```python
import undetected_playwright as up
browser = up.chromium.launch(headless=True)
```

### 方案 D：手动获取 Cookie

1. 在浏览器中手动访问报告页面
2. 使用浏览器开发者工具导出 Cookie
3. 在代码中使用这些 Cookie

### 方案 E：使用代理 IP

如果 IP 被限制，可以使用代理：

```python
browser = playwright.chromium.launch(
    headless=True,
    proxy={
        "server": "http://proxy.example.com:8080",
        "username": "user",
        "password": "pass"
    }
)
```

## 调试技巧

### 1. 查看详细日志

优化版已添加详细日志，包括：
- 每个步骤的执行状态
- 网络拦截的响应信息
- 错误详情

### 2. 检查下载的内容

如果下载失败，查看日志中的：
```
[调试] 内容开头: ...
```

### 3. 验证会话

检查是否成功建立会话：
```
[成功] 基础会话已建立
[成功] 详情页会话已建立
```

## 性能优化

### 1. 缓存机制

相同 URL 的 PDF 只下载一次，后续直接使用缓存。

### 2. 并发控制

如果需要并发下载多个 PDF，建议：
- 使用队列控制并发数
- 避免同时创建多个 Playwright 实例

## 长期方案

如果反爬虫持续升级，考虑：

1. **定期更新反检测脚本**：根据最新的检测技术更新
2. **使用专业反爬虫服务**：如 ScraperAPI、Bright Data 等
3. **建立 Cookie 池**：定期更新和维护 Cookie
4. **使用机器学习**：训练模型识别验证页面

## 总结

优化版服务器已解决：
- ✅ 线程问题
- ✅ 基础反检测
- ✅ 用户行为模拟
- ✅ 会话管理

如果仍然失败，可能需要：
- 使用非无头模式调试
- 增加更多等待时间
- 使用更高级的反检测工具
- 考虑使用专业服务



