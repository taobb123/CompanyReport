"""
接口定义模块
遵循接口编程原则，定义系统的核心抽象接口
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class ReportInfo:
    """报告信息数据类"""
    title: str
    date: str
    detail_url: str
    report_type: str


@dataclass
class PdfInfo:
    """PDF信息数据类"""
    url: str
    filename: str
    report_info: ReportInfo
    detail_html: Optional[str] = None  # 详情页HTML内容（用于提取关键词）


class IReportParser(ABC):
    """报告解析器接口"""
    
    @abstractmethod
    def parse_report_list(self, html_content: str, limit: int = 6) -> List[ReportInfo]:
        """
        解析报告列表页，提取报告信息
        
        Args:
            html_content: HTML内容
            limit: 提取数量限制
            
        Returns:
            报告信息列表
        """
        pass
    
    @abstractmethod
    def parse_pdf_link(self, html_content: str) -> Optional[str]:
        """
        解析报告详情页，提取PDF链接
        
        Args:
            html_content: HTML内容
            
        Returns:
            PDF链接，如果不存在则返回None
        """
        pass


class IPdfDownloader(ABC):
    """PDF下载器接口"""
    
    @abstractmethod
    def download(self, pdf_url: str, save_path: str, referer: str = None) -> bool:
        """
        下载PDF文件
        
        Args:
            pdf_url: PDF链接
            save_path: 保存路径
            referer: 来源页URL（用于防盗链验证，可选）
            
        Returns:
            是否下载成功
        """
        pass


class IStorage(ABC):
    """存储接口"""
    
    @abstractmethod
    def ensure_directory(self, report_type: str) -> str:
        """
        确保目录存在，返回目录路径
        
        Args:
            report_type: 报告类型
            
        Returns:
            目录路径
        """
        pass
    
    @abstractmethod
    def generate_filename(self, report_info: ReportInfo) -> str:
        """
        生成文件名
        
        Args:
            report_info: 报告信息
            
        Returns:
            文件名（不含路径）
        """
        pass


class IHttpClient(ABC):
    """HTTP客户端接口"""
    
    @abstractmethod
    def get(self, url: str, **kwargs) -> Optional[str]:
        """
        发送GET请求
        
        Args:
            url: 请求URL
            **kwargs: 其他请求参数
            
        Returns:
            响应内容，失败返回None
        """
        pass


class IReportTypeHandler(ABC):
    """报告类型处理器接口（策略模式）"""
    
    @abstractmethod
    def get_report_type_name(self) -> str:
        """获取报告类型名称"""
        pass
    
    @abstractmethod
    def get_list_url(self) -> str:
        """获取列表页URL"""
        pass
    
    @abstractmethod
    def parse_list_page(self, html_content: str, limit: int) -> List[ReportInfo]:
        """解析列表页"""
        pass


class IReportCrawler(ABC):
    """报告爬虫接口"""
    
    @abstractmethod
    def crawl_reports(self, report_type: str, limit: int = 6) -> List[PdfInfo]:
        """
        爬取指定类型的报告
        
        Args:
            report_type: 报告类型
            limit: 爬取数量限制
            
        Returns:
            PDF信息列表
        """
        pass

