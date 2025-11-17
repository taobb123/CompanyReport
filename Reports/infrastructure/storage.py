"""
文件存储实现
"""

import os
from pathlib import Path
from typing import Optional
from interfaces import IStorage, ReportInfo


class FileStorage(IStorage):
    """
    文件存储实现
    使用组合方式组织存储逻辑
    """
    
    def __init__(self, base_path: str = r"D:\Books\证券", type_mapping: dict = None):
        """
        初始化存储
        
        Args:
            base_path: 基础存储路径
            type_mapping: 报告类型映射字典（可选，用于扩展）
        """
        self.base_path = Path(base_path)
        self._type_mapping = type_mapping or {
            'strategy': '策略',
            'industry': '行业',
            'macro': '宏观',
            'profit': '盈利预测'
        }
    
    def ensure_directory(self, report_type: str) -> str:
        """
        确保目录存在，返回目录路径
        
        Args:
            report_type: 报告类型（strategy/industry/macro/profit）
            
        Returns:
            目录路径
        """
        # 映射报告类型到中文名称
        type_name = self._type_mapping.get(report_type, report_type)
        dir_path = self.base_path / type_name
        
        # 创建目录（如果不存在）
        dir_path.mkdir(parents=True, exist_ok=True)
        
        return str(dir_path)
    
    def generate_filename(self, report_info: ReportInfo) -> str:
        """
        生成文件名：报告标题 + 日期
        
        Args:
            report_info: 报告信息
            
        Returns:
            文件名（不含路径，包含扩展名）
        """
        # 清理文件名中的非法字符
        title = self._sanitize_filename(report_info.title)
        date = report_info.date.replace('-', '').replace('/', '')
        
        filename = f"{title}_{date}.pdf"
        
        # 限制文件名长度（Windows路径限制）
        if len(filename) > 200:
            title_part = title[:200 - len(date) - 6]  # 减去日期和扩展名长度
            filename = f"{title_part}_{date}.pdf"
        
        return filename
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        清理文件名中的非法字符
        
        Args:
            filename: 原始文件名
            
        Returns:
            清理后的文件名
        """
        # Windows文件名非法字符
        illegal_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        for char in illegal_chars:
            filename = filename.replace(char, '_')
        
        # 移除多余空格
        filename = ' '.join(filename.split())
        
        return filename.strip()

