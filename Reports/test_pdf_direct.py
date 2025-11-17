"""
直接测试 PDF URL 是否可访问
"""

import requests
import sys

def test_pdf_url(pdf_url):
    """测试 PDF URL 是否可访问"""
    print("=" * 60)
    print("测试 PDF URL")
    print("=" * 60)
    print(f"URL: {pdf_url}")
    print()
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/pdf,*/*',
            'Referer': 'https://data.eastmoney.com/',
        }
        
        print("发送请求...")
        response = requests.get(pdf_url, headers=headers, stream=True, timeout=30, allow_redirects=True)
        
        print(f"状态码: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        print(f"Content-Length: {response.headers.get('Content-Length', 'N/A')}")
        print()
        
        # 读取前几个字节
        first_chunk = next(response.iter_content(chunk_size=10), b'')
        print(f"内容开头 (前10字节): {first_chunk}")
        print(f"是否为 PDF: {first_chunk[:5] == b'%PDF-'}")
        
        if first_chunk[:5] == b'%PDF-':
            print("✅ PDF 文件可以正常访问")
            return True
        else:
            print("❌ 响应不是 PDF 文件")
            # 尝试读取错误信息
            try:
                error_text = first_chunk.decode('utf-8', errors='ignore')
                print(f"响应内容: {error_text[:200]}")
            except:
                pass
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False
    finally:
        print("=" * 60)

if __name__ == '__main__':
    # 测试一个示例 PDF URL
    test_url = "https://pdf.dfcfw.com/pdf/H3_AP202510281770514161_1.pdf"
    
    if len(sys.argv) > 1:
        test_url = sys.argv[1]
    
    test_pdf_url(test_url)

