"""
PDF下载器实现
使用代理模式封装下载逻辑
"""

import os
from pathlib import Path
from typing import Optional
from interfaces import IPdfDownloader, IHttpClient


class PdfDownloader(IPdfDownloader):
    """
    PDF下载器
    使用代理模式，委托HTTP客户端进行下载
    支持Referer防盗链
    """
    
    def __init__(self, http_client: IHttpClient):
        """
        初始化下载器
        
        Args:
            http_client: HTTP客户端（通过组合注入）
        """
        self.http_client = http_client
        # 检查是否是Playwright客户端（优先）或Selenium客户端
        self.playwright_downloader = None
        self.selenium_downloader = None
        
        # 优先使用Playwright
        if hasattr(http_client, 'page') and http_client.page:
            try:
                from infrastructure.playwright_client import PlaywrightHttpClient
                if isinstance(http_client, PlaywrightHttpClient):
                    self.playwright_downloader = http_client
                    print(f"[提示] 检测到Playwright，将使用Playwright方式下载PDF")
            except Exception as e:
                print(f"[警告] 无法使用Playwright下载器: {str(e)}")
        
        # 如果没有Playwright，尝试Selenium
        if not self.playwright_downloader and hasattr(http_client, 'driver') and http_client.driver:
            try:
                from infrastructure.selenium_downloader import SeleniumPdfDownloader
                self.selenium_downloader = SeleniumPdfDownloader(http_client)
                print(f"[提示] 检测到Selenium，将使用浏览器方式下载PDF")
            except Exception as e:
                print(f"[警告] 无法创建Selenium下载器: {str(e)}")
                self.selenium_downloader = None
    
    def download(self, pdf_url: str, save_path: str, referer: str = None) -> bool:
        """
        下载PDF文件
        
        Args:
            pdf_url: PDF链接
            save_path: 保存路径（完整路径，包含文件名）
            referer: 来源页URL（用于防盗链验证）
            
        Returns:
            是否下载成功
        """
        try:
            # 确保目录存在
            save_dir = Path(save_path).parent
            save_dir.mkdir(parents=True, exist_ok=True)
            
            # 如果可以使用Playwright下载器，优先使用（最可靠）
            if self.playwright_downloader:
                print(f"[提示] 使用Playwright方式下载PDF（推荐）")
                return self.playwright_downloader.download_pdf(pdf_url, save_path, referer)
            
            # 如果没有Playwright，使用Selenium下载器
            if self.selenium_downloader:
                print(f"[提示] 使用Selenium浏览器方式下载PDF（绕过反爬虫）")
                return self.selenium_downloader.download(pdf_url, save_path, referer)
            
            # 使用HTTP客户端下载（委托，带Referer）
            response_data, content_type = self._download_file(pdf_url, referer)
            if response_data is None:
                return False
            
            # 检查Content-Type
            if content_type and not content_type.startswith('application/pdf'):
                print(f"[警告] Content-Type不是PDF: {content_type}")
                # 检查内容开头
                if response_data[:5] != b'%PDF-':
                    print(f"[错误] 下载的不是PDF文件！")
                    print(f"[调试] 文件开头: {response_data[:100]}")
                    return False
            
            # 检查文件大小
            file_size = len(response_data)
            print(f"[调试] 下载文件大小: {file_size} 字节 ({file_size/1024:.2f} KB)")
            
            # 验证是否是有效的PDF文件（PDF文件必须以%PDF-开头）
            if response_data[:5] != b'%PDF-':
                print(f"[错误] 文件不是有效的PDF格式！")
                print(f"[调试] 文件开头（前20字节）: {response_data[:20]}")
                # 尝试解码为文本查看错误信息
                try:
                    error_text = response_data[:200].decode('utf-8', errors='ignore')
                    print(f"[调试] 错误内容: {error_text}")
                except:
                    pass
                return False
            
            # 检查文件大小是否合理
            if file_size < 1024:
                print(f"[警告] 文件太小（{file_size}字节），可能不完整")
            
            # 保存文件
            with open(save_path, 'wb') as f:
                f.write(response_data)
            
            # 验证保存的文件
            saved_size = Path(save_path).stat().st_size
            if saved_size != file_size:
                print(f"[警告] 文件大小不匹配: 下载{file_size}字节，保存{saved_size}字节")
                return False
            
            print(f"[成功] PDF文件已保存: {save_path}")
            return True
        except Exception as e:
            print(f"下载PDF失败 {pdf_url}: {str(e)}")
            import traceback
            print(f"[错误详情] {traceback.format_exc()}")
            return False
    
    def _download_file(self, url: str, referer: str = None) -> tuple[Optional[bytes], Optional[str]]:
        """
        下载文件内容（委托方法）
        支持Referer防盗链
        
        Args:
            url: 文件URL
            referer: 来源页URL（用于防盗链）
            
        Returns:
            (文件内容（字节）, Content-Type)，失败返回(None, None)
        """
        try:
            import requests
            
            # 构建请求头（关键：必须包含Referer）
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/pdf,application/octet-stream,*/*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            }
            
            # 添加Referer（关键！pdf.dfcfw.com需要这个）
            if referer:
                headers['Referer'] = referer
            else:
                # 如果没有提供Referer，尝试从URL推断
                if 'eastmoney.com' in url or 'dfcfw.com' in url:
                    # 使用通用的东方财富域名作为Referer
                    headers['Referer'] = 'https://data.eastmoney.com/report/'
                else:
                    # 提取域名作为Referer
                    from urllib.parse import urlparse
                    parsed = urlparse(url)
                    headers['Referer'] = f"{parsed.scheme}://{parsed.netloc}/"
            
            print(f"[调试] 下载PDF，Referer: {headers['Referer']}")
            
            # 如果http_client有session，使用它；否则创建新请求
            if hasattr(self.http_client, 'session'):
                response = self.http_client.session.get(
                    url,
                    headers=headers,
                    timeout=30,
                    stream=True
                )
            else:
                response = requests.get(
                    url,
                    headers=headers,
                    timeout=30,
                    stream=True
                )
            
            response.raise_for_status()
            
            # 检查Content-Type
            content_type = response.headers.get('Content-Type', '')
            print(f"[调试] Content-Type: {content_type}")
            
            # 流式下载（避免内存问题）
            content = b''
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    content += chunk
            
            return content, content_type
        except Exception as e:
            print(f"下载文件失败 {url}: {str(e)}")
            import traceback
            print(f"[错误详情] {traceback.format_exc()}")
            return None, None

