# Tushare数据源设置指南

## 📦 安装

```bash
pip install tushare pandas
# 或
pip install -r requirements.txt
```

## 🔑 获取Token

### 步骤1：注册账号
1. 访问：https://tushare.pro/
2. 注册账号（免费版即可）

### 步骤2：获取Token
1. 登录后，进入"接口TOKEN"页面
2. 复制你的Token

### 步骤3：设置Token

**方式1：在代码中设置（推荐用于测试）**
```python
# 在 main.py 中
tushare_token = "你的Token"
```

**方式2：使用环境变量（推荐用于生产）**
```bash
# Windows PowerShell
$env:TUSHARE_TOKEN="你的Token"

# Windows CMD
set TUSHARE_TOKEN=你的Token

# Linux/Mac
export TUSHARE_TOKEN="你的Token"
```

## 🚀 使用方法

### 在main.py中启用Tushare

```python
use_tushare = True   # 使用Tushare
use_akshare = False # 不使用AKShare
tushare_token = "你的Token"  # 或设置为None，从环境变量获取
```

## 📊 Tushare接口说明

### 当前使用的接口

系统会自动尝试以下接口：

1. `report_rc()` - 研究报告（如果存在）
2. `report()` - 研究报告（如果存在）

### 如何查看可用接口

```python
import tushare as ts
ts.set_token('你的Token')
pro = ts.pro_api()

# 查看所有报告相关接口
report_functions = [x for x in dir(pro) if 'report' in x.lower()]
print(report_functions)
```

### 接口可能的变化

Tushare接口可能会更新，如果遇到问题：

1. 查看Tushare最新文档：https://tushare.pro/document/2
2. 运行上述代码查看可用接口
3. 更新 `infrastructure/tushare_client.py` 中的接口名称

## 💡 优势

1. **合法合规**：官方API，完全合法
2. **数据质量高**：官方维护，数据准确
3. **稳定可靠**：不依赖网页结构变化
4. **易于维护**：接口清晰，易于更新

## ⚠️ 注意事项

1. **积分限制**：免费版有积分限制，但足够学习使用
2. **接口更新**：Tushare接口可能更新，需要查看最新文档
3. **PDF下载**：Tushare可能不直接提供PDF链接，需要：
   - 从返回的数据中提取PDF URL
   - 或使用详情页URL获取PDF链接

## 🔍 故障排查

如果Tushare无法获取数据：

1. **检查Token**：
   ```python
   import tushare as ts
   ts.set_token('你的Token')
   pro = ts.pro_api()
   print(pro)  # 应该显示pro_api对象
   ```

2. **查看可用接口**：
   ```python
   import tushare as ts
   ts.set_token('你的Token')
   pro = ts.pro_api()
   print([x for x in dir(pro) if 'report' in x.lower()])
   ```

3. **测试接口**：
   ```python
   import tushare as ts
   ts.set_token('你的Token')
   pro = ts.pro_api()
   # 尝试调用接口
   df = pro.report_rc()  # 或其他接口
   print(df.head())
   ```

4. **查看错误日志**：系统会输出详细的调试信息

## 📚 相关资源

- Tushare官网：https://tushare.pro/
- Tushare文档：https://tushare.pro/document/2
- Tushare GitHub：https://github.com/waditu/tushare

---

**提示**：Tushare是官方API，完全合法合规，推荐使用！

