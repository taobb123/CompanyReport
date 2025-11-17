"""
HTTP客户端实现
使用代理模式封装requests库
"""

import requests
from typing import Optional
from interfaces import IHttpClient


class HttpProxy(IHttpClient):
    """
    HTTP请求代理
    使用代理模式封装HTTP请求，提供统一的接口
    """
    
    def __init__(self, timeout: int = 30, headers: Optional[dict] = None):
        """
        初始化HTTP代理
        
        Args:
            timeout: 请求超时时间（秒）
            headers: 默认请求头
        """
        self.timeout = timeout
        self.default_headers = headers or {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.default_headers)
    
    def get(self, url: str, **kwargs) -> Optional[str]:
        """
        发送GET请求
        
        Args:
            url: 请求URL
            **kwargs: 其他请求参数（headers, timeout等）
            
        Returns:
            响应内容，失败返回None
        """
        try:
            # 合并headers
            headers = kwargs.pop('headers', {})
            merged_headers = {**self.default_headers, **headers}
            
            # 获取timeout
            timeout = kwargs.pop('timeout', self.timeout)
            
            response = self.session.get(
                url,
                headers=merged_headers,
                timeout=timeout,
                **kwargs
            )
            response.raise_for_status()
            response.encoding = response.apparent_encoding or 'utf-8'
            return response.text
        except Exception as e:
            print(f"HTTP请求失败 {url}: {str(e)}")
            return None
    
    def close(self):
        """关闭session"""
        self.session.close()

