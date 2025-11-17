# 解决反爬虫问题指南

## 问题描述

PDF 服务器（如 `pdf.dfcfw.com`）检测到自动化请求，返回 JavaScript 反爬虫页面而不是真正的 PDF 文件。

**症状**：
- HTTP 状态码 200
- Content-Type: `application/pdf`
- 但实际内容开头是 `<script>fu`（JavaScript 代码）
- 文件大小只有 986 字节（太小，不是真正的 PDF）

## 解决方案

### 方案 1：使用 Playwright（推荐）✅

代理服务器已集成 Playwright 支持，可以模拟真实浏览器绕过反爬虫。

#### 安装 Playwright

```bash
pip install playwright
playwright install chromium
```

#### 启动代理服务器

```bash
python backend_proxy.py
```

代理服务器会自动：
1. 检测 Playwright 是否可用
2. 如果可用，使用 Playwright 获取 PDF
3. 如果不可用，回退到 requests（可能失败）

#### 工作原理

1. **建立会话**：先访问报告列表页和详情页建立浏览器会话
2. **网络拦截**：监听网络响应，捕获 PDF 内容
3. **绕过检测**：使用真实浏览器环境，避免被识别为自动化工具

### 方案 2：手动测试和调试

如果 Playwright 仍然失败，可以：

1. **使用非无头模式**（查看浏览器行为）：
   ```python
   # 在 backend_proxy.py 中修改
   _browser = _playwright.chromium.launch(headless=False)  # 改为 False
   ```

2. **检查是否需要登录**：
   - 在浏览器中手动访问 PDF URL
   - 检查是否需要登录或特殊权限

3. **查看网络请求**：
   - 使用浏览器开发者工具
   - 查看实际请求的 Cookie、Referer 等

## 使用步骤

### 1. 确保 Playwright 已安装

```bash
# 检查是否安装
python -c "from playwright.sync_api import sync_playwright; print('Playwright 已安装')"

# 如果未安装，执行：
pip install playwright
playwright install chromium
```

### 2. 重启代理服务器

```bash
python backend_proxy.py
```

应该看到：
```
[Playwright] 浏览器实例已创建
```

### 3. 测试

1. 刷新前端页面
2. 选择一个报告
3. 查看代理服务器终端输出：
   - 应该看到 `[方法] 使用 Playwright 获取 PDF（绕过反爬虫）`
   - 应该看到 `[成功] 使用 Playwright 成功获取 PDF`

## 故障排除

### 问题：Playwright 未安装

**症状**：终端显示 `[警告] Playwright 未安装`

**解决**：
```bash
pip install playwright
playwright install chromium
```

### 问题：Playwright 创建失败

**症状**：`[错误] 创建 Playwright 实例失败`

**可能原因**：
- Chromium 未正确安装
- 权限问题

**解决**：
```bash
# 重新安装 Chromium
playwright install chromium --force
```

### 问题：Playwright 获取失败

**症状**：`[警告] Playwright 未获取到有效 PDF`

**可能原因**：
- 反爬虫机制升级
- 需要更长的等待时间
- 需要特定的 Cookie 或 Session

**解决**：
1. 增加等待时间（在代码中修改 `time.sleep(3)` 为更长的时间）
2. 使用非无头模式查看浏览器行为
3. 检查是否需要登录

### 问题：仍然返回 JavaScript

**症状**：即使使用 Playwright，仍然返回 `<script>` 开头的内容

**解决**：
1. 检查是否需要先登录
2. 检查是否需要从特定页面跳转
3. 尝试手动在浏览器中访问 PDF URL，查看实际行为

## 性能优化

### 重用浏览器实例

代理服务器使用全局浏览器实例，避免每次请求都创建新浏览器，提高性能。

### 会话缓存

首次请求会建立会话，后续请求可以重用会话。

## 注意事项

1. **首次启动较慢**：Playwright 需要启动浏览器，首次请求可能较慢
2. **资源占用**：浏览器实例会占用一定内存
3. **并发限制**：建议不要同时处理太多请求

## 回退方案

如果 Playwright 不可用或失败，代理服务器会：
1. 尝试使用 requests（可能失败，因为会被反爬虫拦截）
2. 返回错误信息，提示使用 Playwright

## 测试命令

测试代理服务器是否正常工作：

```bash
# 测试健康检查
curl http://localhost:5000/health

# 测试代理（需要 URL 编码）
curl "http://localhost:5000/pdf-proxy?url=https%3A%2F%2Fpdf.dfcfw.com%2Fpdf%2FH3_AP202510281770514161_1.pdf"
```

## 下一步

如果问题仍然存在：
1. 查看代理服务器的详细日志
2. 使用非无头模式观察浏览器行为
3. 检查是否需要其他认证或 Cookie

