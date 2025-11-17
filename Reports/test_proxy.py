"""
快速测试代理服务器
"""

import requests
import sys

def test_proxy():
    base_url = 'http://localhost:5000'
    
    print("=" * 60)
    print("测试代理服务器")
    print("=" * 60)
    
    # 测试健康检查
    print("\n1. 测试 /health 端点...")
    try:
        response = requests.get(f'{base_url}/health', timeout=5)
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.json()}")
        if response.status_code == 200:
            print("   ✅ 健康检查通过")
        else:
            print("   ❌ 健康检查失败")
    except requests.exceptions.ConnectionError:
        print("   ❌ 无法连接到服务器，请确保代理服务器正在运行")
        print("   启动命令: python backend_proxy.py")
        return False
    except Exception as e:
        print(f"   ❌ 错误: {e}")
        return False
    
    # 测试根路径
    print("\n2. 测试根路径 / ...")
    try:
        response = requests.get(f'{base_url}/', timeout=5)
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.json()}")
    except Exception as e:
        print(f"   ⚠️  警告: {e}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
    
    return True

if __name__ == '__main__':
    test_proxy()

