"""
报告类型处理器实现
使用策略模式处理不同类型的报告
"""

from typing import List
from interfaces import IReportTypeHandler, IReportParser, ReportInfo


class BaseReportHandler(IReportTypeHandler):
    """
    基础报告处理器（模板方法模式）
    定义通用的处理流程，子类实现具体细节
    """
    
    def __init__(self, parser: IReportParser, report_type: str, list_url: str):
        """
        初始化处理器
        
        Args:
            parser: 解析器（通过组合注入）
            report_type: 报告类型
            list_url: 列表页URL
        """
        self.parser = parser
        self.report_type = report_type
        self.list_url = list_url
    
    def get_report_type_name(self) -> str:
        """获取报告类型名称"""
        return self.report_type
    
    def get_list_url(self) -> str:
        """获取列表页URL"""
        return self.list_url
    
    def parse_list_page(self, html_content: str, limit: int) -> List[ReportInfo]:
        """
        解析列表页（模板方法）
        委托给解析器处理
        """
        reports = self.parser.parse_report_list(html_content, limit)
        
        # 设置报告类型
        for report in reports:
            report.report_type = self.report_type
        
        return reports


class StrategyReportHandler(BaseReportHandler):
    """策略报告处理器"""
    
    def __init__(self, parser: IReportParser):
        super().__init__(
            parser=parser,
            report_type='strategy',
            list_url='https://data.eastmoney.com/report/strategyreport.jshtml'
        )


class IndustryReportHandler(BaseReportHandler):
    """行业研报处理器"""
    
    def __init__(self, parser: IReportParser):
        super().__init__(
            parser=parser,
            report_type='industry',
            list_url='https://data.eastmoney.com/report/industry.jshtml'
        )


class MacroReportHandler(BaseReportHandler):
    """宏观研报处理器"""
    
    def __init__(self, parser: IReportParser):
        super().__init__(
            parser=parser,
            report_type='macro',
            list_url='https://data.eastmoney.com/report/macresearch.jshtml'
        )


class StockReportHandler(BaseReportHandler):
    """个股研报处理器"""
    
    def __init__(self, parser: IReportParser):
        super().__init__(
            parser=parser,
            report_type='stock',
            list_url='https://data.eastmoney.com/report/stock.jshtml'
        )
