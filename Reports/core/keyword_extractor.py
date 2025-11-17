"""
关键词提取工具
从报告标题和详情页HTML中提取个股、行业、策略、宏观等关键词
"""

import re
from typing import Dict, List, Optional
from bs4 import BeautifulSoup


class KeywordExtractor:
    """
    关键词提取器
    从报告标题中提取结构化关键词
    """
    
    def __init__(self):
        """初始化关键词提取器"""
        # 行业关键词列表（常见行业）
        self.industry_keywords = [
            '银行', '证券', '保险', '金融', '地产', '房地产', '建筑', '建材',
            '钢铁', '有色', '煤炭', '石油', '化工', '电力', '新能源', '光伏',
            '风电', '核电', '汽车', '新能源车', '电动车', '医药', '生物', '医疗',
            '消费', '食品', '饮料', '白酒', '零售', '电商', '互联网', '科技',
            '电子', '半导体', '芯片', '通信', '5G', '人工智能', 'AI', '大数据',
            '云计算', '软件', '游戏', '传媒', '教育', '旅游', '航空', '物流',
            '农业', '养殖', '环保', '公用事业', '交通运输', '机械', '军工'
        ]
        
        # 策略关键词
        self.strategy_keywords = [
            '配置', '估值', '投资', '策略', '配置建议', '投资策略', '市场',
            '行情', '趋势', '展望', '预测', '分析', '研究', '报告', '观点',
            '机会', '风险', '建议', '推荐', '评级', '目标价', '买入', '卖出',
            '持有', '增持', '减持', '中性', '看好', '看空'
        ]
        
        # 宏观关键词
        self.macro_keywords = [
            'GDP', 'CPI', 'PPI', '通胀', '通缩', '利率', '汇率', '货币政策',
            '财政政策', '经济', '宏观', '宏观研究', '宏观经济', '经济数据',
            'PMI', '就业', '失业', '消费', '投资', '出口', '进口', '贸易',
            '财政', '债务', '赤字', '流动性', '信贷', 'M2', '社融'
        ]
        
        # 股票代码正则（6位数字）
        self.stock_code_pattern = re.compile(r'\b(\d{6})\b')
        
        # 常见股票名称关键词（用于识别个股报告）
        self.stock_name_keywords = [
            '股份', '集团', '公司', '有限', '科技', '发展', '实业', '投资',
            '控股', '股份公司', 'A股', 'H股'
        ]
    
    def extract_keywords(self, title: str, detail_url: Optional[str] = None, detail_html: Optional[str] = None) -> Dict[str, List[str]]:
        """
        从标题和详情页HTML中提取关键词
        
        Args:
            title: 报告标题
            detail_url: 详情页URL（可选）
            detail_html: 详情页HTML内容（可选，用于提取分类标题/子标题）
            
        Returns:
            关键词字典，包含：
            - stocks: 个股列表（股票代码、股票名称）
            - industries: 行业列表
            - strategies: 策略关键词列表
            - macro: 宏观关键词列表
        """
        keywords = {
            'stocks': [],
            'industries': [],
            'strategies': [],
            'macro': []
        }
        
        # 从标题提取关键词
        if title:
            title_keywords = self._extract_from_title(title)
            for key in keywords:
                keywords[key].extend(title_keywords[key])
        
        # 从详情页HTML提取分类标题/子标题
        if detail_html:
            html_keywords = self._extract_from_detail_html(detail_html)
            for key in keywords:
                # 合并但不重复
                for kw in html_keywords[key]:
                    if kw not in keywords[key]:
                        keywords[key].append(kw)
        
        return keywords
    
    def _extract_from_title(self, title: str) -> Dict[str, List[str]]:
        """从标题中提取关键词"""
        keywords = {
            'stocks': [],
            'industries': [],
            'strategies': [],
            'macro': []
        }
        
        title_lower = title.lower()
        
        # 1. 提取股票代码
        stock_codes = self.stock_code_pattern.findall(title)
        keywords['stocks'].extend(stock_codes)
        
        # 2. 提取行业关键词
        for industry in self.industry_keywords:
            if industry in title:
                if industry not in keywords['industries']:
                    keywords['industries'].append(industry)
        
        # 3. 提取策略关键词
        for strategy in self.strategy_keywords:
            if strategy in title:
                if strategy not in keywords['strategies']:
                    keywords['strategies'].append(strategy)
        
        # 4. 提取宏观关键词
        for macro in self.macro_keywords:
            if macro.lower() in title_lower or macro in title:
                if macro not in keywords['macro']:
                    keywords['macro'].append(macro)
        
        # 5. 尝试从标题中提取股票名称（简单规则）
        if '：' in title or ':' in title:
            parts = re.split('[：:]', title, 1)
            if len(parts) > 0:
                potential_stock_name = parts[0].strip()
                if any(kw in potential_stock_name for kw in self.stock_name_keywords):
                    if potential_stock_name not in keywords['stocks']:
                        keywords['stocks'].append(potential_stock_name)
        
        return keywords
    
    def _extract_from_detail_html(self, html_content: str) -> Dict[str, List[str]]:
        """
        从详情页HTML中提取分类标题/子标题作为关键词
        
        Args:
            html_content: 详情页HTML内容
            
        Returns:
            关键词字典
        """
        keywords = {
            'stocks': [],
            'industries': [],
            'strategies': [],
            'macro': []
        }
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 提取所有可能的标题元素（h1-h6, 带class的div等）
            # 1. 查找所有标题标签
            headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            for heading in headings:
                text = heading.get_text(strip=True)
                if text:
                    self._classify_text_to_keywords(text, keywords)
            
            # 2. 查找常见的分类标题容器（class包含"title", "category", "tag"等）
            title_elements = soup.find_all(class_=re.compile(r'title|category|tag|label|name', re.I))
            for elem in title_elements:
                text = elem.get_text(strip=True)
                if text and len(text) < 50:  # 标题通常不会太长
                    self._classify_text_to_keywords(text, keywords)
            
            # 3. 查找面包屑导航
            breadcrumbs = soup.find_all(class_=re.compile(r'breadcrumb|nav|path', re.I))
            for breadcrumb in breadcrumbs:
                links = breadcrumb.find_all('a')
                for link in links:
                    text = link.get_text(strip=True)
                    if text:
                        self._classify_text_to_keywords(text, keywords)
            
            # 4. 查找标签元素
            tags = soup.find_all(class_=re.compile(r'tag|label|badge', re.I))
            for tag in tags:
                text = tag.get_text(strip=True)
                if text and len(text) < 30:
                    self._classify_text_to_keywords(text, keywords)
            
        except Exception as e:
            print(f"[关键词提取] 解析详情页HTML失败: {e}")
        
        return keywords
    
    def _classify_text_to_keywords(self, text: str, keywords: Dict[str, List[str]]):
        """
        将文本分类到对应的关键词类别
        
        Args:
            text: 要分类的文本
            keywords: 关键词字典（会被修改）
        """
        if not text or len(text) > 100:  # 跳过过长的文本
            return
        
        text_lower = text.lower()
        
        # 检查是否包含股票代码
        stock_codes = self.stock_code_pattern.findall(text)
        for code in stock_codes:
            if code not in keywords['stocks']:
                keywords['stocks'].append(code)
        
        # 检查行业关键词
        for industry in self.industry_keywords:
            if industry in text and industry not in keywords['industries']:
                keywords['industries'].append(industry)
        
        # 检查策略关键词
        for strategy in self.strategy_keywords:
            if strategy in text and strategy not in keywords['strategies']:
                keywords['strategies'].append(strategy)
        
        # 检查宏观关键词
        for macro in self.macro_keywords:
            if (macro.lower() in text_lower or macro in text) and macro not in keywords['macro']:
                keywords['macro'].append(macro)
        
        # 如果文本看起来像股票名称（包含常见关键词且长度适中）
        if 2 <= len(text) <= 20:
            if any(kw in text for kw in self.stock_name_keywords):
                if text not in keywords['stocks']:
                    keywords['stocks'].append(text)
    
    def extract_metadata(self, title: str, date: str, detail_url: Optional[str] = None, detail_html: Optional[str] = None) -> Dict:
        """
        提取报告的完整元信息
        
        Args:
            title: 报告标题
            date: 报告日期
            detail_url: 详情页URL
            detail_html: 详情页HTML内容（可选）
            
        Returns:
            元信息字典
        """
        keywords = self.extract_keywords(title, detail_url, detail_html)
        
        # 生成简要摘要（从标题提取）
        summary = self._generate_summary(title)
        
        metadata = {
            'keywords': keywords,
            'summary': summary,
            'source': 'eastmoney',
            'extracted_at': None  # 可以在后端填充时间戳
        }
        
        return metadata
    
    def _generate_summary(self, title: str) -> str:
        """
        从标题生成简要摘要
        
        Args:
            title: 报告标题
            
        Returns:
            摘要文本
        """
        # 如果标题过长，截取前100个字符
        if len(title) > 100:
            return title[:100] + '...'
        return title


# 全局实例
_keyword_extractor = None

def get_keyword_extractor() -> KeywordExtractor:
    """获取全局关键词提取器实例"""
    global _keyword_extractor
    if _keyword_extractor is None:
        _keyword_extractor = KeywordExtractor()
    return _keyword_extractor

