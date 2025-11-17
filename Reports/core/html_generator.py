"""
HTML生成器
将收集到的PDF链接按类型分类展示在HTML页面中
"""

from typing import List, Dict
from interfaces import PdfInfo
from datetime import datetime
import config


class HtmlReportGenerator:
    """HTML报告生成器"""
    
    def __init__(self, output_path: str = None):
        """
        初始化HTML生成器
        
        Args:
            output_path: 输出HTML文件路径，默认为存储目录下的reports.html
        """
        if output_path is None:
            import os
            output_path = os.path.join(config.STORAGE_BASE_PATH, "reports.html")
        self.output_path = output_path
    
    def generate(self, pdf_links_by_type: Dict[str, List[PdfInfo]]):
        """
        生成HTML页面
        
        Args:
            pdf_links_by_type: 按报告类型分组的PDF链接字典
                {
                    'strategy': [PdfInfo, ...],
                    'industry': [PdfInfo, ...],
                    ...
                }
        """
        html_content = self._generate_html(pdf_links_by_type)
        
        # 确保输出目录存在
        import os
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        
        # 写入文件
        with open(self.output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"\n[成功] HTML报告已生成: {self.output_path}")
        print(f"[提示] 请在浏览器中打开查看")
    
    def _generate_html(self, pdf_links_by_type: Dict[str, List[PdfInfo]]) -> str:
        """生成HTML内容"""
        
        # 统计信息
        total_reports = sum(len(links) for links in pdf_links_by_type.values())
        type_names = {
            'strategy': '策略报告',
            'industry': '行业报告',
            'macro': '宏观报告',
            'profit': '盈利预测'
        }
        
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>证券研究报告链接汇总</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .header .stats {{
            font-size: 1.1em;
            opacity: 0.9;
            margin-top: 10px;
        }}
        
        .content {{
            padding: 30px;
        }}
        
        .section {{
            margin-bottom: 40px;
        }}
        
        .section-title {{
            font-size: 1.8em;
            color: #333;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
            display: flex;
            align-items: center;
        }}
        
        .section-title::before {{
            content: "📊";
            margin-right: 10px;
            font-size: 1.2em;
        }}
        
        .report-list {{
            display: grid;
            gap: 15px;
        }}
        
        .report-item {{
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 20px;
            border-radius: 8px;
            transition: all 0.3s ease;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        
        .report-item:hover {{
            transform: translateX(5px);
            box-shadow: 0 4px 10px rgba(0,0,0,0.15);
            background: #fff;
        }}
        
        .report-title {{
            font-size: 1.2em;
            font-weight: bold;
            color: #333;
            margin-bottom: 10px;
        }}
        
        .report-meta {{
            display: flex;
            gap: 20px;
            margin-bottom: 12px;
            font-size: 0.9em;
            color: #666;
        }}
        
        .report-meta span {{
            display: flex;
            align-items: center;
        }}
        
        .report-meta span::before {{
            margin-right: 5px;
        }}
        
        .report-date::before {{
            content: "📅";
        }}
        
        .report-type::before {{
            content: "🏷️";
        }}
        
        .report-link {{
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 10px 20px;
            text-decoration: none;
            border-radius: 5px;
            font-weight: bold;
            transition: all 0.3s ease;
            margin-top: 10px;
        }}
        
        .report-link:hover {{
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }}
        
        .empty-section {{
            text-align: center;
            padding: 40px;
            color: #999;
            font-size: 1.1em;
        }}
        
        .footer {{
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 0.9em;
            border-top: 1px solid #eee;
        }}
        
        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 1.8em;
            }}
            
            .content {{
                padding: 20px;
            }}
            
            .report-meta {{
                flex-direction: column;
                gap: 5px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📈 证券研究报告链接汇总</h1>
            <div class="stats">
                生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 
                总计: {total_reports} 篇报告
            </div>
        </div>
        
        <div class="content">
"""
        
        # 生成每个类型的报告列表
        for report_type, pdf_infos in pdf_links_by_type.items():
            type_name = type_names.get(report_type, report_type)
            
            html += f"""
            <div class="section">
                <div class="section-title">{type_name} ({len(pdf_infos)} 篇)</div>
"""
            
            if pdf_infos:
                html += '<div class="report-list">\n'
                for pdf_info in pdf_infos:
                    report = pdf_info.report_info
                    date_display = report.date if report.date else "未知日期"
                    html += f"""
                    <div class="report-item">
                        <div class="report-title">{self._escape_html(report.title)}</div>
                        <div class="report-meta">
                            <span class="report-date">{date_display}</span>
                            <span class="report-type">{type_name}</span>
                        </div>
                        <a href="{self._escape_html(pdf_info.url)}" target="_blank" class="report-link">
                            📄 查看PDF报告
                        </a>
                    </div>
"""
                html += '</div>\n'
            else:
                html += '<div class="empty-section">暂无报告</div>\n'
            
            html += '</div>\n'
        
        html += """
        </div>
        
        <div class="footer">
            <p>本页面由证券报告爬虫系统自动生成</p>
            <p>数据来源: AKShare API</p>
        </div>
    </div>
</body>
</html>
"""
        
        return html
    
    def _escape_html(self, text: str) -> str:
        """转义HTML特殊字符"""
        if not text:
            return ""
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))


