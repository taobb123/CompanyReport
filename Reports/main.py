"""
主程序入口
使用工厂模式创建组件并组合成爬虫服务
"""

import config
from infrastructure.http_client import HttpProxy
from infrastructure.playwright_client import PlaywrightHttpClient
from infrastructure.storage import FileStorage
from core.parser import HtmlReportParser
from core.downloader import PdfDownloader
from strategies.report_handler import (
    StrategyReportHandler,
    IndustryReportHandler,
    MacroReportHandler,
    StockReportHandler
)
from strategies.akshare_handler import AkshareReportHandler
from strategies.tushare_handler import TushareReportHandler
from services.crawler_service import ReportCrawlerService
from core.html_generator import HtmlReportGenerator


def create_crawler_service(use_akshare: bool = False, use_tushare: bool = True, headless: bool = True, tushare_token: str = "e433bebb1abbbdb014cbdfd619dfce5f399eeb79442aba1184df6882") -> ReportCrawlerService:
    """
    创建爬虫服务（工厂方法）
    使用组合模式组装各个组件
    
    Args:
        use_akshare: 是否使用AKShare API
        use_tushare: 是否使用Tushare API（推荐，合法合规）
        headless: 是否使用无头模式
        tushare_token: Tushare API Token（可选，也可以从环境变量获取）
    """
    storage = FileStorage(base_path=config.STORAGE_BASE_PATH)
    
    if use_tushare:
        # 使用Tushare API（最推荐，合法合规）
        print("[提示] 使用Tushare API获取研究报告（最推荐，合法合规）")
        # Tushare获取报告列表，但仍需要HTTP客户端下载PDF
        http_client = PlaywrightHttpClient(timeout=config.HTTP_TIMEOUT, headless=headless)
        parser = None  # Tushare不需要HTML解析器
        downloader = PdfDownloader(http_client=http_client)  # 需要下载器来下载PDF
        
        # 创建Tushare处理器
        handlers = {
            'strategy': TushareReportHandler('strategy', '策略', token=tushare_token),
            'industry': TushareReportHandler('industry', '行业', token=tushare_token),
            'macro': TushareReportHandler('macro', '宏观', token=tushare_token),
        }
    elif use_akshare:
        # 使用AKShare API（合法合规，推荐）
        print("[提示] 使用AKShare API获取研究报告（合法合规）")
        # AKShare获取报告列表，但仍需要HTTP客户端下载PDF
        http_client = PlaywrightHttpClient(timeout=config.HTTP_TIMEOUT, headless=headless)
        parser = None  # AKShare不需要HTML解析器
        downloader = PdfDownloader(http_client=http_client)  # 需要下载器来下载PDF
        
        # 创建AKShare处理器
        handlers = {
            'strategy': AkshareReportHandler('strategy', '策略'),
            'industry': AkshareReportHandler('industry', '行业'),
            'macro': AkshareReportHandler('macro', '宏观'),
        }
    else:
        # 使用Playwright爬取（原方式）
        print("[提示] 使用Playwright处理JavaScript动态内容")
        http_client = PlaywrightHttpClient(timeout=config.HTTP_TIMEOUT, headless=headless)
        
        # 2. 创建核心组件（通过组合注入依赖）
        parser = HtmlReportParser()
        downloader = PdfDownloader(http_client=http_client)
        
        # 3. 创建策略处理器（通过组合注入解析器）
        handlers = {
            'strategy': StrategyReportHandler(parser=parser),
            'industry': IndustryReportHandler(parser=parser),
            'macro': MacroReportHandler(parser=parser),
            'stock': StockReportHandler(parser=parser),
        }
    
    # 4. 创建爬虫服务（组合所有组件）
    # 如果使用AKShare，某些组件可能为None，服务层会处理
    # 注意：只收集链接，不下载，所以downloader可以为None
    crawler = ReportCrawlerService(
        http_client=http_client,
        parser=parser,
        downloader=None,  # 不下载，只收集链接
        storage=storage,
        handlers=handlers,
        max_workers=config.MAX_CONCURRENT_DOWNLOADS
    )
    
    return crawler


def main():
    """主函数"""
    print("=" * 60)
    print("证券报告爬虫系统")
    print("=" * 60)
    print(f"存储路径: {config.STORAGE_BASE_PATH}")
    print(f"每种类型爬取数量: {config.CRAWL_LIMIT}")
    print(f"并发下载数: {config.MAX_CONCURRENT_DOWNLOADS}")
    print("=" * 60)
    
    # 创建爬虫服务
    # 数据源选择（按优先级）：
    # 1. Tushare（最推荐，合法合规，需要Token）
    # 2. AKShare（推荐，合法合规，免费）
    # 3. Playwright爬取（仅供学习，可能违反服务条款）
    
    use_tushare = False  # 不使用Tushare
    use_akshare = True   # 使用AKShare（推荐，合法合规，免费）
    use_headless = True  # 调试选项：设置为False可以看到浏览器窗口
    
    # Tushare Token（可以从环境变量获取，或在这里设置）
    tushare_token = None  # 设置为你的Token，或设置环境变量 TUSHARE_TOKEN
    
    if use_tushare:
        print("[提示] 使用Tushare API数据源（最推荐，合法合规）")
        if not tushare_token:
            import os
            tushare_token = os.getenv('TUSHARE_TOKEN')
        if not tushare_token:
            print("[警告] 未提供Tushare Token")
            print("[提示] 获取Token: https://tushare.pro/")
            print("[提示] 免费版有积分限制，但足够学习使用")
    elif use_akshare:
        print("[提示] 使用AKShare API数据源（合法合规）")
    else:
        print("[提示] 使用Playwright爬取方式（仅供学习）")
    
    if not use_headless:
        print("[提示] 使用非无头模式（可以看到浏览器窗口，便于调试）")
    
    crawler = create_crawler_service(
        use_akshare=use_akshare, 
        use_tushare=use_tushare,
        headless=use_headless,
        tushare_token=tushare_token
    )
    
    # 定义要爬取的报告类型
    report_types = list(config.REPORT_TYPES.keys())
    
    # 收集所有PDF链接（按类型分组）
    pdf_links_by_type = {}
    
    # 爬取每种类型的报告（只收集链接，不下载）
    import time
    for idx, report_type in enumerate(report_types):
        try:
            type_name = config.REPORT_TYPES[report_type]['name']
            print(f"\n{'=' * 60}")
            print(f"开始收集 {type_name} 报告PDF链接... ({idx + 1}/{len(report_types)})")
            print(f"{'=' * 60}")
            
            # 收集PDF链接（不下载）
            pdf_infos = crawler.crawl_reports(report_type, limit=config.CRAWL_LIMIT)
            pdf_links_by_type[report_type] = pdf_infos
            
            print(f"[成功] {type_name}: 收集到 {len(pdf_infos)} 个PDF链接")
            print(f"{'=' * 60}\n")
        except Exception as e:
            print(f"收集 {report_type} 报告时发生错误: {str(e)}")
            pdf_links_by_type[report_type] = []
            continue
    
    # 关闭HTTP客户端（如果存在）
    if crawler.http_client:
        crawler.http_client.close()
    
    # 生成HTML报告
    print("\n" + "=" * 60)
    print("正在生成HTML报告...")
    print("=" * 60)
    
    html_generator = HtmlReportGenerator()
    html_generator.generate(pdf_links_by_type)
    
    print("=" * 60)
    print("所有任务完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()

