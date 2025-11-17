"""
PDF 静态文件服务器（优化版）
解决线程问题和反爬虫问题
"""

from flask import Flask, send_file, jsonify, request
from flask_cors import CORS
import os
import hashlib
from pathlib import Path
from urllib.parse import unquote, urlparse
import sys
import threading
import queue
import time

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

app = Flask(__name__)
CORS(app)

# 配置
SERVER_PORT = 5001
PDF_CACHE_DIR = Path(__file__).parent / 'pdf_cache'
PDF_CACHE_DIR.mkdir(exist_ok=True)

# 全局 Playwright 实例（在主线程中运行）
_playwright_thread = None
_playwright_queue = queue.Queue()
_playwright_result = {}

def init_playwright_in_main_thread():
    """在主线程中初始化 Playwright（避免线程问题）"""
    global _playwright_thread
    
    try:
        from playwright.sync_api import sync_playwright
        
        print("[初始化] 在主线程中初始化 Playwright...")
        playwright = sync_playwright().start()
        
        # 启动浏览器（添加更多反检测参数）
        browser_args = [
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-blink-features=AutomationControlled',
            '--disable-web-security',
            '--disable-features=IsolateOrigins,site-per-process',
            '--disable-automation',  # 隐藏自动化特征
            '--disable-infobars',  # 隐藏"Chrome正在被自动化控制"提示
        ]
        
        browser = playwright.chromium.launch(
            headless=True,
            args=browser_args
        )
        
        # 创建上下文（使用更真实的浏览器指纹）
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='zh-CN',
            timezone_id='Asia/Shanghai',
            extra_http_headers={
                'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            },
            # 添加更多反检测特征
            java_script_enabled=True,
            has_touch=False,
            is_mobile=False,
            color_scheme='light',
        )
        
        # 注入反检测脚本
        context.add_init_script("""
            // 隐藏 webdriver 特征
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // 覆盖 plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            // 覆盖 languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['zh-CN', 'zh', 'en-US', 'en']
            });
            
            // 覆盖 permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)
        
        page = context.new_page()
        
        print("[初始化] ✅ Playwright 已初始化（主线程）")
        
        return {
            'playwright': playwright,
            'browser': browser,
            'context': context,
            'page': page
        }
    except Exception as e:
        print(f"[错误] Playwright 初始化失败: {e}")
        import traceback
        print(f"[调试] 错误详情: {traceback.format_exc()[:500]}")
        return None

# 全局 Playwright 实例
_playwright_instance = None

def get_playwright_instance():
    """获取 Playwright 实例（单例模式）"""
    global _playwright_instance
    
    if _playwright_instance is None:
        _playwright_instance = init_playwright_in_main_thread()
    
    return _playwright_instance

def download_pdf_with_playwright(pdf_url, save_path, referer=None):
    """
    使用 Playwright 下载 PDF（在主线程中运行）
    
    优化策略：
    1. 先访问详情页建立完整会话
    2. 等待足够长时间让会话建立
    3. 模拟真实用户行为（滚动、等待）
    4. 使用网络拦截获取 PDF 响应
    """
    instance = get_playwright_instance()
    if not instance:
        return False
    
    page = instance['page']
    context = instance['context']
    
    try:
        print(f"[下载] 开始下载 PDF: {pdf_url[:80]}...")
        
        # 步骤1：访问报告列表页建立基础会话
        print(f"[步骤1] 访问报告列表页建立基础会话...")
        try:
            page.goto('https://data.eastmoney.com/report/', wait_until='domcontentloaded', timeout=30000)
            time.sleep(3)  # 等待页面加载
            
            # 模拟用户行为：滚动页面
            page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
            time.sleep(1)
            page.evaluate("window.scrollTo(0, 0)")
            time.sleep(1)
            
            print(f"[成功] 基础会话已建立")
        except Exception as e:
            print(f"[警告] 建立基础会话失败: {str(e)[:100]}")
        
        # 步骤2：如果提供了 referer（详情页），先访问建立完整会话
        if referer and not referer.startswith('akshare://') and 'pdf.dfcfw.com' not in referer:
            print(f"[步骤2] 访问详情页建立完整会话: {referer[:80]}...")
            try:
                # 增加超时时间到 60 秒
                page.goto(referer, wait_until='domcontentloaded', timeout=60000)
                time.sleep(8)  # 增加等待时间，让会话充分建立
                
                # 模拟用户行为：滚动、点击等
                try:
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight / 3)")
                    time.sleep(1)
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight * 2 / 3)")
                    time.sleep(1)
                except:
                    pass
                
                # 等待页面完全加载（增加超时时间）
                try:
                    page.wait_for_load_state('networkidle', timeout=20000)
                except:
                    # 如果 networkidle 超时，继续执行
                    print(f"[提示] networkidle 超时，继续执行")
                
                print(f"[成功] 详情页会话已建立")
            except Exception as e:
                print(f"[警告] 访问详情页失败: {str(e)[:100]}")
                # 即使失败也继续，可能不需要详情页
        
        # 步骤3：使用网络拦截获取 PDF
        print(f"[步骤3] 使用网络拦截获取 PDF...")
        
        pdf_content = None
        pdf_received = threading.Event()
        
        def handle_response(response):
            """处理 PDF 响应"""
            nonlocal pdf_content
            url = response.url
            
            # 检查是否是 PDF URL
            if 'pdf.dfcfw.com' in url and (url.endswith('.pdf') or 'pdf' in url.lower()):
                try:
                    if response.status == 200:
                        pdf_content = response.body()
                        print(f"[调试] 通过网络拦截获取到 {len(pdf_content)} 字节")
                        pdf_received.set()
                except Exception as e:
                    print(f"[警告] 获取响应体失败: {str(e)[:100]}")
        
        # 监听响应
        page.on('response', handle_response)
        
        try:
            # 设置 Referer
            referer_header = referer if (referer and 'pdf.dfcfw.com' not in referer) else 'https://data.eastmoney.com/report/'
            page.set_extra_http_headers({
                'Referer': referer_header,
                'Accept': 'application/pdf,application/octet-stream,*/*',
            })
            
            # 访问 PDF URL（从当前页面跳转，保持会话）
            print(f"[调试] 访问 PDF URL: {pdf_url[:80]}...")
            
            # 使用 JavaScript 跳转，保持会话连续性
            try:
                page.evaluate(f'window.location.href = "{pdf_url}"')
            except Exception as e:
                print(f"[警告] JavaScript 跳转失败，尝试直接 goto: {str(e)[:100]}")
                # 如果 JavaScript 跳转失败，尝试直接 goto
                try:
                    page.goto(pdf_url, wait_until='domcontentloaded', timeout=60000)
                    time.sleep(3)
                except Exception as e2:
                    print(f"[错误] 直接 goto 也失败: {str(e2)[:100]}")
            
            # 等待 PDF 响应（增加到60秒）
            if pdf_received.wait(timeout=60):
                page.remove_listener('response', handle_response)
                
                if pdf_content and len(pdf_content) >= 5 and pdf_content[:5] == b'%PDF-':
                    # 保存文件
                    save_dir = Path(save_path).parent
                    save_dir.mkdir(parents=True, exist_ok=True)
                    
                    with open(save_path, 'wb') as f:
                        f.write(pdf_content)
                    
                    file_size = len(pdf_content)
                    print(f"[成功] ✅ PDF 下载成功: {save_path} ({file_size} 字节)")
                    return True
                else:
                    print(f"[错误] 获取的内容不是 PDF")
                    if pdf_content:
                        print(f"[调试] 内容开头: {pdf_content[:100]}")
                    return False
            else:
                print(f"[错误] 等待 PDF 响应超时")
                page.remove_listener('response', handle_response)
                return False
                
        except Exception as e:
            print(f"[错误] 网络拦截失败: {str(e)}")
            import traceback
            print(f"[调试] 错误详情: {traceback.format_exc()[:300]}")
            page.remove_listener('response', handle_response)
            return False
        
    except Exception as e:
        print(f"[错误] Playwright 下载失败: {str(e)}")
        import traceback
        print(f"[调试] 错误详情: {traceback.format_exc()[:500]}")
        return False

def get_pdf_filename(url):
    """根据 URL 生成文件名"""
    url_hash = hashlib.md5(url.encode()).hexdigest()
    parsed = urlparse(url)
    original_filename = Path(parsed.path).name
    if original_filename.endswith('.pdf'):
        return f"{url_hash}_{original_filename}"
    return f"{url_hash}.pdf"

@app.route('/pdf/<filename>')
def serve_pdf(filename):
    """提供静态 PDF 文件"""
    pdf_path = PDF_CACHE_DIR / filename
    if pdf_path.exists():
        return send_file(str(pdf_path), mimetype='application/pdf')
    else:
        return jsonify({'error': 'PDF 文件不存在'}), 404

@app.route('/download-and-serve')
def download_and_serve():
    """
    下载 PDF 并返回本地路径
    使用方式: /download-and-serve?url=PDF_URL&referer=REFERER_URL
    """
    try:
        pdf_url = request.args.get('url')
        referer = request.args.get('referer', 'https://data.eastmoney.com/report/')
        
        if not pdf_url:
            return jsonify({'error': '缺少 url 参数'}), 400
        
        pdf_url = unquote(pdf_url)
        referer = unquote(referer)
        
        # 检查缓存
        filename = get_pdf_filename(pdf_url)
        cached_path = PDF_CACHE_DIR / filename
        
        if cached_path.exists():
            print(f"[缓存] 使用缓存的 PDF: {filename}")
            return jsonify({
                'success': True,
                'url': f'/pdf/{filename}',
                'cached': True
            })
        
        # 下载 PDF（使用优化的 Playwright 方法）
        print(f"[下载] 开始下载 PDF: {pdf_url[:80]}...")
        
        success = download_pdf_with_playwright(pdf_url, str(cached_path), referer)
        
        if success and cached_path.exists():
            # 验证文件
            with open(cached_path, 'rb') as f:
                header = f.read(5)
                if header != b'%PDF-':
                    print(f"[错误] 下载的文件不是 PDF")
                    cached_path.unlink()
                    return jsonify({'error': '下载的文件不是有效的 PDF'}), 400
            
            file_size = cached_path.stat().st_size
            print(f"[成功] ✅ PDF 下载成功: {filename} ({file_size} 字节)")
            
            return jsonify({
                'success': True,
                'url': f'/pdf/{filename}',
                'cached': False,
                'size': file_size
            })
        else:
            return jsonify({'error': 'PDF 下载失败，可能被反爬虫拦截'}), 500
            
    except Exception as e:
        print(f"[错误] 下载失败: {e}")
        import traceback
        print(f"[调试] 错误详情: {traceback.format_exc()[:500]}")
        return jsonify({'error': f'服务器错误: {str(e)}'}), 500

@app.route('/health')
def health():
    """健康检查"""
    instance = get_playwright_instance()
    return jsonify({
        'status': 'ok',
        'service': 'PDF Static Server (Optimized)',
        'cache_dir': str(PDF_CACHE_DIR),
        'cached_files': len(list(PDF_CACHE_DIR.glob('*.pdf'))),
        'playwright_ready': instance is not None
    })

@app.route('/')
def index():
    """根路径"""
    return jsonify({
        'service': 'PDF Static Server (Optimized)',
        'endpoints': {
            'health': '/health',
            'download': '/download-and-serve?url=PDF_URL&referer=REFERER_URL',
            'serve': '/pdf/<filename>'
        },
        'cache_dir': str(PDF_CACHE_DIR),
        'cached_files': len(list(PDF_CACHE_DIR.glob('*.pdf')))
    })

if __name__ == '__main__':
    print("=" * 60)
    print("PDF 静态文件服务器（优化版）")
    print("=" * 60)
    print(f"服务地址: http://localhost:{SERVER_PORT}")
    print(f"缓存目录: {PDF_CACHE_DIR}")
    print("=" * 60)
    
    # 在主线程中初始化 Playwright
    print("\n[初始化] 在主线程中初始化 Playwright...")
    get_playwright_instance()
    
    print("=" * 60)
    print("按 Ctrl+C 停止服务器")
    print("=" * 60)
    print()
    
    try:
        app.run(host='0.0.0.0', port=SERVER_PORT, debug=False, threaded=False)  # 单线程模式
    finally:
        # 清理资源
        instance = get_playwright_instance()
        if instance:
            try:
                instance['context'].close()
                instance['browser'].close()
                instance['playwright'].stop()
                print("[清理] Playwright 资源已关闭")
            except:
                pass

