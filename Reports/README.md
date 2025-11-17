# 证券报告爬虫系统

## 项目简介

这是一个用于爬取东方财富网证券报告的系统，支持爬取策略报告、行业研报、宏观研报和盈利预测四种类型的报告。

## 功能特点

- ✅ 支持多种报告类型（策略、行业、宏观、盈利预测）
- ✅ 每个类型爬取前6篇报告
- ✅ 自动下载PDF原文
- ✅ 支持并发下载（最多6个并发）
- ✅ 按类型分类存储
- ✅ 错误处理：跳过失败项继续执行
- ✅ 遵循良好的设计模式（接口编程、组合优于继承、策略模式、代理模式等）

## 系统架构

### 分层设计

```
┌─────────────────────────────────┐
│   Application Layer (main.py)   │  应用层
├─────────────────────────────────┤
│   Service Layer                 │  服务层（爬虫服务编排）
├─────────────────────────────────┤
│   Strategy Layer                │  策略层（不同报告类型处理）
├─────────────────────────────────┤
│   Core Layer                    │  核心层（解析、下载）
├─────────────────────────────────┤
│   Infrastructure Layer          │  基础设施层（HTTP、存储）
└─────────────────────────────────┘
```

### 设计模式应用

1. **接口编程**：所有核心功能都通过接口定义，实现与接口解耦
2. **组合优于继承**：通过依赖注入组合各个组件
3. **策略模式**：不同报告类型使用不同的处理器
4. **代理模式**：HTTP请求和下载功能使用代理封装
5. **模板方法模式**：基础处理器定义通用流程
6. **委托模式**：功能委托给专门的组件处理

## 安装依赖

```bash
pip install -r requirements.txt
playwright install chromium
```

**注意**：
- 安装完Playwright后，需要运行 `playwright install chromium` 来安装Chromium浏览器
- 如果使用Tushare，需要注册账号获取Token（免费版即可）
- 如果使用AKShare，无需额外配置

## 使用方法

直接运行主程序：

```bash
python main.py
```

程序会自动爬取以下类型的报告：
- 策略报告
- 行业研报
- 宏观研报
- 盈利预测

每种类型爬取前6篇，PDF文件会保存到 `D:\Books\证券` 目录下，按类型分文件夹存储。

## 存储结构

```
D:\Books\证券\
├── 策略\
│   ├── 报告标题1_20241107.pdf
│   └── 报告标题2_20241107.pdf
├── 行业\
│   └── ...
├── 宏观\
│   └── ...
└── 盈利预测\
    └── ...
```

## 项目结构

```
Reports/
├── interfaces/          # 接口定义
│   └── __init__.py
├── infrastructure/      # 基础设施层
│   ├── __init__.py
│   ├── http_client.py   # HTTP客户端（代理模式）
│   └── storage.py       # 文件存储
├── core/                # 核心层
│   ├── __init__.py
│   ├── parser.py        # HTML解析器
│   └── downloader.py    # PDF下载器
├── strategies/          # 策略层
│   ├── __init__.py
│   └── report_handler.py # 报告类型处理器
├── services/            # 服务层
│   ├── __init__.py
│   └── crawler_service.py # 爬虫服务
├── main.py              # 主程序入口
├── requirements.txt     # 依赖列表
└── README.md           # 说明文档
```

## 配置说明

可以在 `config.py` 中修改以下配置：

- `STORAGE_BASE_PATH`: 存储路径（默认：`D:\Books\证券`）
- `MAX_CONCURRENT_DOWNLOADS`: 并发下载数量（默认：6）
- `CRAWL_LIMIT`: 每种类型爬取数量（默认：6）
- `HTTP_TIMEOUT`: HTTP请求超时时间（默认：30秒）
- `REPORT_TYPES`: 报告类型配置（可扩展）

## 注意事项

1. 确保网络连接正常
2. 确保存储路径有写入权限
3. 如果某个报告没有PDF链接或下载失败，程序会跳过并继续
4. 文件名中的非法字符会被自动替换为下划线

## ⚠️ 法律声明

**重要提示：**
- 本工具仅供学习研究使用
- 请遵守目标网站的服务条款和robots.txt协议
- 建议优先使用合法的API数据源（如Tushare、AKShare）
- 商业使用需要获得数据提供方的授权
- 详细法律说明请查看 `LEGAL_NOTICE.md`
- 替代数据源推荐请查看 `ALTERNATIVE_DATA_SOURCES.md`

**推荐使用合法的数据源：**
- Tushare（官方API）：https://tushare.pro/
- AKShare（开源免费）：https://www.akshare.xyz/
- 巨潮资讯网（官方指定）：http://www.cninfo.com.cn/

## 扩展性

系统设计具有良好的扩展性：

- **添加新的报告类型**：只需创建新的Handler类并注册到handlers字典
- **更换解析器**：实现`IReportParser`接口即可
- **更换存储方式**：实现`IStorage`接口即可
- **更换HTTP客户端**：实现`IHttpClient`接口即可

