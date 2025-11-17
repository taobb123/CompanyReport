"""
AKShare数据源客户端
使用AKShare API获取证券研究报告（合法合规）
"""

from typing import Optional, List
from interfaces import ReportInfo


class AkshareDataClient:
    """
    AKShare数据源客户端
    使用AKShare API获取研究报告数据
    """
    
    def __init__(self):
        """初始化AKShare客户端"""
        self.ak = None
        self._init_akshare()
    
    def _init_akshare(self):
        """初始化AKShare"""
        try:
            import akshare as ak
            self.ak = ak
            print(f"[成功] AKShare初始化成功")
        except ImportError:
            print(f"[警告] AKShare未安装")
            print(f"[提示] 请安装: pip install akshare")
            self.ak = None
        except Exception as e:
            print(f"[警告] AKShare初始化失败: {str(e)}")
            self.ak = None
    
    def get_reports(self, report_type: str, limit: int = 6) -> List[ReportInfo]:
        """
        获取研究报告列表
        
        Args:
            report_type: 报告类型（strategy/industry/macro/profit）
            limit: 获取数量限制
            
        Returns:
            报告信息列表
        """
        if not self.ak:
            print(f"[错误] AKShare未初始化")
            return []
        
        try:
            reports = []
            
            # 尝试使用AKShare的研究报告接口
            # 注意：需要根据AKShare最新文档调整接口名称
            try:
                # 方法1: 尝试stock_research_report_em（东方财富研究报告）
                if hasattr(self.ak, 'stock_research_report_em'):
                    print(f"[调试] 使用 stock_research_report_em 接口")
                    df = self.ak.stock_research_report_em()
                    reports = self._parse_akshare_data(df, report_type, limit)
                # 方法2: 尝试report_rc（研究报告）
                elif hasattr(self.ak, 'report_rc'):
                    print(f"[调试] 使用 report_rc 接口")
                    df = self.ak.report_rc()
                    reports = self._parse_akshare_data(df, report_type, limit)
                # 方法3: 查找所有包含report的函数
                else:
                    report_functions = [name for name in dir(self.ak) 
                                      if 'report' in name.lower() and not name.startswith('_')]
                    if report_functions:
                        print(f"[调试] 找到AKShare报告相关函数: {report_functions[:5]}")
                        # 尝试第一个
                        func = getattr(self.ak, report_functions[0])
                        df = func()
                        reports = self._parse_akshare_data(df, report_type, limit)
                    else:
                        print(f"[警告] 未找到AKShare研究报告接口")
                        print(f"[提示] 请查看AKShare文档: https://www.akshare.xyz/")
                        print(f"[提示] 或运行: import akshare as ak; print([x for x in dir(ak) if 'report' in x.lower()])")
                        return []
            except Exception as e:
                print(f"[错误] 调用AKShare接口失败: {str(e)}")
                import traceback
                print(f"[错误详情] {traceback.format_exc()[:500]}")
                return []
            
            return reports[:limit]
            
        except Exception as e:
            print(f"AKShare获取报告失败: {str(e)}")
            import traceback
            print(f"[错误详情] {traceback.format_exc()[:500]}")
            return []
    
    def _parse_akshare_data(self, df, report_type: str, limit: int) -> List[ReportInfo]:
        """
        解析AKShare返回的数据
        
        Args:
            df: AKShare返回的DataFrame
            report_type: 报告类型
            limit: 限制数量
            
        Returns:
            报告信息列表
        """
        reports = []
        
        try:
            import pandas as pd
            if df is None or df.empty:
                print(f"[警告] AKShare返回空数据")
                return []
            
            # 打印列名以便调试
            print(f"[调试] AKShare数据列: {list(df.columns)}")
            print(f"[调试] 数据行数: {len(df)}")
            
            # 根据实际列名映射字段
            title_col = None
            date_col = None
            url_col = None
            
            # 查找标题列
            for col in df.columns:
                col_lower = str(col).lower()
                if 'title' in col_lower or '名称' in str(col) or '报告' in str(col) or '标题' in str(col):
                    title_col = col
                    break
            
            # 查找日期列
            for col in df.columns:
                col_lower = str(col).lower()
                if 'date' in col_lower or '日期' in str(col) or '时间' in str(col):
                    date_col = col
                    break
            
            # 查找URL列
            for col in df.columns:
                col_lower = str(col).lower()
                if 'url' in col_lower or '链接' in str(col) or 'href' in col_lower or 'pdf' in col_lower:
                    url_col = col
                    break
            
            # 如果没有找到，使用前几列
            if not title_col and len(df.columns) > 0:
                title_col = df.columns[0]
            if not date_col and len(df.columns) > 1:
                date_col = df.columns[1]
            if not url_col and len(df.columns) > 2:
                url_col = df.columns[2]
            
            print(f"[调试] 使用列映射: 标题={title_col}, 日期={date_col}, URL={url_col}")
            
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
            
            print(f"[成功] 从AKShare解析到 {len(reports)} 篇报告")
            return reports
            
        except Exception as e:
            print(f"[错误] 解析AKShare数据失败: {str(e)}")
            import traceback
            print(f"[错误详情] {traceback.format_exc()[:500]}")
            return []

