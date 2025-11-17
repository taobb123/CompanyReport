"""
API客户端实现
尝试从API接口直接获取报告数据（如果存在）
"""

import requests
import json
from typing import Optional, List, Dict
from interfaces import IHttpClient, ReportInfo


class ApiHttpClient(IHttpClient):
    """
    API HTTP客户端
    尝试查找并调用API接口获取报告数据
    """
    
    def __init__(self, base_http_client: IHttpClient):
        """
        初始化API客户端
        
        Args:
            base_http_client: 基础HTTP客户端（用于API请求）
        """
        self.base_client = base_http_client
        self.session = getattr(base_http_client, 'session', None) or requests.Session()
    
    def get(self, url: str, **kwargs) -> Optional[str]:
        """
        发送GET请求
        
        Args:
            url: 请求URL
            **kwargs: 其他请求参数
            
        Returns:
            响应内容，失败返回None
        """
        return self.base_client.get(url, **kwargs)
    
    def get_reports_from_api(self, report_type: str, limit: int = 6) -> Optional[List[Dict]]:
        """
        尝试从API接口获取报告数据
        
        Args:
            report_type: 报告类型
            limit: 获取数量限制
            
        Returns:
            报告数据列表，如果API不存在则返回None
        """
        # 东方财富可能的API接口模式
        api_patterns = [
            f"https://datacenter-web.eastmoney.com/api/data/v1/get?sortColumns=NOTICE_DATE&sortTypes=-1&pageSize={limit}&pageNumber=1&reportName=RPT_RESEARCHREPORT_LIST&columns=ALL&source=WEB&client=WEB&filter=(REPORT_TYPE='{report_type}')",
            f"https://data.eastmoney.com/report/{report_type}.jshtml?pageSize={limit}",
        ]
        
        # 根据报告类型构建API URL
        type_mapping = {
            'strategy': 'strategyreport',
            'industry': 'industry',
            'macro': 'macresearch',
            'profit': 'profitforecast'
        }
        
        api_type = type_mapping.get(report_type, report_type)
        
        # 尝试常见的API接口
        api_urls = [
            f"https://datacenter-web.eastmoney.com/api/data/v1/get",
            f"https://data.eastmoney.com/report/api/{api_type}",
        ]
        
        for api_url in api_urls:
            try:
                # 尝试GET请求
                response = self.get(api_url)
                if response:
                    try:
                        data = json.loads(response)
                        if data and isinstance(data, dict):
                            print(f"[调试] 找到API接口: {api_url}")
                            return data
                    except:
                        pass
            except:
                continue
        
        return None

