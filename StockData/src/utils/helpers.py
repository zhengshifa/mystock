"""
辅助工具函数模块
"""
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Union


def create_directories(*paths: str) -> None:
    """创建目录"""
    for path in paths:
        Path(path).mkdir(parents=True, exist_ok=True)


def format_symbol(symbol: str) -> str:
    """格式化股票代码"""
    # 移除空格和特殊字符
    symbol = symbol.strip().upper()
    
    # 如果是A股，确保格式正确
    if symbol.startswith(('00', '30', '60', '68')):
        if len(symbol) == 6:
            return f"SH{symbol}" if symbol.startswith(('60', '68')) else f"SZ{symbol}"
    
    return symbol


def generate_hash(data: Union[Dict, List, str]) -> str:
    """生成数据的哈希值，用于去重"""
    if isinstance(data, (dict, list)):
        data_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
    else:
        data_str = str(data)
    
    return hashlib.md5(data_str.encode('utf-8')).hexdigest()


def format_datetime(dt: datetime) -> str:
    """格式化日期时间"""
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def safe_float(value: Any, default: float = 0.0) -> float:
    """安全转换为浮点数"""
    try:
        if value is None:
            return default
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    """安全转换为整数"""
    try:
        if value is None:
            return default
        return int(value)
    except (ValueError, TypeError):
        return default


def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """将列表分块"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def is_trading_time() -> bool:
    """判断是否为交易时间"""
    now = datetime.now()
    
    # 周末不交易
    if now.weekday() >= 5:
        return False
    
    # 交易时间：9:30-11:30, 13:00-15:00
    morning_start = now.replace(hour=9, minute=30, second=0, microsecond=0)
    morning_end = now.replace(hour=11, minute=30, second=0, microsecond=0)
    afternoon_start = now.replace(hour=13, minute=0, second=0, microsecond=0)
    afternoon_end = now.replace(hour=15, minute=0, second=0, microsecond=0)
    
    return (morning_start <= now <= morning_end) or (afternoon_start <= now <= afternoon_end)
