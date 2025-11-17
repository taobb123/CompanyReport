"""
Tushare报告处理器
使用Tushare API获取研究报告
"""

from typing import List
from interfaces import IReportTypeHandler, ReportInfo
from infrastructure.tushare_client import TushareDataClient


class TushareReportHandler(IReportTypeHandler):
    """
    Tushare报告处理器
    使用Tushare API获取数据，不依赖网页爬取
    """
    
    def __init__(self, report_type: str, type_name: str, token: str = None):
        """
        初始化处理器
        
        Args:
            report_type: 报告类型（strategy/industry/macro/stock）
            type_name: 报告类型中文名称
            token: Tushare API Token（可选）
        """
        self.report_type = report_type
        self.type_name = type_name
        self.tushare_client = TushareDataClient(token=token)
    
    def get_report_type_name(self) -> str:
        """获取报告类型名称"""
        return self.type_name
    
    def get_list_url(self) -> str:
        """获取列表页URL（Tushare不需要URL）"""
        return f"tushare://{self.report_type}"
    
    def parse_list_page(self, html_content: str, limit: int) -> List[ReportInfo]:
        """
        解析列表页（Tushare直接返回数据，不需要解析HTML）
        
        Args:
            html_content: HTML内容（Tushare不使用）
            limit: 限制数量
            
        Returns:
            报告信息列表
        """
        # 直接使用Tushare API获取数据
        return self.tushare_client.get_reports(self.report_type, limit)

