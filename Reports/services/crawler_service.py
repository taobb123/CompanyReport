"""
爬虫服务实现
使用组合模式，组合解析器、下载器、存储等组件
支持并发下载
"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional, Dict
from interfaces import (
    IReportCrawler, IHttpClient, IReportParser, 
    IPdfDownloader, IStorage, IReportTypeHandler,
    ReportInfo, PdfInfo
)


class ReportCrawlerService(IReportCrawler):
    """
    报告爬虫服务
    使用组合模式，组合各个组件完成爬取任务
    """
    
    def __init__(
        self,
        http_client: IHttpClient,
        parser: IReportParser,
        downloader: IPdfDownloader,
        storage: IStorage,
        handlers: Dict[str, IReportTypeHandler],
        max_workers: int = 6
    ):
        """
        初始化爬虫服务
        
        Args:
            http_client: HTTP客户端
            parser: 解析器
            downloader: 下载器
            storage: 存储
            handlers: 报告类型处理器字典
            max_workers: 最大并发下载数
        """
        self.http_client = http_client
        self.parser = parser
        self.downloader = downloader
        self.storage = storage
        self.handlers = handlers
        self.max_workers = max_workers
    
    def crawl_reports(self, report_type: str, limit: int = 6) -> List[PdfInfo]:
        """
        爬取指定类型的报告
        
        Args:
            report_type: 报告类型
            limit: 爬取数量限制
            
        Returns:
            PDF信息列表
        """
        # 获取对应的处理器
        handler = self.handlers.get(report_type)
        if not handler:
            print(f"不支持的报告类型: {report_type}")
            return []
        
        print(f"开始爬取 {handler.get_report_type_name()} 报告...")
        
        # 检查是否是API处理器（直接使用API，不需要HTTP请求）
        handler_class_name = type(handler).__name__
        is_tushare = 'Tushare' in handler_class_name
        is_akshare = 'Akshare' in handler_class_name
        is_api_handler = is_tushare or is_akshare
        
        if is_api_handler:
            # 使用API直接获取报告列表（Tushare或AKShare）
            api_name = "Tushare" if is_tushare else "AKShare"
            print(f"[方法] 使用{api_name} API获取报告列表")
            reports = handler.parse_list_page("", limit)  # API不需要HTML内容
        else:
            # 使用网页爬取方式
            # 1. 获取列表页（使用Playwright处理JavaScript动态内容）
            list_url = handler.get_list_url()
            
            # 检查是否是Playwright或Selenium客户端
            if self.http_client:
                client_type = type(self.http_client).__name__
                is_playwright = client_type == 'PlaywrightHttpClient'
                is_selenium = client_type == 'SeleniumHttpClient'
                
                if is_playwright or is_selenium:
                    # 如果已经是浏览器自动化客户端，直接使用
                    html_content = self.http_client.get(list_url, wait_time=5)
                    if not html_content:
                        print(f"获取列表页失败: {list_url}")
                        return []
                else:
                    # 如果不是浏览器客户端，尝试使用Playwright
                    print(f"[提示] 使用Playwright获取JavaScript动态加载的内容...")
                    try:
                        from infrastructure.playwright_client import PlaywrightHttpClient
                        playwright_client = PlaywrightHttpClient(timeout=30, headless=True)
                        html_content = playwright_client.get(list_url, wait_time=5)
                        playwright_client.close()
                        
                        if not html_content:
                            print(f"[错误] Playwright获取页面失败: {list_url}")
                            return []
                    except Exception as e:
                        print(f"[错误] Playwright初始化失败: {str(e)}")
                        print(f"[提示] 请安装依赖: pip install playwright")
                        print(f"[提示] 然后运行: playwright install chromium")
                        return []
            else:
                print(f"[错误] HTTP客户端未初始化")
                return []
            
            # 调试：保存HTML以便检查（开发时使用）
            try:
                from utils.debug import save_html_for_debug
                save_html_for_debug(html_content, f"{report_type}_list.html")
            except:
                pass  # 如果调试模块不可用，继续执行
            
            # 2. 解析报告列表
            reports = handler.parse_list_page(html_content, limit)
        
        if not reports:
            print(f"未找到报告（可能页面结构已变化，请检查HTML结构）")
            print(f"提示：可以查看debug目录下的HTML文件")
            return []
        
        print(f"找到 {len(reports)} 篇报告")
        
        # 3. 获取每篇报告的PDF链接
        pdf_infos = []
        for idx, report in enumerate(reports, 1):
            print(f"\n[处理] 报告 {idx}/{len(reports)}: {report.title[:50]}...")
            print(f"[URL] 详情页: {report.detail_url}")
            
            # 如果使用API且已有PDF链接
            detail_html = None
            if is_api_handler and report.detail_url:
                # 验证URL是否有效
                if not report.detail_url.startswith(('http://', 'https://')):
                    # 无效的URL，跳过
                    api_name = "Tushare" if is_tushare else "AKShare"
                    print(f"[警告] {api_name}返回的URL无效: {report.detail_url[:50]}，跳过此报告")
                    continue
                
                if 'pdf' in report.detail_url.lower() and 'pdf.dfcfw.com' in report.detail_url:
                    # 直接是PDF链接，尝试从详情页获取HTML（如果有详情页URL）
                    pdf_url = report.detail_url
                    api_name = "Tushare" if is_tushare else "AKShare"
                    print(f"[成功] PDF链接（来自{api_name}）: {pdf_url[:100]}")
                    # 注意：API返回的直接PDF链接，没有详情页，所以detail_html为None
                else:
                    # 是详情页URL，需要访问获取PDF链接和HTML
                    api_name = "Tushare" if is_tushare else "AKShare"
                    print(f"[提示] {api_name}返回的是详情页URL，需要获取PDF链接")
                    pdf_url, detail_html = self._get_pdf_url_and_html(report.detail_url) if report.detail_url else (None, None)
            else:
                # 需要访问详情页获取PDF链接
                # 先验证URL是否有效
                if report.detail_url and not report.detail_url.startswith(('http://', 'https://')):
                    print(f"[警告] 详情页URL无效: {report.detail_url[:50]}，跳过此报告")
                    continue
                # 获取PDF链接和详情页HTML（复用HTML内容）
                pdf_url, detail_html = self._get_pdf_url_and_html(report.detail_url) if report.detail_url else (None, None)
            
            if pdf_url:
                if not is_api_handler:
                    print(f"[成功] PDF链接: {pdf_url[:100]}")
                filename = self.storage.generate_filename(report)
                
                pdf_infos.append(PdfInfo(
                    url=pdf_url,
                    filename=filename,
                    report_info=report,
                    detail_html=detail_html  # 添加详情页HTML
                ))
            else:
                print(f"[跳过] 未找到PDF链接: {report.title}")
        
        # 4. 并发下载PDF（如果有下载器）
        if self.downloader and pdf_infos:
            self._download_pdfs(pdf_infos, report_type)
        elif pdf_infos:
            print(f"[成功] 找到 {len(pdf_infos)} 篇报告的PDF链接（已跳过下载步骤）")
            for info in pdf_infos:
                print(f"  - {info.report_info.title[:50]}: {info.url[:80]}")
        
        return pdf_infos
    
    def _get_pdf_url(self, detail_url: str) -> Optional[str]:
        """
        获取报告详情页的PDF链接（保留向后兼容）
        
        Args:
            detail_url: 详情页URL
            
        Returns:
            PDF链接，失败返回None
        """
        pdf_url, _ = self._get_pdf_url_and_html(detail_url)
        return pdf_url
    
    def _get_pdf_url_and_html(self, detail_url: str) -> tuple[Optional[str], Optional[str]]:
        """
        获取报告详情页的PDF链接和HTML内容（一次性获取，避免重复请求）
        
        Args:
            detail_url: 详情页URL
            
        Returns:
            (PDF链接, HTML内容) 元组，失败返回 (None, None)
        """
        # 使用Playwright或Selenium获取详情页（确保JavaScript渲染完成）
        client_type = type(self.http_client).__name__
        is_playwright = client_type == 'PlaywrightHttpClient'
        is_selenium = client_type == 'SeleniumHttpClient'
        
        if is_playwright or is_selenium:
            html_content = self.http_client.get(detail_url, wait_time=3)
        else:
            # 如果不是浏览器客户端，尝试使用Playwright
            try:
                from infrastructure.playwright_client import PlaywrightHttpClient
                playwright_client = PlaywrightHttpClient(timeout=30, headless=True)
                html_content = playwright_client.get(detail_url, wait_time=3)
                playwright_client.close()
            except:
                html_content = self.http_client.get(detail_url)
        
        if not html_content:
            print(f"[错误] 无法获取详情页内容: {detail_url}")
            return None, None
        
        pdf_url = self.parser.parse_pdf_link(html_content)
        return pdf_url, html_content
    
    def _download_pdfs(self, pdf_infos: List[PdfInfo], report_type: str):
        """
        并发下载PDF文件
        
        Args:
            pdf_infos: PDF信息列表
            report_type: 报告类型
        """
        if not pdf_infos:
            return
        
        # 确保存储目录存在
        save_dir = self.storage.ensure_directory(report_type)
        
        # 关键：在主线程中获取Cookie（避免greenlet错误）
        # 使用统一的会话（访问报告列表页建立会话）
        cookies_map = {}  # {pdf_url: cookies}
        
        if self.downloader and self.downloader.playwright_downloader:
            # 为所有PDF建立统一会话（使用报告列表页）
            print(f"[提示] 在主线程中建立统一会话（使用报告列表页）...")
            try:
                # 访问报告列表页建立会话
                common_cookies = self.downloader.playwright_downloader.get_cookies(referer_url=None)
                if common_cookies:
                    print(f"[成功] 建立会话，获取到 {len(common_cookies)} 个Cookie")
                    # 所有PDF使用相同的Cookie
                    for pdf_info in pdf_infos:
                        cookies_map[pdf_info.url] = common_cookies
                else:
                    print(f"[警告] 未能获取Cookie")
            except Exception as e:
                print(f"[警告] 建立会话失败: {str(e)}")
                import traceback
                print(f"[错误详情] {traceback.format_exc()[:300]}")
        
        # 使用线程池并发下载
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            for pdf_info in pdf_infos:
                save_path = f"{save_dir}/{pdf_info.filename}"
                # 传递对应的Cookie给下载方法（避免在并发线程中调用Playwright）
                pdf_cookies = cookies_map.get(pdf_info.url)
                future = executor.submit(
                    self._download_single_pdf,
                    pdf_info,
                    save_path,
                    pdf_cookies  # 传递对应的Cookie
                )
                futures.append((future, pdf_info))
            
            # 等待所有任务完成
            completed = 0
            for future, pdf_info in futures:
                try:
                    success = future.result()
                    if success:
                        completed += 1
                        print(f"✓ 下载成功: {pdf_info.filename}")
                    else:
                        print(f"✗ 下载失败: {pdf_info.filename}")
                except Exception as e:
                    print(f"✗ 下载异常 {pdf_info.filename}: {str(e)}")
        
        print(f"下载完成: {completed}/{len(pdf_infos)}")
    
    def _download_single_pdf(self, pdf_info: PdfInfo, save_path: str, cookies: list = None) -> bool:
        """
        下载单个PDF文件
        
        Args:
            pdf_info: PDF信息
            save_path: 保存路径
            cookies: Cookie列表（在主线程中获取，避免greenlet错误）
            
        Returns:
            是否下载成功
        """
        # 使用详情页URL作为Referer（关键！）
        # 如果没有详情页URL，使用报告列表页作为Referer
        referer = pdf_info.report_info.detail_url
        if not referer or referer.startswith('akshare://') or referer.startswith('tushare://'):
            # 如果使用API且没有详情页，使用报告列表页作为Referer
            referer = 'https://data.eastmoney.com/report/'
        
        # 如果使用Playwright下载器，传递Cookie（避免在并发线程中调用Playwright API）
        if self.downloader and self.downloader.playwright_downloader:
            return self.downloader.playwright_downloader.download_pdf(
                pdf_info.url, save_path, referer=referer, cookies=cookies
            )
        else:
            return self.downloader.download(pdf_info.url, save_path, referer=referer)

