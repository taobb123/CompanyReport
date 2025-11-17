# AKShare集成说明

## ✅ 已完成的集成

系统已成功集成AKShare API，可以合法合规地获取证券研究报告。

## 📦 安装步骤

```bash
# 1. 安装AKShare
pip install akshare pandas

# 2. 更新requirements.txt已包含akshare
pip install -r requirements.txt
```

## 🔧 使用方法

### 方式1：使用AKShare（推荐，合法合规）

在 `main.py` 中设置：

```python
use_akshare = True  # 使用AKShare API
```

### 方式2：使用Playwright爬取（原方式）

在 `main.py` 中设置：

```python
use_akshare = False  # 使用Playwright爬取
```

## 🏗️ 架构设计

### 保持接口一致性

- `AkshareReportHandler` 实现了 `IReportTypeHandler` 接口
- 与原有的 `BaseReportHandler` 接口兼容
- 系统可以无缝切换数据源

### 组件说明

1. **AkshareDataClient** (`infrastructure/akshare_client.py`)
   - 封装AKShare API调用
   - 自动解析DataFrame数据
   - 转换为系统内部的ReportInfo格式

2. **AkshareReportHandler** (`strategies/akshare_handler.py`)
   - 实现IReportTypeHandler接口
   - 适配不同报告类型
   - 不需要HTML解析器

## 📊 AKShare接口说明

### 当前使用的接口

系统会自动尝试以下接口（按优先级）：

1. `stock_research_report_em()` - 东方财富研究报告
2. `report_rc()` - 研究报告
3. 自动查找包含'report'的函数

### 如何查看可用接口

```python
import akshare as ak

# 查看所有报告相关接口
report_functions = [x for x in dir(ak) if 'report' in x.lower()]
print(report_functions)
```

### 接口可能的变化

AKShare接口可能会更新，如果遇到问题：

1. 查看AKShare最新文档：https://www.akshare.xyz/
2. 运行上述代码查看可用接口
3. 更新 `infrastructure/akshare_client.py` 中的接口名称

## 🔍 数据字段映射

系统会自动识别以下字段：

- **标题**：包含'title'、'名称'、'报告'、'标题'的列
- **日期**：包含'date'、'日期'、'时间'的列
- **URL**：包含'url'、'链接'、'href'、'pdf'的列

如果自动识别失败，会使用前3列作为默认映射。

## ⚙️ 配置

在 `main.py` 中：

```python
use_akshare = True  # 切换数据源
```

## 🎯 优势

1. **合法合规**：使用官方API，无法律风险
2. **稳定可靠**：不依赖网页结构变化
3. **易于维护**：接口清晰，易于更新
4. **性能更好**：直接获取数据，无需渲染JavaScript

## 📝 注意事项

1. **PDF下载**：AKShare可能不直接提供PDF链接，需要：
   - 从返回的数据中提取PDF URL
   - 或使用详情页URL获取PDF链接

2. **数据格式**：AKShare返回的DataFrame格式可能变化，需要：
   - 查看返回的列名
   - 调整字段映射逻辑

3. **接口更新**：AKShare接口可能更新，需要：
   - 定期查看AKShare文档
   - 更新接口调用代码

## 🐛 故障排查

如果AKShare无法获取数据：

1. **检查安装**：
   ```python
   import akshare as ak
   print(ak.__version__)
   ```

2. **查看可用接口**：
   ```python
   import akshare as ak
   print([x for x in dir(ak) if 'report' in x.lower()])
   ```

3. **测试接口**：
   ```python
   import akshare as ak
   df = ak.stock_research_report_em()  # 或其他接口
   print(df.head())
   ```

4. **查看错误日志**：系统会输出详细的调试信息

## 📚 相关资源

- AKShare文档：https://www.akshare.xyz/
- AKShare GitHub：https://github.com/akfamily/akshare
- 问题反馈：查看AKShare GitHub Issues

