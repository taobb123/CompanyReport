"""
基于Selenium的PDF下载器
完全模拟浏览器行为，绕过反爬虫限制
"""

from pathlib import Path
from typing import Optional
from interfaces import IPdfDownloader


class SeleniumPdfDownloader(IPdfDownloader):
    """
    基于Selenium的PDF下载器
    通过浏览器直接下载PDF，绕过防盗链限制
    """
    
    def __init__(self, selenium_client):
        """
        初始化下载器
        
        Args:
            selenium_client: Selenium HTTP客户端
        """
        self.selenium_client = selenium_client
    
    def download(self, pdf_url: str, save_path: str, referer: str = None) -> bool:
        """
        使用Selenium下载PDF文件
        方法：获取Cookie后用requests下载（最可靠）
        
        Args:
            pdf_url: PDF链接
            save_path: 保存路径
            referer: 来源页URL（关键！）
            
        Returns:
            是否下载成功
        """
        if not self.selenium_client or not self.selenium_client.driver:
            print(f"[错误] Selenium WebDriver未初始化")
            return False
        
        try:
            driver = self.selenium_client.driver
            
            # 方法1（推荐）：使用Selenium获取Cookie，然后用requests下载
            print(f"[方法] 使用Selenium获取Cookie，然后用requests下载PDF")
            
            # 1. 先访问详情页建立会话（获取Cookie）
            if referer:
                print(f"[步骤1] 访问详情页建立会话: {referer[:80]}...")
                driver.get(referer)
                import time
                time.sleep(2)  # 等待页面加载和Cookie设置
            else:
                # 如果没有Referer，访问报告列表页
                print(f"[步骤1] 访问报告列表页建立会话")
                driver.get('https://data.eastmoney.com/report/')
                import time
                time.sleep(2)
            
            # 2. 获取所有Cookie
            cookies = driver.get_cookies()
            print(f"[步骤2] 获取到 {len(cookies)} 个Cookie")
            
            # 3. 使用requests下载PDF（带Cookie和Referer）
            import requests
            session = requests.Session()
            
            # 添加Cookie到session
            for cookie in cookies:
                session.cookies.set(cookie['name'], cookie['value'])
            
            # 构建请求头
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/pdf,application/octet-stream,*/*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Referer': referer if referer else 'https://data.eastmoney.com/report/',
                'Connection': 'keep-alive',
            }
            
            print(f"[步骤3] 使用requests下载PDF: {pdf_url[:80]}...")
            print(f"[调试] Referer: {headers['Referer']}")
            
            # 下载PDF
            response = session.get(pdf_url, headers=headers, timeout=30, stream=True)
            response.raise_for_status()
            
            # 检查Content-Type
            content_type = response.headers.get('Content-Type', '')
            print(f"[调试] Content-Type: {content_type}")
            
            # 流式下载
            content = b''
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    content += chunk
            
            # 验证PDF
            if content[:5] != b'%PDF-':
                print(f"[错误] 下载的不是PDF文件！")
                print(f"[调试] 文件开头（前100字节）: {content[:100]}")
                # 尝试解码查看错误信息
                try:
                    error_text = content[:500].decode('utf-8', errors='ignore')
                    if error_text:
                        print(f"[调试] 错误内容: {error_text[:200]}")
                except:
                    pass
                return False
            
            # 保存文件
            file_size = len(content)
            print(f"[步骤4] PDF文件大小: {file_size} 字节 ({file_size/1024:.2f} KB)")
            
            with open(save_path, 'wb') as f:
                f.write(content)
            
            return self._verify_pdf(save_path)
            
        except Exception as e:
            print(f"Selenium下载PDF失败: {str(e)}")
            import traceback
            print(f"[错误详情] {traceback.format_exc()}")
            return False
    
    def _download_from_network_log_old(self, driver, pdf_url: str, save_path: str) -> bool:
        """
        从浏览器网络日志中获取PDF
        
        Args:
            driver: WebDriver实例
            pdf_url: PDF URL
            save_path: 保存路径
            
        Returns:
            是否成功
        """
        try:
            # 使用Chrome DevTools Protocol获取网络请求
            from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
            
            # 获取性能日志
            driver.execute_cdp_cmd('Network.enable', {})
            
            # 重新请求PDF
            driver.get(pdf_url)
            import time
            time.sleep(3)
            
            # 获取网络日志
            logs = driver.get_log('performance')
            for log in logs:
                message = log.get('message', {})
                if isinstance(message, str):
                    import json
                    message = json.loads(message)
                
                method = message.get('message', {}).get('method', '')
                if method == 'Network.responseReceived':
                    response = message.get('message', {}).get('params', {}).get('response', {})
                    url = response.get('url', '')
                    if 'pdf.dfcfw.com' in url and 'pdf' in url.lower():
                        # 找到了PDF响应
                        request_id = message.get('message', {}).get('params', {}).get('requestId', '')
                        # 获取响应体
                        response_body = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': request_id})
                        body = response_body.get('body', '')
                        if body:
                            # 解码base64
                            import base64
                            pdf_data = base64.b64decode(body)
                            if pdf_data.startswith(b'%PDF-'):
                                with open(save_path, 'wb') as f:
                                    f.write(pdf_data)
                                return self._verify_pdf(save_path)
            
            return False
        except Exception as e:
            print(f"[警告] 从网络日志获取PDF失败: {str(e)}")
            return False
    
    def _download_via_browser_old(self, driver, pdf_url: str, save_path: str) -> bool:
        """
        通过浏览器下载功能下载PDF
        
        Args:
            driver: WebDriver实例
            pdf_url: PDF URL
            save_path: 保存路径
            
        Returns:
            是否成功
        """
        try:
            # 设置下载路径
            download_dir = str(Path(save_path).parent)
            
            # Chrome下载设置
            download_prefs = {
                "download.default_directory": download_dir,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True
            }
            
            # 更新Chrome选项
            from selenium.webdriver.chrome.options import Options
            chrome_options = Options()
            chrome_options.add_experimental_option("prefs", download_prefs)
            
            # 访问PDF URL（浏览器会自动下载）
            driver.get(pdf_url)
            
            # 等待下载完成
            import time
            time.sleep(5)
            
            # 检查下载目录中的文件
            download_dir_path = Path(download_dir)
            pdf_files = list(download_dir_path.glob("*.pdf"))
            
            if pdf_files:
                # 找到最新的PDF文件
                latest_pdf = max(pdf_files, key=lambda p: p.stat().st_mtime)
                # 移动到目标位置
                import shutil
                shutil.move(str(latest_pdf), save_path)
                return self._verify_pdf(save_path)
            
            return False
        except Exception as e:
            print(f"[警告] 浏览器下载失败: {str(e)}")
            return False
    
    def _verify_pdf(self, file_path: str) -> bool:
        """
        验证PDF文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否有效
        """
        try:
            with open(file_path, 'rb') as f:
                header = f.read(5)
                if header == b'%PDF-':
                    file_size = Path(file_path).stat().st_size
                    print(f"[成功] PDF文件验证通过，大小: {file_size} 字节")
                    return True
                else:
                    print(f"[错误] 文件不是有效的PDF格式")
                    return False
        except Exception as e:
            print(f"[错误] 验证PDF失败: {str(e)}")
            return False

