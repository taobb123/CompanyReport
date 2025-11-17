# 故障排查指南

## 问题：下载返回JavaScript验证页面而非PDF

### 症状
- Content-Type显示`application/pdf`，但实际内容是JavaScript
- 文件大小只有987-988字节（太小，不是真正的PDF）
- 内容以`<script>`开头

### 可能的原因
1. **服务器检测到自动化访问**：即使使用Playwright，服务器仍能识别
2. **Cookie不完整**：需要更完整的会话信息
3. **需要先访问详情页**：某些PDF需要从详情页跳转才能下载

### 解决方案

#### 方案1：使用非无头模式调试（推荐）

在 `main.py` 中修改：

```python
# 将 headless=True 改为 headless=False
http_client = PlaywrightHttpClient(timeout=config.HTTP_TIMEOUT, headless=False)
```

这样可以：
- 观察浏览器实际行为
- 查看是否被重定向到验证页面
- 检查Cookie是否正确设置

#### 方案2：增加延迟和等待时间

在 `infrastructure/playwright_client.py` 中增加等待时间：

```python
time.sleep(5)  # 增加到5秒，让会话充分建立
```

#### 方案3：先访问详情页建立会话

如果AKShare提供了详情页URL，确保先访问详情页：

```python
# 在下载PDF前，先访问详情页
if detail_url:
    page.goto(detail_url)
    time.sleep(3)
    # 然后再下载PDF
```

#### 方案4：检查是否需要登录

某些PDF可能需要登录才能访问。检查：
- 是否需要登录账号
- 是否需要特定的权限

#### 方案5：手动测试PDF链接

1. 在浏览器中打开PDF链接
2. 检查是否需要登录
3. 检查是否需要从特定页面跳转
4. 使用浏览器开发者工具查看网络请求，检查：
   - Cookie
   - Referer
   - 其他请求头

### 调试步骤

1. **启用非无头模式**：
   ```python
   http_client = PlaywrightHttpClient(timeout=config.HTTP_TIMEOUT, headless=False)
   ```

2. **运行程序并观察浏览器**：
   - 查看是否被重定向
   - 查看Cookie是否正确
   - 查看网络请求

3. **检查调试输出**：
   - Cookie数量
   - Referer设置
   - 响应状态码
   - 响应内容预览

4. **对比浏览器行为**：
   - 在真实浏览器中打开PDF链接
   - 使用开发者工具查看请求头
   - 对比程序发送的请求头

### 如果所有方法都失败

如果所有方法都无法下载PDF，可能的原因：

1. **服务器有强反爬虫机制**：需要更复杂的绕过方法
2. **PDF链接已过期**：需要重新获取链接
3. **需要登录或权限**：需要先登录账号
4. **需要使用其他数据源**：考虑使用Tushare等合法API

### 建议

1. **优先使用合法的API数据源**（如Tushare、AKShare）
2. **如果必须爬取，遵守robots.txt和服务条款**
3. **仅用于个人学习研究，不要商业使用**

