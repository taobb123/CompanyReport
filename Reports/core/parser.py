"""
HTML解析器实现
使用BeautifulSoup解析HTML内容
"""

from bs4 import BeautifulSoup
from typing import List, Optional
from interfaces import IReportParser, ReportInfo


class HtmlReportParser(IReportParser):
    """
    HTML报告解析器
    使用委托模式，将解析逻辑委托给专门的解析方法
    """
    
    def __init__(self):
        """初始化解析器"""
        pass
    
    def parse_report_list(self, html_content: str, limit: int = 6) -> List[ReportInfo]:
        """
        解析报告列表页，提取报告信息
        
        Args:
            html_content: HTML内容
            limit: 提取数量限制
            
        Returns:
            报告信息列表
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        reports = []
        
        # 直接使用解析方法（假设内容已经通过Selenium动态加载完成）
        report_items = self._extract_report_items(soup, limit)
        
        for item in report_items:
            report_info = self._parse_report_item(item)
            if report_info:
                reports.append(report_info)
        
        return reports[:limit]
    
    def parse_pdf_link(self, html_content: str) -> Optional[str]:
        """
        解析报告详情页，提取PDF链接
        
        Args:
            html_content: HTML内容
            
        Returns:
            PDF链接，如果不存在则返回None
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 方法1: 查找class='pdf-link'的链接
        pdf_link = soup.find('a', class_='pdf-link')
        if pdf_link and pdf_link.get('href'):
            href = pdf_link.get('href')
            print(f"[调试] 找到PDF链接（方法1）: {href[:100]}")
            return href
        
        # 方法2: 查找包含'pdf'关键词的链接
        all_links = soup.find_all('a', href=True)
        for link in all_links:
            href = link.get('href', '')
            link_text = link.get_text(strip=True)
            # 检查是否是PDF链接
            if ('pdf' in href.lower() or 'pdf' in link_text.lower()) and 'pdf.dfcfw.com' in href:
                print(f"[调试] 找到PDF链接（方法2）: {href[:100]}")
                return href
        
        # 方法3: 查找包含'查看PDF'或'PDF原文'文本的链接
        for link in all_links:
            link_text = link.get_text(strip=True)
            if 'pdf' in link_text.lower() or '查看' in link_text:
                href = link.get('href', '')
                if href and ('pdf' in href.lower() or 'dfcfw.com' in href):
                    print(f"[调试] 找到PDF链接（方法3）: {href[:100]}")
                    return href
        
        # 方法4: 查找所有包含pdf.dfcfw.com的链接
        for link in all_links:
            href = link.get('href', '')
            if 'pdf.dfcfw.com' in href:
                print(f"[调试] 找到PDF链接（方法4）: {href[:100]}")
                return href
        
        print(f"[警告] 未找到PDF链接，页面中可能没有PDF原文")
        # 输出一些调试信息
        print(f"[调试] 页面中找到 {len(all_links)} 个链接")
        print(f"[调试] 前5个链接:")
        for i, link in enumerate(all_links[:5]):
            href = link.get('href', '')
            text = link.get_text(strip=True)
            print(f"  {i+1}. '{text[:30]}...' -> {href[:80]}")
        
        return None
    
    def _extract_report_items(self, soup: BeautifulSoup, limit: int) -> List:
        """
        提取报告列表项（委托方法）
        
        根据实际网页结构：报告在表格的"报告名称"列中
        使用CSS选择器精确提取
        
        Args:
            soup: BeautifulSoup对象
            limit: 限制数量
            
        Returns:
            报告项列表
        """
        # 方法1: 使用CSS选择器直接定位报告链接（已验证成功的选择器）
        # 根据实际测试，成功的选择器是：table.table-model tbody tr td:nth-child(2) a
        css_selector = 'table.table-model tbody tr td:nth-child(2) a'
        
        try:
            elements = soup.select(css_selector)
            if elements:
                print(f"[调试] CSS选择器找到 {len(elements)} 个链接")
                
                # 提取链接的父行（tr）
                report_rows = []
                for link_idx, link in enumerate(elements[:limit]):
                    parent_tr = link.find_parent('tr')
                    if parent_tr and parent_tr not in report_rows:
                        link_text = link.get_text(strip=True)
                        link_href = link.get('href', '')
                        print(f"[调试] 链接 {link_idx+1}: '{link_text[:50]}...' -> {link_href[:80]}")
                        report_rows.append(parent_tr)
                
                if report_rows:
                    print(f"[成功] 找到 {len(report_rows)} 个报告行")
                    return report_rows[:limit]
        except Exception as e:
            print(f"[调试] CSS选择器执行出错: {str(e)}")
        
        # 方法2: 查找表格中"报告名称"列所在的表格行（通过列索引）
        print(f"[调试] 方法1失败，尝试方法2：通过列索引查找")
        all_tables = soup.find_all('table', class_='floathead')
        if not all_tables:
            all_tables = soup.find_all('table')
        
        for table in all_tables:
            # 查找表头，定位"报告名称"列的索引
            thead = table.find('thead')
            if thead:
                header_row = thead.find('tr')
                if header_row:
                    headers = header_row.find_all(['th', 'td'])
                    report_name_col_index = -1
                    for idx, header in enumerate(headers):
                        header_text = header.get_text(strip=True)
                        if '报告名称' in header_text:
                            report_name_col_index = idx
                            print(f"[调试] 找到'报告名称'列，索引: {idx}")
                            break
                    
                    # 如果找到了报告名称列，提取该列的所有行
                    if report_name_col_index >= 0:
                        tbody = table.find('tbody')
                        if tbody:
                            rows = tbody.find_all('tr')
                            report_rows = []
                            for row in rows:
                                cells = row.find_all(['td', 'th'])
                                if len(cells) > report_name_col_index:
                                    cell = cells[report_name_col_index]
                                    link = cell.find('a', href=True)
                                    if link and link.get_text(strip=True):
                                        report_rows.append(row)
                                        if len(report_rows) >= limit:
                                            break
                            if report_rows:
                                print(f"[调试] 方法2成功，找到 {len(report_rows)} 个报告行")
                                return report_rows
        
        # 方法3: 直接查找表格行，包含报告链接的行（备用方法）
        print(f"[调试] 方法2失败，尝试方法3：遍历所有表格行查找链接")
        all_rows = soup.find_all('tr')
        report_rows = []
        checked_rows = 0
        for row_idx, row in enumerate(all_rows):
            # 跳过明显的表头行
            if 'head' in row.get('class', []) or row.find('th'):
                row_text = row.get_text()
                if '报告名称' in row_text or '序号' in row_text:
                    continue
            
            # 查找行中的链接（优先查找第二列的链接）
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                # 检查第二列是否有链接
                second_cell = cells[1]
                link = second_cell.find('a', href=True)
                if link:
                    link_text = link.get_text(strip=True)
                    if link_text and len(link_text) > 5:
                        report_rows.append(row)
                        checked_rows += 1
                        if len(report_rows) >= limit:
                            break
            else:
                # 如果没有第二列，查找行中所有链接
                links = row.find_all('a', href=True)
                for link in links:
                    href = link.get('href', '')
                    link_text = link.get_text(strip=True)
                    if (('report' in href.lower() or 'detail' in href.lower() or 
                         '/report/' in href or len(link_text) > 5) and 
                        link_text and not link_text.isdigit()):
                        report_rows.append(row)
                        checked_rows += 1
                        break
            
            if len(report_rows) >= limit:
                break
        
        if report_rows:
            print(f"[调试] 方法3成功，找到 {len(report_rows)} 个报告行")
            return report_rows[:limit]
        
        # 如果所有方法都失败，输出调试信息
        print(f"[调试] 所有方法都未找到报告行！")
        print(f"[调试] 找到 {len(soup.find_all('table'))} 个表格")
        print(f"[调试] 找到 {len(all_rows)} 个表格行")
        
        return []
    
    def _parse_report_item(self, item) -> Optional[ReportInfo]:
        """
        解析单个报告项（委托方法）
        
        从表格行中提取报告名称（链接）和日期
        
        Args:
            item: 报告项元素（表格行）
            
        Returns:
            报告信息，解析失败返回None
        """
        try:
            # 查找所有单元格
            cells = item.find_all(['td', 'th'])
            
            # 查找报告名称链接（通常在"报告名称"列中）
            title_link = None
            title = ""
            
            # 方法1: 查找最长的链接文本（通常是报告名称）
            all_links = item.find_all('a', href=True)
            for link in all_links:
                link_text = link.get_text(strip=True)
                # 报告名称通常较长，且不是纯数字
                if len(link_text) > 5 and not link_text.isdigit():
                    title_link = link
                    title = link_text
                    break
            
            # 方法2: 如果没找到，查找第一个非空链接
            if not title_link and all_links:
                for link in all_links:
                    link_text = link.get_text(strip=True)
                    if link_text and not link_text.isdigit():
                        title_link = link
                        title = link_text
                        break
            
            if not title_link or not title:
                return None
            
            detail_url = title_link.get('href', '')
            
            # 补全URL（如果是相对路径）
            if detail_url.startswith('/'):
                detail_url = f"https://data.eastmoney.com{detail_url}"
            elif not detail_url.startswith('http'):
                # 尝试从URL中提取报告ID
                if 'report' in detail_url.lower() or 'detail' in detail_url.lower():
                    detail_url = f"https://data.eastmoney.com{detail_url}" if not detail_url.startswith('/') else f"https://data.eastmoney.com{detail_url}"
                else:
                    detail_url = f"https://data.eastmoney.com/report/{detail_url}"
            
            # 查找日期（从表格单元格中提取）
            date = self._extract_date(item)
            
            # 从URL推断报告类型
            report_type = self._infer_report_type(detail_url)
            
            return ReportInfo(
                title=title,
                date=date,
                detail_url=detail_url,
                report_type=report_type
            )
        except Exception as e:
            print(f"解析报告项失败: {str(e)}")
            return None
    
    def _extract_date(self, item) -> str:
        """
        提取日期（委托方法）
        
        Args:
            item: 报告项元素（表格行）
            
        Returns:
            日期字符串
        """
        # 尝试多种方式提取日期
        date_cells = item.find_all(['td', 'th'])
        for cell in date_cells:
            text = cell.get_text(strip=True)
            # 检查是否是日期格式
            # YYYY-MM-DD, YYYY/MM/DD, YYYY.MM.DD
            if len(text) >= 8:
                # 检查是否包含日期分隔符
                if ('-' in text or '/' in text or '.' in text) and len(text) <= 12:
                    # 尝试提取日期部分
                    import re
                    # 匹配 YYYY-MM-DD 或 YYYY/MM/DD 格式
                    date_match = re.search(r'(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})', text)
                    if date_match:
                        year, month, day = date_match.groups()
                        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    # 匹配 YYYYMMDD 格式
                    date_match = re.search(r'(\d{4})(\d{2})(\d{2})', text)
                    if date_match:
                        year, month, day = date_match.groups()
                        return f"{year}-{month}-{day}"
        
        # 如果没找到，尝试从标题中提取日期（有些报告标题包含日期）
        title_cell = item.find('a')
        if title_cell:
            title_text = title_cell.get_text()
            import re
            # 查找标题中的日期
            date_match = re.search(r'(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})', title_text)
            if date_match:
                year, month, day = date_match.groups()
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        # 如果都没找到，返回当前日期（格式：YYYY-MM-DD）
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d')
    
    def _infer_report_type(self, url: str) -> str:
        """
        从URL推断报告类型（委托方法）
        
        Args:
            url: 报告URL
            
        Returns:
            报告类型
        """
        if 'strategy' in url:
            return 'strategy'
        elif 'industry' in url:
            return 'industry'
        elif 'macro' in url or 'macresearch' in url:
            return 'macro'
        elif 'stock' in url:
            return 'stock'
        else:
            return 'unknown'

