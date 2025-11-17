"""
Playwright HTTP客户端实现
更现代、更强大的浏览器自动化工具
推荐用于处理复杂的反爬虫场景
"""

from typing import Optional
from interfaces import IHttpClient


class PlaywrightHttpClient(IHttpClient):
    """
    Playwright HTTP客户端
    使用Playwright进行浏览器自动化，比Selenium更强大
    """
    
    def __init__(self, timeout: int = 30, headless: bool = True):
        """
        初始化Playwright客户端
        
        Args:
            timeout: 页面加载超时时间（秒）
            headless: 是否使用无头模式
        """
        self.timeout = timeout
        self.headless = headless
        self.browser = None
        self.context = None
        self.page = None
        self._init_playwright()
    
    def _init_playwright(self):
        """初始化Playwright"""
        try:
            from playwright.sync_api import sync_playwright
            
            self.playwright = sync_playwright().start()
            
            # 启动浏览器（添加更多反检测参数）
            browser_args = [
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',  # 允许跨域（某些情况下需要）
                '--disable-features=IsolateOrigins,site-per-process',
            ]
            
            self.browser = self.playwright.chromium.launch(
                headless=self.headless,
                args=browser_args
            )
            
            # 创建上下文（可以设置Cookie、User-Agent等）
            # 使用更真实的浏览器指纹
            self.context = self.browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
                locale='zh-CN',
                timezone_id='Asia/Shanghai',
                # 添加更多浏览器特征
                extra_http_headers={
                    'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
                }
            )
            
            # 创建页面
            self.page = self.context.new_page()
            
            print(f"[成功] Playwright初始化成功")
        except ImportError:
            print(f"[警告] Playwright未安装")
            print(f"[提示] 请安装: pip install playwright")
            print(f"[提示] 然后运行: playwright install chromium")
            self.browser = None
        except Exception as e:
            print(f"[警告] Playwright初始化失败: {str(e)}")
            self.browser = None
    
    def get(self, url: str, wait_time: int = 5, **kwargs) -> Optional[str]:
        """
        发送GET请求并等待JavaScript渲染
        
        Args:
            url: 请求URL
            wait_time: 等待时间（秒）
            **kwargs: 其他参数
            
        Returns:
            渲染后的HTML内容，失败返回None
        """
        if not self.page:
            print(f"[错误] Playwright未初始化")
            return None
        
        try:
            # 访问页面（使用更宽松的等待策略）
            # 'load' 比 'networkidle' 更宽松，只等待页面load事件
            # 如果还是超时，可以改用 'domcontentloaded'
            try:
                self.page.goto(url, wait_until='load', timeout=self.timeout * 1000)
            except Exception as timeout_error:
                # 如果load也超时，尝试domcontentloaded（更宽松）
                print(f"[警告] load超时，尝试domcontentloaded: {str(timeout_error)[:100]}")
                try:
                    self.page.goto(url, wait_until='domcontentloaded', timeout=self.timeout * 1000)
                except Exception as e2:
                    print(f"[警告] domcontentloaded也超时，继续执行: {str(e2)[:100]}")
                    # 即使超时也继续，可能页面已经部分加载
            
            # 等待指定时间（让JavaScript有时间执行）
            import time
            time.sleep(wait_time)
            
            # 尝试等待表格出现（如果页面有表格）
            try:
                from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
                # 等待表格出现（最多5秒）
                self.page.wait_for_selector('table', timeout=5000)
                print(f"[调试] 检测到表格已加载")
            except PlaywrightTimeoutError:
                # 表格可能不存在或加载较慢，继续执行
                print(f"[调试] 未检测到表格，继续执行")
            except Exception:
                # 其他错误忽略
                pass
            
            # 获取渲染后的HTML
            html_content = self.page.content()
            return html_content
        except Exception as e:
            print(f"Playwright请求失败 {url}: {str(e)}")
            import traceback
            print(f"[错误详情] {traceback.format_exc()[:500]}")
            return None
    
    def get_cookies(self, referer_url: str = None) -> list:
        """
        获取当前会话的Cookie（在主线程中调用）
        
        Args:
            referer_url: 详情页URL（如果提供，先访问建立会话）
        
        Returns:
            Cookie列表
        """
        if not self.page:
            return []
        
        try:
            # 如果提供了详情页URL，先访问建立会话（更可靠）
            if referer_url and not referer_url.startswith('akshare://'):
                print(f"[调试] 访问详情页建立会话: {referer_url[:80]}...")
                try:
                    self.page.goto(referer_url, wait_until='load', timeout=self.timeout * 1000)
                except:
                    try:
                        self.page.goto(referer_url, wait_until='domcontentloaded', timeout=self.timeout * 1000)
                    except:
                        print(f"[警告] 访问详情页失败，使用列表页")
                        # 回退到列表页
                        try:
                            self.page.goto('https://data.eastmoney.com/report/', wait_until='domcontentloaded', timeout=self.timeout * 1000)
                        except:
                            pass
                import time
                time.sleep(2)
            elif not hasattr(self, '_cookies_cached'):
                # 访问报告列表页建立会话
                print(f"[调试] 访问报告列表页建立会话...")
                try:
                    self.page.goto('https://data.eastmoney.com/report/', wait_until='load', timeout=self.timeout * 1000)
                except:
                    try:
                        self.page.goto('https://data.eastmoney.com/report/', wait_until='domcontentloaded', timeout=self.timeout * 1000)
                    except:
                        pass
                import time
                time.sleep(2)
            
            cookies = self.context.cookies()
            if not hasattr(self, '_cookies_cached'):
                self._cookies_cached = cookies
            return cookies
        except Exception as e:
            print(f"[警告] 获取Cookie失败: {str(e)}")
            return []
    
    def download_pdf(self, pdf_url: str, save_path: str, referer: str = None, cookies: list = None) -> bool:
        """
        使用Playwright下载PDF
        方法：获取Cookie后用requests下载（最可靠）
        注意：不直接使用Playwright访问PDF URL，避免ERR_ABORTED错误
        
        Args:
            pdf_url: PDF URL
            save_path: 保存路径
            referer: 来源页URL（关键！）
            
        Returns:
            是否成功
        """
        if not self.page:
            print(f"[错误] Playwright未初始化")
            return False
        
        try:
            # 方法1：尝试使用Playwright直接下载（最接近真实浏览器）
            # 如果失败，回退到requests方式
            print(f"[方法] 尝试使用Playwright直接下载PDF（最接近真实浏览器）")
            
            # 先访问报告列表页建立基础会话
            if not hasattr(self, '_session_established'):
                print(f"[步骤1] 访问报告列表页建立基础会话...")
                try:
                    self.page.goto('https://data.eastmoney.com/report/', wait_until='domcontentloaded', timeout=self.timeout * 1000)
                    import time
                    time.sleep(5)  # 增加等待时间，让会话充分建立
                    self._session_established = True
                    print(f"[成功] 基础会话已建立")
                except Exception as e:
                    print(f"[警告] 建立基础会话失败: {str(e)}")
            
            # 关键：如果提供了referer（详情页URL），先访问建立更完整的会话
            if referer and not referer.startswith('akshare://') and 'pdf.dfcfw.com' not in referer:
                print(f"[步骤1.5] 访问详情页建立完整会话: {referer[:80]}...")
                try:
                    self.page.goto(referer, wait_until='domcontentloaded', timeout=self.timeout * 1000)
                    import time
                    time.sleep(3)  # 等待详情页加载和会话建立
                    print(f"[成功] 详情页会话已建立")
                except Exception as e:
                    print(f"[警告] 访问详情页失败: {str(e)}")
            
            # 方法1：使用Playwright网络拦截获取PDF响应体（PDF在浏览器中直接显示时）
            try:
                print(f"[步骤2] 使用Playwright网络拦截获取PDF响应体...")
                
                # 设置Referer
                if referer and not referer.startswith('akshare://') and 'pdf.dfcfw.com' not in referer:
                    referer_header = referer
                else:
                    referer_header = 'https://data.eastmoney.com/report/'
                
                # 设置额外的HTTP头（包括Referer）
                self.page.set_extra_http_headers({
                    'Referer': referer_header,
                    'Accept': 'application/pdf,application/octet-stream,*/*',
                })
                
                from pathlib import Path
                save_dir = Path(save_path).parent
                save_dir.mkdir(parents=True, exist_ok=True)
                
                # 使用网络拦截捕获PDF响应
                pdf_content = None
                
                # 监听PDF响应
                def check_pdf_response(response):
                    url = response.url
                    # 检查是否是PDF URL
                    if 'pdf.dfcfw.com' in url and (url.endswith('.pdf') or 'pdf' in url.lower()):
                        return True
                    return False
                
                try:
                    with self.page.expect_response(check_pdf_response, timeout=30 * 1000) as response_info:
                        # 访问PDF URL（从当前页面跳转，保持会话）
                        print(f"[调试] 从当前页面访问PDF URL: {pdf_url[:80]}...")
                        # 使用JavaScript跳转，保持会话连续性
                        self.page.evaluate(f'window.location.href = "{pdf_url}"')
                        # 或者直接goto
                        # self.page.goto(pdf_url, wait_until='networkidle', timeout=30 * 1000)
                        import time
                        time.sleep(5)  # 增加等待时间，确保PDF加载完成
                    
                    pdf_response = response_info.value
                    if pdf_response:
                        # 检查响应状态
                        if pdf_response.status != 200:
                            print(f"[警告] PDF响应状态码: {pdf_response.status}")
                        
                        # 获取响应体
                        pdf_content = pdf_response.body()
                        print(f"[调试] 通过网络拦截获取到 {len(pdf_content)} 字节")
                        
                        # 验证是否是PDF
                        if len(pdf_content) >= 5 and pdf_content[:5] == b'%PDF-':
                            print(f"[成功] 通过Playwright网络拦截获取到有效PDF")
                            # 保存文件
                            with open(save_path, 'wb') as f:
                                f.write(pdf_content)
                            
                            file_size = len(pdf_content)
                            print(f"[成功] PDF文件已保存: {save_path} ({file_size/1024:.2f} KB)")
                            return True
                        else:
                            print(f"[警告] 网络拦截获取的内容不是PDF")
                            print(f"[调试] 内容开头: {pdf_content[:100]}")
                            # 尝试下载API
                except Exception as download_error:
                    print(f"[警告] 网络拦截失败: {str(download_error)}")
                    # 尝试下载API
                
                # 方法1.5：如果网络拦截失败，尝试下载API（PDF触发下载时）
                try:
                    print(f"[步骤2.5] 尝试使用Playwright下载API...")
                    with self.page.expect_download(timeout=10 * 1000) as download_info:
                        # 如果PDF触发下载，这里会捕获
                        self.page.goto(pdf_url, wait_until='networkidle', timeout=30 * 1000)
                        import time
                        time.sleep(2)
                    
                    download = download_info.value
                    if download:
                        download.save_as(save_path)
                        if Path(save_path).exists():
                            with open(save_path, 'rb') as f:
                                header = f.read(5)
                                if header == b'%PDF-':
                                    print(f"[成功] 通过Playwright下载API获取到有效PDF")
                                    return True
                except:
                    # 下载API也失败，继续到requests方式
                    pass
                    
            except Exception as e:
                print(f"[警告] Playwright方法失败: {str(e)}")
                import traceback
                print(f"[调试] 错误详情: {traceback.format_exc()[:300]}")
                print(f"[提示] 回退到requests方式...")
            
            # 方法2：使用requests下载（带Cookie）
            print(f"[方法] 使用requests下载PDF（带完整Cookie和请求头）")
            
            # 获取Cookie
            if cookies is None:
                print(f"[步骤1] 获取Cookie...")
                cookies = self.get_cookies()
                print(f"[步骤2] 获取到 {len(cookies)} 个Cookie")
            else:
                print(f"[步骤1] 使用提供的Cookie（{len(cookies)}个）")
            
            # 2. 使用requests下载PDF（带Cookie和Referer）
            # 关键：不直接使用Playwright访问PDF URL，避免ERR_ABORTED
            # 关键：不在并发线程中调用Playwright API，避免greenlet错误
            import requests
            session = requests.Session()
            
            # 添加Cookie到session
            if cookies:
                for cookie in cookies:
                    try:
                        session.cookies.set(
                            cookie['name'],
                            cookie['value'],
                            domain=cookie.get('domain', ''),
                            path=cookie.get('path', '/')
                        )
                    except:
                        pass
            
            # 构建请求头（关键：正确的Referer）
            # Referer应该是来源页URL，不能是PDF URL本身
            referer_header = 'https://data.eastmoney.com/report/'
            if referer and not referer.startswith('akshare://') and 'pdf.dfcfw.com' not in referer:
                # 如果referer是详情页URL（不是PDF URL），使用它
                referer_header = referer
            # 如果referer是PDF URL或没有referer，使用报告列表页作为Referer
            # 这是最安全的默认值
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/pdf,application/octet-stream,*/*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
                'Referer': referer_header,
                'Origin': 'https://data.eastmoney.com',  # 添加Origin头
                'Connection': 'keep-alive',
                'Cache-Control': 'no-cache',
                'Sec-Fetch-Dest': 'document',  # 模拟浏览器行为
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'cross-site',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1',
            }
            
            print(f"[步骤2] 使用requests下载PDF（不通过Playwright，避免ERR_ABORTED和greenlet错误）")
            print(f"[调试] PDF URL: {pdf_url[:80]}...")
            print(f"[调试] Referer: {headers['Referer']}")
            print(f"[调试] Cookie数量: {len(cookies) if cookies else 0}")
            
            # 下载PDF（使用requests）
            # 关键：使用完整的浏览器请求头，模拟真实访问
            try:
                # 直接流式下载，检查内容而不是Content-Type（因为服务器可能撒谎）
                print(f"[步骤3] 开始下载PDF...")
                response = session.get(
                    pdf_url, 
                    headers=headers, 
                    timeout=30, 
                    stream=True,  # 流式下载
                    allow_redirects=True
                )
                response.raise_for_status()
                
                # 检查Content-Type（仅供参考，不依赖它）
                content_type = response.headers.get('Content-Type', '')
                print(f"[调试] Content-Type: {content_type}")
                
            except requests.exceptions.RequestException as e:
                print(f"[错误] requests下载失败: {str(e)}")
                return False
            
            # 流式下载，同时检查前几个字节
            content = b''
            first_chunk = True
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    content += chunk
                    # 检查前几个字节，如果是JavaScript立即停止
                    if first_chunk and len(content) >= 10:
                        first_chunk = False
                        if content[:5] != b'%PDF-':
                            # 不是PDF，检查是否是JavaScript
                            if b'<script>' in content[:200] or b'function' in content[:200]:
                                print(f"[错误] 检测到JavaScript验证页面，停止下载")
                                print(f"[调试] 文件开头: {content[:100]}")
                                # 尝试解码查看错误信息
                                try:
                                    error_text = content[:500].decode('utf-8', errors='ignore')
                                    if error_text:
                                        print(f"[调试] 错误内容: {error_text[:200]}")
                                except:
                                    pass
                                return False
            
            # 验证PDF（检查文件大小和开头）
            if len(content) < 1024:  # PDF文件通常至少几KB
                print(f"[错误] 文件太小（{len(content)}字节），不是有效的PDF")
                print(f"[调试] 文件开头: {content[:100]}")
                return False
            
            if len(content) < 5 or content[:5] != b'%PDF-':
                print(f"[错误] 下载的不是PDF文件！")
                print(f"[调试] 文件大小: {len(content)} 字节")
                print(f"[调试] 文件开头（前100字节）: {content[:100]}")
                # 尝试解码查看错误信息
                try:
                    error_text = content[:500].decode('utf-8', errors='ignore')
                    if error_text and ('验证' in error_text or '失败' in error_text or 'code' in error_text or '<script>' in error_text):
                        print(f"[调试] 错误内容: {error_text[:200]}")
                except:
                    pass
                return False
            
            # 保存文件
            file_size = len(content)
            print(f"[步骤3] PDF文件大小: {file_size} 字节 ({file_size/1024:.2f} KB)")
            
            from pathlib import Path
            save_dir = Path(save_path).parent
            save_dir.mkdir(parents=True, exist_ok=True)
            
            with open(save_path, 'wb') as f:
                f.write(content)
            
            # 验证保存的文件
            saved_size = Path(save_path).stat().st_size
            if saved_size == file_size:
                print(f"[成功] PDF文件已保存: {save_path}")
                return True
            else:
                print(f"[警告] 文件大小不匹配: 下载{file_size}字节，保存{saved_size}字节")
                return False
            
        except Exception as e:
            print(f"Playwright下载PDF失败: {str(e)}")
            import traceback
            print(f"[错误详情] {traceback.format_exc()}")
            return False
    
    def close(self):
        """关闭Playwright"""
        try:
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if hasattr(self, 'playwright'):
                self.playwright.stop()
        except:
            pass

