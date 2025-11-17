# PDF 代理服务器设置指南

## 概述

使用 Mozilla PDF.js 官方查看器 + 后端代理的方案，可以完美解决 CORS 跨域问题，在右侧直接显示 PDF，无需新窗口。

## 架构说明

```
前端 (Vue) 
  ↓
PDF.js 官方查看器 (iframe)
  ↓
后端代理服务器 (Flask)
  ↓
原始 PDF 服务器
```

## 快速开始

### 1. 安装后端依赖

```bash
pip install flask flask-cors requests
```

或使用 requirements.txt：

```bash
pip install -r requirements.txt
```

### 2. 启动代理服务器

```bash
python backend_proxy.py
```

服务器将在 `http://localhost:5000` 启动

### 3. 配置前端（可选）

如果需要修改代理地址，创建 `frontend/.env` 文件：

```env
VITE_PROXY_URL=http://localhost:5000
```

### 4. 启动前端

```bash
cd frontend
npm install
npm run dev
```

## 使用方式

1. 从左侧目录选择报告
2. PDF 会自动通过代理加载并在右侧显示
3. 使用 PDF.js 官方查看器的所有功能（缩放、搜索、打印等）

## 代理端点

### 健康检查

```
GET http://localhost:5000/health
```

响应：
```json
{
  "status": "ok",
  "service": "PDF Proxy"
}
```

### PDF 代理

```
GET http://localhost:5000/pdf-proxy?url=PDF_URL
```

参数：
- `url` (必需): PDF 文件的 URL（需要 URL 编码）
- `referer` (可选): Referer 头（用于防盗链）

示例：
```
http://localhost:5000/pdf-proxy?url=https%3A%2F%2Fpdf.dfcfw.com%2Fpdf%2FH3_AP202510281770514161_1.pdf
```

## 配置说明

在 `backend_proxy.py` 中可以修改：

```python
PROXY_PORT = 5000          # 代理服务器端口
MAX_FILE_SIZE = 100 * 1024 * 1024  # 最大文件大小（100MB）
TIMEOUT = 30              # 请求超时时间（秒）
```

## 优势

### ✅ 相比直接 iframe 的优势

1. **绕过 CORS 限制**：通过后端代理，完全绕过浏览器 CORS 限制
2. **绕过 X-Frame-Options**：PDF.js 查看器不受安全策略限制
3. **完整功能**：使用官方查看器，功能完整（搜索、打印、注释等）
4. **无需新窗口**：在右侧直接显示，用户体验好

### ✅ 相比 PDF.js 直接渲染的优势

1. **更简单**：不需要手动渲染，使用官方查看器
2. **功能完整**：官方查看器包含所有功能
3. **性能好**：官方查看器经过优化
4. **维护成本低**：不需要维护渲染逻辑

## 故障排除

### 问题：PDF 无法加载

**检查清单**：
1. ✅ 代理服务器是否运行？（访问 `http://localhost:5000/health`）
2. ✅ 前端 `.env` 文件中的代理地址是否正确？
3. ✅ 浏览器控制台是否有错误信息？
4. ✅ 网络连接是否正常？

### 问题：代理服务器启动失败

**可能原因**：
- 端口 5000 已被占用

**解决方案**：
```python
# 修改 backend_proxy.py 中的端口
PROXY_PORT = 5001  # 或其他可用端口
```

### 问题：PDF 加载很慢

**可能原因**：
- PDF 文件很大
- 网络速度慢

**解决方案**：
- 等待加载完成
- 检查网络连接
- 考虑增加超时时间

## 安全注意事项

⚠️ **生产环境建议**：

1. **限制访问**：只允许特定域名访问代理
2. **验证 URL**：严格验证 PDF URL，防止 SSRF 攻击
3. **文件大小限制**：设置合理的文件大小限制
4. **速率限制**：防止滥用
5. **HTTPS**：使用 HTTPS 保护数据传输

## 部署建议

### 开发环境

- 直接运行 `python backend_proxy.py`
- 前端使用 `npm run dev`

### 生产环境

1. **使用 Gunicorn 运行 Flask**：
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 backend_proxy:app
```

2. **使用 Nginx 反向代理**：
```nginx
location /pdf-proxy {
    proxy_pass http://localhost:5000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

3. **配置环境变量**：
```bash
export VITE_PROXY_URL=https://your-domain.com
```

## 更新日志

### v1.0.0
- ✅ 实现基础 PDF 代理功能
- ✅ 集成 PDF.js 官方查看器
- ✅ 支持 CORS 和跨域请求
- ✅ 流式传输大文件

