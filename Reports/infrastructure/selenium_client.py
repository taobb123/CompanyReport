"""
Selenium HTTP客户端实现
用于处理JavaScript动态加载的页面
"""

from typing import Optional
from interfaces import IHttpClient


class SeleniumHttpClient(IHttpClient):
    """
    Selenium HTTP客户端
    使用Selenium WebDriver渲染JavaScript动态内容
    """
    
    def __init__(self, timeout: int = 30, headless: bool = True):
        """
        初始化Selenium客户端
        
        Args:
            timeout: 页面加载超时时间（秒）
            headless: 是否使用无头模式
        """
        self.timeout = timeout
        self.headless = headless
        self.driver = None
        self._init_driver()
    
    def _init_driver(self):
        """初始化WebDriver"""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
            # 抑制WebGL和其他警告信息
            chrome_options.add_argument('--disable-logging')
            chrome_options.add_argument('--log-level=3')
            chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # 尝试使用webdriver-manager自动管理ChromeDriver
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                from selenium.webdriver.chrome.service import Service
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                print(f"[成功] 使用webdriver-manager自动配置ChromeDriver")
            except ImportError:
                # 如果没有webdriver-manager，尝试直接使用系统PATH中的ChromeDriver
                try:
                    self.driver = webdriver.Chrome(options=chrome_options)
                    print(f"[成功] 使用系统PATH中的ChromeDriver")
                except Exception as e:
                    print(f"[警告] 无法创建Chrome WebDriver: {str(e)}")
                    print(f"[提示] 解决方案1: 安装webdriver-manager自动管理驱动")
                    print(f"      pip install webdriver-manager")
                    print(f"[提示] 解决方案2: 手动安装ChromeDriver")
                    print(f"      1. 下载ChromeDriver: https://chromedriver.chromium.org/")
                    print(f"      2. 确保ChromeDriver在系统PATH中")
                    print(f"      3. 或使用: pip install selenium")
                    self.driver = None
            except Exception as e:
                # webdriver-manager失败，尝试直接使用
                try:
                    self.driver = webdriver.Chrome(options=chrome_options)
                    print(f"[成功] 使用系统PATH中的ChromeDriver")
                except Exception as e2:
                    print(f"[警告] 无法创建Chrome WebDriver")
                    print(f"[错误] webdriver-manager方式: {str(e)}")
                    print(f"[错误] 直接方式: {str(e2)}")
                    print(f"[提示] 请安装: pip install webdriver-manager")
                    print(f"[提示] 或手动配置ChromeDriver")
                    self.driver = None
        except ImportError:
            print(f"[警告] Selenium未安装，无法使用JavaScript渲染功能")
            print(f"[提示] 请安装: pip install selenium webdriver-manager")
            self.driver = None
    
    def get(self, url: str, wait_time: int = 5, **kwargs) -> Optional[str]:
        """
        发送GET请求并等待JavaScript渲染
        
        Args:
            url: 请求URL
            wait_time: 等待JavaScript渲染的时间（秒）
            **kwargs: 其他参数（忽略）
            
        Returns:
            渲染后的HTML内容，失败返回None
        """
        if not self.driver:
            print(f"[错误] Selenium WebDriver未初始化，无法获取动态内容")
            return None
        
        try:
            # 访问页面
            self.driver.get(url)
            
            # 等待页面加载（等待表格出现）
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.common.by import By
            
            try:
                # 等待表格加载（最多等待wait_time秒）
                WebDriverWait(self.driver, wait_time).until(
                    EC.presence_of_element_located((By.TAG_NAME, "table"))
                )
                print(f"[调试] 检测到表格已加载")
            except:
                # 如果表格没出现，至少等待页面基本加载
                import time
                time.sleep(2)
                print(f"[调试] 等待页面加载完成（表格可能未出现）")
            
            # 获取渲染后的HTML
            html_content = self.driver.page_source
            return html_content
        except Exception as e:
            print(f"Selenium请求失败 {url}: {str(e)}")
            return None
    
    def close(self):
        """关闭WebDriver"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass

