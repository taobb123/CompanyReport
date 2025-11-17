"""
配置文件
集中管理系统配置参数
"""

# 存储配置
STORAGE_BASE_PATH = r"C:\Users\111\Desktop\Reports\frontend\public"

# 爬取配置
CRAWL_LIMIT = 6  # 每种类型爬取的数量
MAX_CONCURRENT_DOWNLOADS = 6  # 最大并发下载数

# HTTP配置
HTTP_TIMEOUT = 60  # HTTP请求超时时间（秒，Playwright需要更长时间）

# 报告类型配置
REPORT_TYPES = {
    'strategy': {
        'name': '策略报告',
        'url': 'https://data.eastmoney.com/report/strategyreport.jshtml'
    },
    'industry': {
        'name': '行业研报',
        'url': 'https://data.eastmoney.com/report/industry.jshtml'
    },
    'macro': {
        'name': '宏观研究',
        'url': 'https://data.eastmoney.com/report/macresearch.jshtml'
    },
    'stock': {
        'name': '个股研报',
        'url': 'https://data.eastmoney.com/report/stock.jshtml'
    }
}

