"""
调试工具
用于保存HTML内容以便检查页面结构
"""

import os
from pathlib import Path


def save_html_for_debug(html_content: str, filename: str = "debug.html"):
    """
    保存HTML内容到文件以便调试
    
    Args:
        html_content: HTML内容
        filename: 文件名
    """
    debug_dir = Path("debug")
    debug_dir.mkdir(exist_ok=True)
    
    file_path = debug_dir / filename
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"调试HTML已保存到: {file_path}")

