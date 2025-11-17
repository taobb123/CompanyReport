"""
PDF 代理服务器
用于解决前端 CORS 跨域问题，代理 PDF 文件请求
使用 Playwright 绕过反爬虫机制
"""

from flask import Flask, request, Response, jsonify
from flask_cors import CORS
import requests
from urllib.parse import unquote, urlparse
import os
import tempfile
from pathlib import Path

# 尝试导入 Playwright（可选）
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("[警告] Playwright 未安装，将使用 requests（可能无法绕过反爬虫）")
    print("[提示] 安装: pip install playwright && playwright install chromium")

# 尝试使用项目中的 PlaywrightHttpClient（更完善的实现）
try:
    import sys
    from pathlib import Path
    # 添加项目根目录到路径
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    from infrastructure.playwright_client import PlaywrightHttpClient
    USE_PROJECT_PLAYWRIGHT = True
except Exception as e:
    USE_PROJECT_PLAYWRIGHT = False
    print(f"[提示] 无法导入项目中的 PlaywrightHttpClient: {e}")

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 配置
PROXY_PORT = 5000
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB 最大文件大小
TIMEOUT = 30  # 30秒超时

# Playwright 实例（全局，避免重复创建）
_playwright = None
_browser = None
_page = None
_playwright_initialized = False
_project_playwright_client = None

def init_playwright():
    """初始化 Playwright（在服务器启动时调用）"""
    global _playwright, _browser, _page, _playwright_initialized, _project_playwright_client
    
    if _playwright_initialized:
        return _page is not None or _project_playwright_client is not None
    
    _playwright_initialized = True
    
    # 优先使用项目中的 PlaywrightHttpClient（更完善的实现）
    if USE_PROJECT_PLAYWRIGHT:
        try:
            print("[Playwright] 正在初始化项目中的 PlaywrightHttpClient...")
            _project_playwright_client = PlaywrightHttpClient(timeout=TIMEOUT, headless=True)
            print("[Playwright] ✅ 使用项目中的 PlaywrightHttpClient（推荐）")
            return True
        except Exception as e:
            print(f"[警告] 初始化项目 PlaywrightHttpClient 失败: {e}")
            print("[提示] 回退到基础 Playwright 实现")
    
    # 回退到基础 Playwright 实现
    if not PLAYWRIGHT_AVAILABLE:
        print("[警告] Playwright 未安装，将使用 requests（可能无法绕过反爬虫）")
        print("[提示] 安装命令: pip install playwright && playwright install chromium")
        return False
    
    try:
        print("[Playwright] 正在初始化浏览器...")
        _playwright = sync_playwright().start()
        _browser = _playwright.chromium.launch(headless=True)
        _page = _browser.new_page()
        print("[Playwright] ✅ 浏览器实例已创建，可以绕过反爬虫")
        return True
    except Exception as e:
        print(f"[错误] 创建 Playwright 实例失败: {e}")
        print("[提示] 请确保已安装: pip install playwright && playwright install chromium")
        return False

def get_playwright_page():
    """获取 Playwright 页面实例"""
    global _playwright, _browser, _page, _project_playwright_client
    
    # 优先返回项目中的 PlaywrightHttpClient
    if _project_playwright_client and _project_playwright_client.page:
        return _project_playwright_client.page
    
    if not PLAYWRIGHT_AVAILABLE:
        return None
    
    if _page is None:
        # 如果未初始化，尝试初始化
        if not _playwright_initialized:
            init_playwright()
    
    return _page


@app.route('/pdf-proxy', methods=['GET', 'HEAD', 'OPTIONS'])
def proxy_pdf():
    """
    代理 PDF 文件请求
    使用方式: /pdf-proxy?url=PDF_URL
    """
    # 处理 OPTIONS 请求（CORS 预检）
    if request.method == 'OPTIONS':
        return Response(
            '',
            headers={
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Range',
                'Access-Control-Max-Age': '3600',
            },
            status=200
        )
    
    try:
        # 获取 PDF URL
        pdf_url = request.args.get('url')
        if not pdf_url:
            return jsonify({'error': '缺少 url 参数'}), 400
        
        # URL 解码
        pdf_url = unquote(pdf_url)
        
        # 验证 URL
        parsed = urlparse(pdf_url)
        if not parsed.scheme or not parsed.netloc:
            return jsonify({'error': '无效的 URL'}), 400
        
        # 只允许 http 和 https
        if parsed.scheme not in ['http', 'https']:
            return jsonify({'error': '只支持 http 和 https 协议'}), 400
        
        print(f"[代理] 请求 PDF: {pdf_url}")
        
        # 设置请求头（模拟浏览器）
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/pdf,application/octet-stream,*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://data.eastmoney.com/',
        }
        
        # 如果有 Referer，添加到请求头
        referer = request.args.get('referer')
        if referer:
            headers['Referer'] = unquote(referer)
        
        print(f"[调试] 请求头: {headers}")
        
        # 方法1：优先使用项目中的 PlaywrightHttpClient（更完善的实现）
        if _project_playwright_client:
            try:
                print("[方法] 使用项目中的 PlaywrightHttpClient 下载 PDF（最可靠）")
                
                # 创建临时文件保存 PDF
                import tempfile
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
                temp_path = temp_file.name
                temp_file.close()
                
                # 获取 referer
                referer = request.args.get('referer')
                if referer:
                    referer = unquote(referer)
                else:
                    referer = 'https://data.eastmoney.com/report/'
                
                # 使用项目中的下载方法
                success = _project_playwright_client.download_pdf(pdf_url, temp_path, referer=referer)
                
                if success and Path(temp_path).exists():
                    # 读取 PDF 文件
                    with open(temp_path, 'rb') as f:
                        pdf_content = f.read()
                    
                    # 删除临时文件
                    try:
                        os.unlink(temp_path)
                    except:
                        pass
                    
                    if pdf_content and len(pdf_content) > 100 and pdf_content[:5] == b'%PDF-':
                        print(f"[成功] ✅ 使用 PlaywrightHttpClient 成功获取 PDF，大小: {len(pdf_content)} 字节")
                        return Response(
                            pdf_content,
                            headers={
                                'Content-Type': 'application/pdf',
                                'Content-Disposition': 'inline; filename="report.pdf"',
                                'Access-Control-Allow-Origin': '*',
                                'Access-Control-Allow-Methods': 'GET, OPTIONS, HEAD',
                                'Access-Control-Allow-Headers': 'Content-Type, Range',
                                'Accept-Ranges': 'bytes',
                                'Content-Length': str(len(pdf_content)),
                            },
                            status=200
                        )
                    else:
                        print(f"[警告] 下载的文件不是有效 PDF")
                else:
                    print(f"[警告] PlaywrightHttpClient 下载失败")
            except Exception as e:
                print(f"[警告] PlaywrightHttpClient 方法失败: {e}")
                import traceback
                print(f"[调试] 错误详情: {traceback.format_exc()[:300]}")
        
        # 方法2：使用基础 Playwright（绕过反爬虫）
        page = get_playwright_page()
        if page:
            try:
                print("[方法] 使用 Playwright 获取 PDF（绕过反爬虫）")
                
                # 先访问详情页建立会话（如果有 referer）
                referer = request.args.get('referer')
                if referer:
                    referer = unquote(referer)
                    if not referer.startswith('akshare://') and 'pdf.dfcfw.com' not in referer:
                        print(f"[步骤1] 访问详情页建立会话: {referer[:80]}...")
                        try:
                            page.goto(referer, wait_until='domcontentloaded', timeout=30000)
                            import time
                            time.sleep(2)
                        except Exception as e:
                            print(f"[警告] 访问详情页失败: {e}")
                
                # 访问报告列表页建立基础会话
                print("[步骤2] 访问报告列表页建立基础会话...")
                try:
                    page.goto('https://data.eastmoney.com/report/', wait_until='domcontentloaded', timeout=30000)
                    import time
                    time.sleep(2)
                except:
                    pass
                
                # 使用网络拦截获取 PDF
                print(f"[步骤3] 访问 PDF URL: {pdf_url[:80]}...")
                pdf_content = None
                response_urls = []
                
                def handle_response(response):
                    nonlocal pdf_content
                    response_urls.append(response.url)
                    print(f"[调试] 收到响应: {response.url[:100]}... (状态: {response.status})")
                    
                    # 检查是否是 PDF 响应
                    if 'pdf.dfcfw.com' in response.url or response.url.endswith('.pdf'):
                        try:
                            content_type = response.headers.get('content-type', '')
                            print(f"[调试] Content-Type: {content_type}")
                            
                            body = response.body()
                            print(f"[调试] 响应大小: {len(body)} 字节")
                            print(f"[调试] 内容开头: {body[:20]}")
                            
                            # 检查是否是 PDF
                            if body[:5] == b'%PDF-':
                                pdf_content = body
                                print(f"[成功] ✅ 通过 Playwright 获取到 PDF，大小: {len(pdf_content)} 字节")
                            elif body[:10].startswith(b'<script'):
                                print(f"[警告] ⚠️  收到 JavaScript 反爬虫页面，不是 PDF")
                            else:
                                print(f"[警告] ⚠️  响应不是 PDF，开头: {body[:50]}")
                        except Exception as e:
                            print(f"[错误] 读取响应体失败: {e}")
                            import traceback
                            print(f"[调试] 错误详情: {traceback.format_exc()[:200]}")
                
                page.on('response', handle_response)
                
                # 访问 PDF URL
                try:
                    page.goto(pdf_url, wait_until='networkidle', timeout=30000)
                    import time
                    time.sleep(5)  # 增加等待时间，确保 PDF 加载完成
                    
                    # 检查页面内容
                    page_content = page.content()
                    if '<script' in page_content[:100]:
                        print(f"[警告] 页面内容是 JavaScript，可能被反爬虫拦截")
                    
                except Exception as e:
                    print(f"[错误] 访问 PDF URL 失败: {e}")
                    import traceback
                    print(f"[调试] 错误详情: {traceback.format_exc()[:200]}")
                
                page.remove_listener('response', handle_response)
                
                print(f"[调试] 总共收到 {len(response_urls)} 个响应")
                
                if pdf_content and len(pdf_content) > 100 and pdf_content[:5] == b'%PDF-':
                    print(f"[成功] ✅ 使用 Playwright 成功获取 PDF")
                    # 使用获取到的 PDF 内容
                    return Response(
                        pdf_content,
                        headers={
                            'Content-Type': 'application/pdf',
                            'Content-Disposition': 'inline; filename="report.pdf"',
                            'Access-Control-Allow-Origin': '*',
                            'Access-Control-Allow-Methods': 'GET, OPTIONS, HEAD',
                            'Access-Control-Allow-Headers': 'Content-Type, Range',
                            'Accept-Ranges': 'bytes',
                            'Content-Length': str(len(pdf_content)),
                        },
                        status=200
                    )
                else:
                    print(f"[警告] ⚠️  Playwright 未获取到有效 PDF")
                    if pdf_content:
                        print(f"[调试] 获取到的内容大小: {len(pdf_content)} 字节")
                        print(f"[调试] 内容开头: {pdf_content[:50]}")
                    print(f"[提示] 回退到 requests 方法（可能失败）")
            except Exception as e:
                print(f"[警告] Playwright 方法失败: {e}")
                import traceback
                print(f"[调试] 错误详情: {traceback.format_exc()[:300]}")
        
        # 方法2：使用 requests（如果 Playwright 不可用或失败）
        print("[方法] 使用 requests 获取 PDF")
        response = requests.get(
            pdf_url,
            headers=headers,
            stream=True,
            timeout=TIMEOUT,
            allow_redirects=True
        )
        
        # 检查响应状态
        response.raise_for_status()
        
        # 检查 Content-Type
        content_type = response.headers.get('Content-Type', '')
        print(f"[调试] 响应 Content-Type: {content_type}")
        print(f"[调试] 响应状态码: {response.status_code}")
        
        # 检查内容开头是否为 PDF
        first_chunk = next(response.iter_content(chunk_size=10), b'')
        print(f"[调试] 内容开头 (前10字节): {first_chunk}")
        
        if first_chunk[:5] != b'%PDF-':
            print(f"[错误] 响应不是 PDF 文件，开头是: {first_chunk[:20]}")
            # 尝试读取更多内容查看错误信息
            try:
                error_text = first_chunk.decode('utf-8', errors='ignore')
                if len(error_text) < 100:
                    more_content = next(response.iter_content(chunk_size=100), b'')
                    error_text += more_content.decode('utf-8', errors='ignore')
                print(f"[错误] 响应内容: {error_text[:200]}")
            except:
                pass
            return jsonify({'error': '响应不是 PDF 文件，可能是错误页面或重定向。建议使用 Playwright 绕过反爬虫。'}), 400
        
        # 如果是 PDF，重置响应流
        response = requests.get(pdf_url, headers=headers, stream=True, timeout=TIMEOUT, allow_redirects=True)
        response.raise_for_status()
        
        # 检查文件大小
        content_length = response.headers.get('Content-Length')
        if content_length and int(content_length) > MAX_FILE_SIZE:
            return jsonify({'error': f'文件过大（超过 {MAX_FILE_SIZE / 1024 / 1024}MB）'}), 400
        
        # 设置响应头
        headers_to_send = {
            'Content-Type': 'application/pdf',
            'Content-Disposition': 'inline; filename="report.pdf"',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, OPTIONS, HEAD',
            'Access-Control-Allow-Headers': 'Content-Type, Range',
            'Accept-Ranges': 'bytes',  # 支持范围请求（PDF.js 需要）
        }
        
        # 如果有 Content-Length，传递它
        if content_length:
            headers_to_send['Content-Length'] = content_length
        
        # 检查是否有 Range 请求（PDF.js 查看器会使用）
        range_header = request.headers.get('Range')
        if range_header:
            # 处理范围请求
            try:
                # 解析 Range 头
                range_match = range_header.replace('bytes=', '').split('-')
                start = int(range_match[0]) if range_match[0] else 0
                end = int(range_match[1]) if range_match[1] and range_match[1] else None
                
                # 重新获取完整响应（需要支持范围请求）
                range_headers = headers.copy()
                range_headers['Range'] = f'bytes={start}-{end if end else ""}'
                
                range_response = requests.get(
                    pdf_url,
                    headers=range_headers,
                    stream=True,
                    timeout=TIMEOUT
                )
                
                if range_response.status_code == 206:  # Partial Content
                    headers_to_send['Content-Range'] = range_response.headers.get('Content-Range', '')
                    headers_to_send['Content-Length'] = range_response.headers.get('Content-Length', '')
                    return Response(
                        range_response.iter_content(chunk_size=8192),
                        headers=headers_to_send,
                        status=206
                    )
            except Exception as e:
                print(f"[警告] 处理 Range 请求失败: {e}，返回完整文件")
        
        # 流式返回 PDF
        return Response(
            response.iter_content(chunk_size=8192),
            headers=headers_to_send,
            status=200
        )
        
    except requests.exceptions.Timeout:
        return jsonify({'error': '请求超时'}), 504
    except requests.exceptions.RequestException as e:
        print(f"[错误] 代理请求失败: {str(e)}")
        return jsonify({'error': f'代理请求失败: {str(e)}'}), 500
    except Exception as e:
        print(f"[错误] 未知错误: {str(e)}")
        return jsonify({'error': f'服务器错误: {str(e)}'}), 500


@app.route('/api/reports', methods=['GET'])
def get_reports():
    """
    获取报告数据API（支持缓存）
    支持参数：
    - type: 报告类型，支持：
        - 'all': 获取所有类型
        - 单个类型: 'strategy', 'industry', 'macro', 'stock'
        - 多个类型（逗号分隔）: 'strategy,industry' 或 'strategy,industry,macro'
    - limit: 每种类型获取的数量，默认6
    - force: 是否强制刷新（忽略缓存），默认false
    """
    try:
        import sys
        from pathlib import Path
        # 添加项目根目录到路径
        project_root = Path(__file__).parent
        sys.path.insert(0, str(project_root))
        
        from main import create_crawler_service
        from config import REPORT_TYPES
        from core.cache_manager import get_cache_manager
        
        # 获取参数
        report_type = request.args.get('type', 'all')
        limit = int(request.args.get('limit', 6))
        force = request.args.get('force', 'false').lower() == 'true'
        
        # 验证limit范围
        if limit < 1 or limit > 50:
            return jsonify({'error': 'limit参数必须在1-50之间'}), 400
        
        # 获取缓存管理器
        cache_manager = get_cache_manager()
        
        # 确定要爬取的类型（支持多个类型，逗号分隔）
        if report_type == 'all':
            types_to_crawl = list(REPORT_TYPES.keys())
        else:
            # 支持逗号分隔的多个类型
            type_list = [t.strip() for t in report_type.split(',')]
            types_to_crawl = []
            invalid_types = []
            
            for t in type_list:
                if t in REPORT_TYPES:
                    types_to_crawl.append(t)
                else:
                    invalid_types.append(t)
            
            if invalid_types:
                return jsonify({
                    'error': f'不支持的报告类型: {", ".join(invalid_types)}',
                    'valid_types': list(REPORT_TYPES.keys())
                }), 400
            
            if not types_to_crawl:
                return jsonify({'error': '请至少指定一个有效的报告类型'}), 400
        
        # 收集所有PDF链接（按类型分组，支持缓存）
        pdf_links_by_type = {}
        cache_status = {}  # 记录每个类型是否使用缓存
        
        # 先检查缓存，确定哪些需要爬取
        types_to_fetch = []  # 需要爬取的类型
        for report_type_key in types_to_crawl:
            if force:
                # 强制刷新，不使用缓存
                types_to_fetch.append(report_type_key)
                cache_status[report_type_key] = 'force_refresh'
            else:
                # 检查缓存
                cached_data = cache_manager.get_cache(report_type_key, limit)
                if cached_data:
                    # 使用缓存数据，但需要确保有元信息（旧缓存可能没有）
                    from core.keyword_extractor import get_keyword_extractor
                    from datetime import datetime
                    keyword_extractor = get_keyword_extractor()
                    
                    # 为缓存数据补充元信息（如果缺失）
                    # 注意：缓存数据没有detail_html，只能从标题提取
                    for item in cached_data:
                        if 'metadata' not in item or not item.get('metadata'):
                            metadata = keyword_extractor.extract_metadata(
                                item['report_info']['title'],
                                item['report_info']['date'],
                                item['report_info'].get('detail_url'),
                                None  # 缓存数据没有detail_html
                            )
                            metadata['extracted_at'] = datetime.now().isoformat()
                            item['metadata'] = metadata
                    
                    pdf_links_by_type[report_type_key] = cached_data
                    cache_status[report_type_key] = 'cached'
                    print(f"[API] {REPORT_TYPES[report_type_key]['name']}: 使用缓存，{len(cached_data)} 个PDF链接")
                else:
                    # 缓存不存在或过期，需要爬取
                    types_to_fetch.append(report_type_key)
                    cache_status[report_type_key] = 'fetching'
        
        # 如果有需要爬取的类型，执行爬取
        if types_to_fetch:
            print(f"[API] 需要爬取的类型: {', '.join([REPORT_TYPES[t]['name'] for t in types_to_fetch])}")
            crawler = create_crawler_service(
                use_akshare=False,  # 使用Playwright爬取
                use_tushare=False,
                headless=True
            )
            
            for report_type_key in types_to_fetch:
                try:
                    type_name = REPORT_TYPES[report_type_key]['name']
                    print(f"[API] 开始收集 {type_name} 报告PDF链接...")
                    
                    # 收集PDF链接（不下载）
                    pdf_infos = crawler.crawl_reports(report_type_key, limit=limit)
                    
                    # 导入关键词提取器
                    from core.keyword_extractor import get_keyword_extractor
                    from datetime import datetime
                    keyword_extractor = get_keyword_extractor()
                    
                    # 转换为前端需要的格式，添加元信息
                    formatted_data = []
                    for pdf_info in pdf_infos:
                        # 提取关键词和元信息（使用详情页HTML）
                        metadata = keyword_extractor.extract_metadata(
                            pdf_info.report_info.title,
                            pdf_info.report_info.date,
                            pdf_info.report_info.detail_url,
                            pdf_info.detail_html  # 传入详情页HTML
                        )
                        metadata['extracted_at'] = datetime.now().isoformat()
                        
                        formatted_data.append({
                            'url': pdf_info.url,
                            'filename': pdf_info.filename,
                            'report_info': {
                                'title': pdf_info.report_info.title,
                                'date': pdf_info.report_info.date,
                                'detail_url': pdf_info.report_info.detail_url,
                                'report_type': pdf_info.report_info.report_type
                            },
                            'metadata': metadata
                        })
                    
                    pdf_links_by_type[report_type_key] = formatted_data
                    
                    # 保存到缓存
                    cache_manager.set_cache(report_type_key, limit, formatted_data)
                    cache_status[report_type_key] = 'fetched'
                    
                    print(f"[API] {type_name}: 收集到 {len(formatted_data)} 个PDF链接并已缓存")
                except Exception as e:
                    print(f"[API] 收集 {report_type_key} 报告时发生错误: {str(e)}")
                    pdf_links_by_type[report_type_key] = []
                    cache_status[report_type_key] = 'error'
                    continue
            
            # 关闭HTTP客户端
            if crawler.http_client:
                crawler.http_client.close()
        else:
            print("[API] 所有类型都使用缓存，无需爬取")
        
        # 合并所有报告数据
        all_reports = []
        for report_type_key, pdf_infos in pdf_links_by_type.items():
            all_reports.extend(pdf_infos)
        
        return jsonify({
            'success': True,
            'data': all_reports,
            'count': len(all_reports),
            'by_type': {k: len(v) for k, v in pdf_links_by_type.items()},
            'requested_types': types_to_crawl,
            'limit': limit,
            'cache_status': cache_status,
            'force_refresh': force
        }), 200
        
    except Exception as e:
        print(f"[API] 获取报告数据失败: {str(e)}")
        import traceback
        print(f"[API] 错误详情: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': f'获取报告数据失败: {str(e)}'
        }), 500


@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({'status': 'ok', 'service': 'PDF Proxy'}), 200

@app.route('/api/cache/status', methods=['GET'])
def get_cache_status():
    """获取缓存状态"""
    try:
        import sys
        from pathlib import Path
        project_root = Path(__file__).parent
        sys.path.insert(0, str(project_root))
        
        from core.cache_manager import get_cache_manager
        
        cache_manager = get_cache_manager()
        status = cache_manager.get_cache_status()
        
        return jsonify({
            'success': True,
            'status': status
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/cache/clear', methods=['POST'])
def clear_cache():
    """清除缓存"""
    try:
        import sys
        from pathlib import Path
        project_root = Path(__file__).parent
        sys.path.insert(0, str(project_root))
        
        from core.cache_manager import get_cache_manager
        
        cache_manager = get_cache_manager()
        report_type = request.json.get('type') if request.json else None
        limit = request.json.get('limit') if request.json else None
        
        cache_manager.clear_cache(report_type, limit)
        
        return jsonify({
            'success': True,
            'message': '缓存已清除'
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/', methods=['GET'])
def index():
    """根路径"""
    return jsonify({
        'service': 'PDF Proxy Server',
        'endpoints': {
            'health': '/health',
            'proxy': '/pdf-proxy?url=PDF_URL',
            'reports': '/api/reports?type=all&limit=6&force=false',
            'cache_status': '/api/cache/status',
            'clear_cache': '/api/cache/clear (POST)'
        }
    }), 200


if __name__ == '__main__':
    print("=" * 60)
    print("PDF 代理服务器")
    print("=" * 60)
    print(f"服务地址: http://localhost:{PROXY_PORT}")
    print(f"代理端点: http://localhost:{PROXY_PORT}/pdf-proxy?url=PDF_URL")
    print("=" * 60)
    
    # 初始化 Playwright（在服务器启动时）
    print("\n[初始化] 检查 Playwright 支持...")
    playwright_ready = init_playwright()
    
    if playwright_ready:
        print("[状态] ✅ 已启用 Playwright，可以绕过反爬虫")
    else:
        print("[状态] ⚠️  未启用 Playwright，可能无法绕过反爬虫")
        print("[建议] 安装 Playwright 以获得更好的兼容性")
    
    print("=" * 60)
    print("按 Ctrl+C 停止服务器")
    print("=" * 60)
    print()
    
    try:
        app.run(host='0.0.0.0', port=PROXY_PORT, debug=False)
    finally:
        # 清理 Playwright 资源
        if _browser:
            try:
                _browser.close()
                print("[清理] Playwright 浏览器已关闭")
            except:
                pass
        if _playwright:
            try:
                _playwright.stop()
                print("[清理] Playwright 已停止")
            except:
                pass

