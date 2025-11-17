"""
测试PDF下载脚本
用于调试PDF下载问题
"""

from infrastructure.playwright_client import PlaywrightHttpClient
from pathlib import Path

def test_pdf_download():
    """测试单个PDF下载"""
    # 使用非无头模式，可以看到浏览器行为
    client = PlaywrightHttpClient(timeout=60, headless=False)
    
    # 测试PDF URL（从AKShare获取的链接）
    pdf_url = "https://pdf.dfcfw.com/pdf/H3_AP202503181644529525_1.pdf"
    save_path = "test_download.pdf"
    
    print("=" * 60)
    print("测试PDF下载")
    print("=" * 60)
    print(f"PDF URL: {pdf_url}")
    print(f"保存路径: {save_path}")
    print("=" * 60)
    
    # 测试下载
    success = client.download_pdf(
        pdf_url=pdf_url,
        save_path=save_path,
        referer='https://data.eastmoney.com/report/'
    )
    
    if success:
        print("\n" + "=" * 60)
        print("✓ 下载成功！")
        print("=" * 60)
        
        # 验证文件
        if Path(save_path).exists():
            file_size = Path(save_path).stat().st_size
            print(f"文件大小: {file_size} 字节 ({file_size/1024:.2f} KB)")
            
            with open(save_path, 'rb') as f:
                header = f.read(5)
                if header == b'%PDF-':
                    print("✓ PDF文件有效")
                else:
                    print("✗ PDF文件无效")
                    print(f"文件开头: {header}")
    else:
        print("\n" + "=" * 60)
        print("✗ 下载失败")
        print("=" * 60)
        print("\n请观察浏览器窗口，查看：")
        print("1. 是否被重定向到验证页面")
        print("2. 是否需要登录")
        print("3. 网络请求的详细信息（F12 -> Network）")
    
    # 保持浏览器打开一段时间，方便观察
    import time
    print("\n浏览器将保持打开10秒，请观察...")
    time.sleep(10)
    
    client.close()

if __name__ == "__main__":
    test_pdf_download()

