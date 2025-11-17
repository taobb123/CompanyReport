"""
Tushare数据源客户端
使用Tushare API获取证券研究报告（合法合规，推荐）
"""

import time
from typing import Optional, List
from interfaces import ReportInfo


class TushareDataClient:
    """
    Tushare数据源客户端
    使用Tushare API获取研究报告数据
    """
    
    def __init__(self, token: str = None):
        """
        初始化Tushare客户端
        
        Args:
            token: Tushare API Token（如果提供）
        """
        self.token = token
        self.pro = None
        self._last_request_time = 0  # 上次请求时间（用于速率限制）
        self._min_request_interval = 35  # 最小请求间隔（秒），免费版每分钟2次，所以至少30秒间隔
        self._init_tushare()
    
    def _init_tushare(self):
        """初始化Tushare"""
        try:
            import tushare as ts
            
            # 如果提供了token，设置token
            if self.token:
                ts.set_token(self.token)
                print(f"[成功] 使用提供的Tushare Token")
            else:
                # 尝试从环境变量获取token
                import os
                token = os.getenv('TUSHARE_TOKEN')
                if token:
                    ts.set_token(token)
                    print(f"[成功] 从环境变量获取Tushare Token")
                else:
                    print(f"[警告] 未提供Tushare Token")
                    print(f"[提示] 获取Token: https://tushare.pro/")
                    print(f"[提示] 设置方式1: 在代码中提供token参数")
                    print(f"[提示] 设置方式2: 设置环境变量 TUSHARE_TOKEN")
                    print(f"[提示] 免费版有积分限制，但足够学习使用")
            
            self.pro = ts.pro_api()
            print(f"[成功] Tushare初始化成功")
        except ImportError:
            print(f"[警告] Tushare未安装")
            print(f"[提示] 请安装: pip install tushare")
            self.pro = None
        except Exception as e:
            print(f"[警告] Tushare初始化失败: {str(e)}")
            self.pro = None
    
    def _wait_for_rate_limit(self):
        """等待以满足速率限制"""
        current_time = time.time()
        time_since_last_request = current_time - self._last_request_time
        
        if time_since_last_request < self._min_request_interval:
            wait_time = self._min_request_interval - time_since_last_request
            print(f"[提示] 等待 {wait_time:.1f} 秒以满足Tushare速率限制（免费版每分钟最多2次）...")
            time.sleep(wait_time)
        
        self._last_request_time = time.time()
    
    def _call_api_with_retry(self, api_func, max_retries: int = 3):
        """
        调用API并带重试机制
        
        Args:
            api_func: API函数（无参数）
            max_retries: 最大重试次数
            
        Returns:
            API返回的DataFrame，失败返回None
        """
        for attempt in range(max_retries):
            try:
                # 等待速率限制
                self._wait_for_rate_limit()
                
                # 调用API
                return api_func()
                
            except Exception as e:
                error_msg = str(e)
                
                # 检查是否是速率限制错误
                if '每分钟最多访问' in error_msg or 'rate limit' in error_msg.lower():
                    if attempt < max_retries - 1:
                        # 速率限制，等待更长时间后重试
                        wait_time = self._min_request_interval * (attempt + 2)
                        print(f"[警告] 遇到速率限制，等待 {wait_time} 秒后重试（尝试 {attempt + 2}/{max_retries}）...")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"[错误] 达到最大重试次数，仍然遇到速率限制")
                        print(f"[提示] Tushare免费版每分钟最多访问2次")
                        print(f"[提示] 建议：")
                        print(f"  1. 等待1分钟后再次运行")
                        print(f"  2. 升级到付费版获得更高速率限制")
                        print(f"  3. 使用AKShare作为替代数据源（无需速率限制）")
                        return None
                
                # 其他错误
                print(f"[错误] 调用Tushare接口失败（尝试 {attempt + 1}/{max_retries}）: {error_msg}")
                if attempt < max_retries - 1:
                    wait_time = 5 * (attempt + 1)  # 指数退避
                    print(f"[提示] 等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                else:
                    import traceback
                    print(f"[错误详情] {traceback.format_exc()[:500]}")
                    print(f"[提示] 可能是积分不足或接口名称已更新")
                    return None
        
        return None
    
    def get_reports(self, report_type: str, limit: int = 6) -> List[ReportInfo]:
        """
        获取研究报告列表
        
        Args:
            report_type: 报告类型（strategy/industry/macro/profit）
            limit: 获取数量限制
            
        Returns:
            报告信息列表
        """
        if not self.pro:
            print(f"[错误] Tushare未初始化")
            return []
        
        try:
            reports = []
            
            # Tushare的研究报告接口
            # 注意：需要根据Tushare最新文档调整接口名称
            df = None
            
            # 方法1: 尝试report_rc（研究报告）
            if hasattr(self.pro, 'report_rc'):
                print(f"[调试] 使用 report_rc 接口")
                df = self._call_api_with_retry(lambda: self.pro.report_rc(limit=limit))
                if df is not None:
                    reports = self._parse_tushare_data(df, report_type, limit)
            # 方法2: 尝试其他可能的接口
            elif hasattr(self.pro, 'report'):
                print(f"[调试] 使用 report 接口")
                df = self._call_api_with_retry(lambda: self.pro.report(limit=limit))
                if df is not None:
                    reports = self._parse_tushare_data(df, report_type, limit)
            else:
                print(f"[警告] 未找到Tushare研究报告接口")
                print(f"[提示] 请查看Tushare文档: https://tushare.pro/document/2")
                print(f"[提示] 或运行: import tushare as ts; pro = ts.pro_api(); print([x for x in dir(pro) if 'report' in x.lower()])")
                return []
            
            if df is None:
                print(f"[错误] 无法获取Tushare数据")
                return []
            
            return reports[:limit]
            
        except Exception as e:
            print(f"Tushare获取报告失败: {str(e)}")
            import traceback
            print(f"[错误详情] {traceback.format_exc()[:500]}")
            return []
    
    def _parse_tushare_data(self, df, report_type: str, limit: int) -> List[ReportInfo]:
        """
        解析Tushare返回的数据
        
        Args:
            df: Tushare返回的DataFrame
            report_type: 报告类型
            limit: 限制数量
            
        Returns:
            报告信息列表
        """
        reports = []
        
        try:
            import pandas as pd
            if df is None or df.empty:
                print(f"[警告] Tushare返回空数据")
                return []
            
            # 打印列名以便调试
            print(f"[调试] Tushare数据列: {list(df.columns)}")
            print(f"[调试] 数据行数: {len(df)}")
            
            # 根据实际列名映射字段
            title_col = None
            date_col = None
            url_col = None
            
            # 查找标题列（优先匹配）
            for col in df.columns:
                col_lower = str(col).lower()
                col_str = str(col)
                if any(keyword in col_lower for keyword in ['title', 'name', '名称', '标题', '报告名称', '报告标题']):
                    title_col = col
                    break
            
            # 如果没找到标题列，尝试使用第一列（通常第一列是标题）
            if not title_col and len(df.columns) > 0:
                # 检查第一列是否看起来像标题（不是纯数字，不是日期格式）
                first_col = df.columns[0]
                first_sample = str(df[first_col].iloc[0]) if len(df) > 0 else ""
                if not first_sample.isdigit() and len(first_sample) > 5:
                    title_col = first_col
            
            # 查找日期列（优先匹配）
            for col in df.columns:
                col_lower = str(col).lower()
                col_str = str(col)
                if any(keyword in col_lower for keyword in ['date', 'time', '日期', '时间', '发布日期', '报告日期']):
                    date_col = col
                    break
            
            # 如果没找到日期列，尝试使用第二列（如果第一列是标题）
            if not date_col and len(df.columns) > 1:
                second_col = df.columns[1]
                # 检查第二列是否看起来像日期（8位数字或包含日期格式）
                if len(df) > 0:
                    second_sample = str(df[second_col].iloc[0])
                    if second_sample.isdigit() and len(second_sample) == 8:  # 可能是YYYYMMDD格式
                        date_col = second_col
            
            # 查找URL列（必须严格匹配，避免误识别日期）
            for col in df.columns:
                col_lower = str(col).lower()
                col_str = str(col)
                # 只匹配明确的URL相关关键词
                if any(keyword in col_lower for keyword in ['url', 'link', 'href', '链接', 'pdf_url', 'report_url', '下载链接']):
                    # 验证该列的值是否真的是URL
                    if len(df) > 0:
                        sample_value = str(df[col].iloc[0])
                        if sample_value.startswith(('http://', 'https://')):
                            url_col = col
                            break
            
            # 如果没找到URL列，不强制使用第三列（可能是其他字段）
            # 这样避免将日期字段误识别为URL
            
            print(f"[调试] 使用列映射: 标题={title_col}, 日期={date_col}, URL={url_col if url_col else '(未找到)'}")
            
            # 解析数据
            for idx, row in df.head(limit).iterrows():
                try:
                    title = str(row[title_col]) if title_col and pd.notna(row[title_col]) else f"报告_{idx}"
                    date = str(row[date_col]) if date_col and pd.notna(row[date_col]) else ""
                    detail_url_raw = str(row[url_col]) if url_col and pd.notna(row[url_col]) else ""
                    
                    # 清理日期格式
                    if date:
                        date = date.replace('/', '-').replace('.', '-')
                        if len(date) > 10:
                            date = date[:10]
                    
                    # 验证URL是否有效（必须以http://或https://开头）
                    detail_url = ""
                    if detail_url_raw:
                        detail_url_raw = detail_url_raw.strip()
                        # 检查是否是有效的URL
                        if detail_url_raw.startswith(('http://', 'https://')):
                            detail_url = detail_url_raw
                        else:
                            # 如果不是有效URL，可能是日期或其他字段，忽略它
                            print(f"[提示] 字段'{url_col}'的值'{detail_url_raw[:50]}'不是有效URL，已忽略")
                    
                    # 如果标题为空，跳过
                    if not title or title == 'nan':
                        continue
                    
                    reports.append(ReportInfo(
                        title=title,
                        date=date,
                        detail_url=detail_url,  # 只使用有效的URL
                        report_type=report_type
                    ))
                except Exception as e:
                    print(f"[警告] 解析第{idx}行数据失败: {str(e)}")
                    continue
            
            print(f"[成功] 从Tushare解析到 {len(reports)} 篇报告")
            return reports
            
        except Exception as e:
            print(f"[错误] 解析Tushare数据失败: {str(e)}")
            import traceback
            print(f"[错误详情] {traceback.format_exc()[:500]}")
            return []

