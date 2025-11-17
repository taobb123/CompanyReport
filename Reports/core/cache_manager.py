"""
缓存管理组件
用于缓存爬取结果，避免重复爬取
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from config import REPORT_TYPES


class ReportCacheManager:
    """
    报告缓存管理器
    使用文件存储缓存，每个类型+limit组合独立缓存
    缓存有效期：24小时
    """
    
    def __init__(self, cache_dir: str = "cache"):
        """
        初始化缓存管理器
        
        Args:
            cache_dir: 缓存目录路径
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_file = self.cache_dir / "reports_cache.json"
        self.cache_data = self._load_cache()
    
    def _load_cache(self) -> Dict[str, Any]:
        """加载缓存文件"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[缓存] 加载缓存文件失败: {e}，将创建新缓存")
                return {}
        return {}
    
    def _save_cache(self):
        """保存缓存到文件"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[缓存] 保存缓存文件失败: {e}")
    
    def _get_cache_key(self, report_type: str, limit: int) -> str:
        """
        生成缓存键
        
        Args:
            report_type: 报告类型
            limit: 数量限制
            
        Returns:
            缓存键
        """
        return f"{report_type}_{limit}"
    
    def _is_expired(self, cache_entry: Dict[str, Any]) -> bool:
        """
        检查缓存是否过期
        
        Args:
            cache_entry: 缓存条目
            
        Returns:
            是否过期
        """
        if 'expires_at' not in cache_entry:
            return True
        
        try:
            expires_at = datetime.fromisoformat(cache_entry['expires_at'])
            return datetime.now() > expires_at
        except Exception as e:
            print(f"[缓存] 解析过期时间失败: {e}")
            return True
    
    def get_cache(self, report_type: str, limit: int) -> Optional[Dict[str, Any]]:
        """
        获取缓存
        
        Args:
            report_type: 报告类型
            limit: 数量限制
            
        Returns:
            缓存数据，如果不存在或过期则返回None
        """
        cache_key = self._get_cache_key(report_type, limit)
        
        if cache_key not in self.cache_data:
            return None
        
        cache_entry = self.cache_data[cache_key]
        
        # 检查是否过期
        if self._is_expired(cache_entry):
            print(f"[缓存] 缓存已过期: {cache_key}")
            # 删除过期缓存
            del self.cache_data[cache_key]
            self._save_cache()
            return None
        
        print(f"[缓存] 使用缓存: {cache_key} (过期时间: {cache_entry.get('expires_at')})")
        return cache_entry.get('data')
    
    def set_cache(self, report_type: str, limit: int, data: List[Dict[str, Any]]):
        """
        设置缓存
        
        Args:
            report_type: 报告类型
            limit: 数量限制
            data: 要缓存的数据
        """
        cache_key = self._get_cache_key(report_type, limit)
        
        # 计算过期时间（24小时后）
        now = datetime.now()
        expires_at = now + timedelta(hours=24)
        
        cache_entry = {
            'data': data,
            'timestamp': now.isoformat(),
            'expires_at': expires_at.isoformat(),
            'report_type': report_type,
            'limit': limit
        }
        
        self.cache_data[cache_key] = cache_entry
        self._save_cache()
        print(f"[缓存] 已缓存: {cache_key} (过期时间: {expires_at.isoformat()})")
    
    def clear_cache(self, report_type: Optional[str] = None, limit: Optional[int] = None):
        """
        清除缓存
        
        Args:
            report_type: 报告类型，如果为None则清除所有
            limit: 数量限制，如果为None则清除该类型的所有limit
        """
        if report_type is None:
            # 清除所有缓存
            self.cache_data = {}
            self._save_cache()
            print("[缓存] 已清除所有缓存")
        elif limit is None:
            # 清除该类型的所有limit缓存
            keys_to_delete = [k for k in self.cache_data.keys() if k.startswith(f"{report_type}_")]
            for key in keys_to_delete:
                del self.cache_data[key]
            self._save_cache()
            print(f"[缓存] 已清除类型 {report_type} 的所有缓存")
        else:
            # 清除特定类型和limit的缓存
            cache_key = self._get_cache_key(report_type, limit)
            if cache_key in self.cache_data:
                del self.cache_data[cache_key]
                self._save_cache()
                print(f"[缓存] 已清除缓存: {cache_key}")
    
    def get_cache_status(self) -> Dict[str, Any]:
        """
        获取缓存状态信息
        
        Returns:
            缓存状态字典
        """
        status = {
            'total_entries': len(self.cache_data),
            'entries': {}
        }
        
        for cache_key, cache_entry in self.cache_data.items():
            is_expired = self._is_expired(cache_entry)
            status['entries'][cache_key] = {
                'report_type': cache_entry.get('report_type'),
                'limit': cache_entry.get('limit'),
                'timestamp': cache_entry.get('timestamp'),
                'expires_at': cache_entry.get('expires_at'),
                'is_expired': is_expired,
                'data_count': len(cache_entry.get('data', []))
            }
        
        return status
    
    def cleanup_expired(self):
        """清理所有过期的缓存"""
        expired_keys = []
        for cache_key, cache_entry in self.cache_data.items():
            if self._is_expired(cache_entry):
                expired_keys.append(cache_key)
        
        for key in expired_keys:
            del self.cache_data[key]
        
        if expired_keys:
            self._save_cache()
            print(f"[缓存] 已清理 {len(expired_keys)} 个过期缓存")
        else:
            print("[缓存] 没有过期缓存需要清理")


# 全局缓存管理器实例
_cache_manager = None

def get_cache_manager() -> ReportCacheManager:
    """获取全局缓存管理器实例"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = ReportCacheManager()
        # 启动时清理过期缓存
        _cache_manager.cleanup_expired()
    return _cache_manager

