"""
PDF 静态文件服务器
先下载 PDF 到本地，然后提供静态文件服务
这样可以避免实时代理的不确定性
"""

from flask import Flask, send_file, jsonify, request
from flask_cors import CORS
import os
import hashlib
from pathlib import Path
from urllib.parse import unquote, urlparse
import sys

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from infrastructure.playwright_client import PlaywrightHttpClient
    from infrastructure.storage import FileStorage
    from core.downloader import PdfDownloader
    PLAYWRIGHT_AVAILABLE = True
except ImportError as e:
    PLAYWRIGHT_AVAILABLE = False
    print(f"[警告] 无法导入项目模块: {e}")

app = Flask(__name__)
CORS(app)

# 配置
SERVER_PORT = 5001
PDF_CACHE_DIR = Path(__file__).parent / 'pdf_cache'
PDF_CACHE_DIR.mkdir(exist_ok=True)

# 全局客户端（延迟初始化）
_http_client = None
_downloader = None

def get_downloader():
    """获取下载器实例"""
    global _http_client, _downloader
    
    if _downloader is None and PLAYWRIGHT_AVAILABLE:
        try:
            print("[初始化] 创建 PlaywrightHttpClient...")
            _http_client = PlaywrightHttpClient(timeout=60, headless=True)
            storage = FileStorage(base_path=str(PDF_CACHE_DIR))
            _downloader = PdfDownloader(http_client=_http_client)
            print("[初始化] ✅ 下载器已创建")
        except Exception as e:
            print(f"[错误] 创建下载器失败: {e}")
    
    return _downloader

def get_pdf_filename(url):
    """根据 URL 生成文件名"""
    # 使用 URL 的哈希值作为文件名
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
        
        # 下载 PDF
        print(f"[下载] 开始下载 PDF: {pdf_url[:80]}...")
        downloader = get_downloader()
        
        if not downloader:
            return jsonify({'error': '下载器未初始化，请检查 Playwright 是否安装'}), 500
        
        # 使用项目的下载逻辑
        success = False
        if hasattr(downloader, 'playwright_downloader') and downloader.playwright_downloader:
            print("[方法] 使用 PlaywrightHttpClient 下载")
            success = downloader.playwright_downloader.download_pdf(
                pdf_url, 
                str(cached_path), 
                referer=referer
            )
        else:
            print("[方法] 使用基础下载器")
            success = downloader.download(pdf_url, str(cached_path), referer=referer)
        
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
            return jsonify({'error': 'PDF 下载失败'}), 500
            
    except Exception as e:
        print(f"[错误] 下载失败: {e}")
        import traceback
        print(f"[调试] 错误详情: {traceback.format_exc()[:300]}")
        return jsonify({'error': f'服务器错误: {str(e)}'}), 500

@app.route('/health')
def health():
    """健康检查"""
    return jsonify({
        'status': 'ok',
        'service': 'PDF Static Server',
        'cache_dir': str(PDF_CACHE_DIR),
        'cached_files': len(list(PDF_CACHE_DIR.glob('*.pdf')))
    })

@app.route('/')
def index():
    """根路径"""
    return jsonify({
        'service': 'PDF Static Server',
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
    print("PDF 静态文件服务器")
    print("=" * 60)
    print(f"服务地址: http://localhost:{SERVER_PORT}")
    print(f"缓存目录: {PDF_CACHE_DIR}")
    print("=" * 60)
    
    # 初始化下载器
    print("\n[初始化] 初始化下载器...")
    get_downloader()
    
    print("=" * 60)
    print("按 Ctrl+C 停止服务器")
    print("=" * 60)
    print()
    
    try:
        app.run(host='0.0.0.0', port=SERVER_PORT, debug=False)
    finally:
        # 清理资源
        if _http_client:
            try:
                _http_client.close()
                print("[清理] HTTP 客户端已关闭")
            except:
                pass

