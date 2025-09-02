#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
时间工具模块

提供时间相关的工具函数:
- 时间格式转换
- 交易时间判断
- 时区处理
- 时间计算
"""

import time
from datetime import datetime, date, timedelta, timezone
from typing import Optional, Union, List, Tuple
import pytz
from zoneinfo import ZoneInfo

from .exceptions import ValidationError, DateValidationError


class TimeUtils:
    """时间工具类"""
    
    # 时区定义
    TIMEZONE_MAP = {
        'UTC': timezone.utc,
        'CST': ZoneInfo('Asia/Shanghai'),  # 中国标准时间
        'EST': ZoneInfo('America/New_York'),  # 美东时间
        'PST': ZoneInfo('America/Los_Angeles'),  # 美西时间
        'JST': ZoneInfo('Asia/Tokyo'),  # 日本标准时间
        'HKT': ZoneInfo('Asia/Hong_Kong'),  # 香港时间
    }
    
    # 交易时间定义
    TRADING_HOURS = {
        'A股': {
            'morning': ('09:30', '11:30'),
            'afternoon': ('13:00', '15:00'),
            'timezone': 'CST'
        },
        '港股': {
            'morning': ('09:30', '12:00'),
            'afternoon': ('13:00', '16:00'),
            'timezone': 'HKT'
        },
        '美股': {
            'regular': ('09:30', '16:00'),
            'pre_market': ('04:00', '09:30'),
            'after_hours': ('16:00', '20:00'),
            'timezone': 'EST'
        }
    }
    
    @classmethod
    def now(cls, timezone_name: str = 'CST') -> datetime:
        """获取当前时间"""
        tz = cls.TIMEZONE_MAP.get(timezone_name, cls.TIMEZONE_MAP['CST'])
        return datetime.now(tz)
    
    @classmethod
    def utc_now(cls) -> datetime:
        """获取UTC当前时间"""
        return datetime.now(timezone.utc)
    
    @classmethod
    def timestamp_to_datetime(cls, timestamp: Union[int, float], 
                            timezone_name: str = 'CST') -> datetime:
        """时间戳转datetime"""
        tz = cls.TIMEZONE_MAP.get(timezone_name, cls.TIMEZONE_MAP['CST'])
        return datetime.fromtimestamp(timestamp, tz)
    
    @classmethod
    def datetime_to_timestamp(cls, dt: datetime) -> float:
        """datetime转时间戳"""
        return dt.timestamp()
    
    @classmethod
    def string_to_datetime(cls, date_str: str, format_str: str = '%Y-%m-%d %H:%M:%S',
                          timezone_name: str = 'CST') -> datetime:
        """字符串转datetime"""
        try:
            dt = datetime.strptime(date_str, format_str)
            tz = cls.TIMEZONE_MAP.get(timezone_name, cls.TIMEZONE_MAP['CST'])
            return dt.replace(tzinfo=tz)
        except ValueError as e:
            raise DateValidationError(
                f"Cannot parse date string '{date_str}' with format '{format_str}'",
                date_value=date_str,
                date_format=format_str,
                cause=e
            )
    
    @classmethod
    def datetime_to_string(cls, dt: datetime, format_str: str = '%Y-%m-%d %H:%M:%S') -> str:
        """datetime转字符串"""
        return dt.strftime(format_str)
    
    @classmethod
    def convert_timezone(cls, dt: datetime, from_tz: str, to_tz: str) -> datetime:
        """时区转换"""
        if from_tz not in cls.TIMEZONE_MAP:
            raise ValidationError(f"Unknown timezone: {from_tz}")
        if to_tz not in cls.TIMEZONE_MAP:
            raise ValidationError(f"Unknown timezone: {to_tz}")
        
        from_timezone = cls.TIMEZONE_MAP[from_tz]
        to_timezone = cls.TIMEZONE_MAP[to_tz]
        
        # 如果datetime没有时区信息，假设它是from_tz时区
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=from_timezone)
        
        return dt.astimezone(to_timezone)
    
    @classmethod
    def get_trading_day(cls, dt: Optional[datetime] = None, 
                       timezone_name: str = 'CST') -> date:
        """获取交易日（排除周末）"""
        if dt is None:
            dt = cls.now(timezone_name)
        
        # 如果是周末，返回下一个工作日
        while dt.weekday() >= 5:  # 5=Saturday, 6=Sunday
            dt += timedelta(days=1)
        
        return dt.date()
    
    @classmethod
    def get_previous_trading_day(cls, dt: Optional[datetime] = None,
                               timezone_name: str = 'CST') -> date:
        """获取上一个交易日"""
        if dt is None:
            dt = cls.now(timezone_name)
        
        dt -= timedelta(days=1)
        
        # 如果是周末，继续往前找
        while dt.weekday() >= 5:
            dt -= timedelta(days=1)
        
        return dt.date()
    
    @classmethod
    def get_next_trading_day(cls, dt: Optional[datetime] = None,
                           timezone_name: str = 'CST') -> date:
        """获取下一个交易日"""
        if dt is None:
            dt = cls.now(timezone_name)
        
        dt += timedelta(days=1)
        
        # 如果是周末，继续往后找
        while dt.weekday() >= 5:
            dt += timedelta(days=1)
        
        return dt.date()
    
    @classmethod
    def is_trading_day(cls, dt: datetime) -> bool:
        """判断是否为交易日"""
        return dt.weekday() < 5  # Monday=0, Friday=4
    
    @classmethod
    def is_trading_time(cls, dt: datetime, market: str = 'A股') -> bool:
        """判断是否为交易时间"""
        if not cls.is_trading_day(dt):
            return False
        
        if market not in cls.TRADING_HOURS:
            raise ValidationError(f"Unknown market: {market}")
        
        trading_hours = cls.TRADING_HOURS[market]
        market_tz = trading_hours['timezone']
        
        # 转换到市场时区
        market_dt = cls.convert_timezone(dt, dt.tzinfo.zone if dt.tzinfo else 'CST', market_tz)
        current_time = market_dt.time()
        
        # 检查各个交易时段
        for session_name, (start_str, end_str) in trading_hours.items():
            if session_name == 'timezone':
                continue
            
            start_time = datetime.strptime(start_str, '%H:%M').time()
            end_time = datetime.strptime(end_str, '%H:%M').time()
            
            if start_time <= current_time <= end_time:
                return True
        
        return False
    
    @classmethod
    def get_market_open_time(cls, market: str = 'A股', 
                           session: str = 'morning') -> Tuple[datetime, datetime]:
        """获取市场开盘时间"""
        if market not in cls.TRADING_HOURS:
            raise ValidationError(f"Unknown market: {market}")
        
        trading_hours = cls.TRADING_HOURS[market]
        
        if session not in trading_hours or session == 'timezone':
            available_sessions = [k for k in trading_hours.keys() if k != 'timezone']
            raise ValidationError(f"Unknown session: {session}. Available: {available_sessions}")
        
        start_str, end_str = trading_hours[session]
        market_tz = cls.TIMEZONE_MAP[trading_hours['timezone']]
        
        today = cls.get_trading_day()
        start_dt = datetime.combine(today, datetime.strptime(start_str, '%H:%M').time())
        end_dt = datetime.combine(today, datetime.strptime(end_str, '%H:%M').time())
        
        start_dt = start_dt.replace(tzinfo=market_tz)
        end_dt = end_dt.replace(tzinfo=market_tz)
        
        return start_dt, end_dt
    
    @classmethod
    def get_trading_days_between(cls, start_date: Union[str, date, datetime],
                               end_date: Union[str, date, datetime]) -> List[date]:
        """获取两个日期之间的交易日列表"""
        # 转换为date对象
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        elif isinstance(start_date, datetime):
            start_date = start_date.date()
        
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        elif isinstance(end_date, datetime):
            end_date = end_date.date()
        
        if start_date > end_date:
            raise ValidationError("Start date must be before end date")
        
        trading_days = []
        current_date = start_date
        
        while current_date <= end_date:
            if current_date.weekday() < 5:  # 工作日
                trading_days.append(current_date)
            current_date += timedelta(days=1)
        
        return trading_days
    
    @classmethod
    def add_trading_days(cls, start_date: Union[str, date, datetime], 
                        days: int) -> date:
        """在指定日期基础上增加交易日"""
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        elif isinstance(start_date, datetime):
            start_date = start_date.date()
        
        current_date = start_date
        added_days = 0
        
        while added_days < days:
            current_date += timedelta(days=1)
            if current_date.weekday() < 5:  # 工作日
                added_days += 1
        
        return current_date
    
    @classmethod
    def subtract_trading_days(cls, start_date: Union[str, date, datetime], 
                            days: int) -> date:
        """在指定日期基础上减少交易日"""
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        elif isinstance(start_date, datetime):
            start_date = start_date.date()
        
        current_date = start_date
        subtracted_days = 0
        
        while subtracted_days < days:
            current_date -= timedelta(days=1)
            if current_date.weekday() < 5:  # 工作日
                subtracted_days += 1
        
        return current_date
    
    @classmethod
    def get_week_range(cls, dt: Optional[datetime] = None) -> Tuple[date, date]:
        """获取指定日期所在周的起止日期（周一到周日）"""
        if dt is None:
            dt = cls.now()
        
        # 获取周一
        monday = dt.date() - timedelta(days=dt.weekday())
        # 获取周日
        sunday = monday + timedelta(days=6)
        
        return monday, sunday
    
    @classmethod
    def get_month_range(cls, dt: Optional[datetime] = None) -> Tuple[date, date]:
        """获取指定日期所在月的起止日期"""
        if dt is None:
            dt = cls.now()
        
        # 获取月初
        first_day = dt.date().replace(day=1)
        
        # 获取月末
        if dt.month == 12:
            next_month = dt.replace(year=dt.year + 1, month=1, day=1)
        else:
            next_month = dt.replace(month=dt.month + 1, day=1)
        
        last_day = (next_month - timedelta(days=1)).date()
        
        return first_day, last_day
    
    @classmethod
    def sleep_until(cls, target_time: datetime) -> None:
        """休眠到指定时间"""
        now = cls.utc_now()
        if target_time.tzinfo is None:
            target_time = target_time.replace(tzinfo=timezone.utc)
        
        sleep_seconds = (target_time - now).total_seconds()
        
        if sleep_seconds > 0:
            time.sleep(sleep_seconds)
    
    @classmethod
    def format_duration(cls, seconds: float) -> str:
        """格式化持续时间"""
        if seconds < 60:
            return f"{seconds:.2f}秒"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.2f}分钟"
        elif seconds < 86400:
            hours = seconds / 3600
            return f"{hours:.2f}小时"
        else:
            days = seconds / 86400
            return f"{days:.2f}天"
    
    @classmethod
    def get_age_in_seconds(cls, dt: datetime) -> float:
        """获取指定时间到现在的秒数"""
        now = cls.utc_now()
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        
        return (now - dt).total_seconds()


# 便捷函数
def now(timezone_name: str = 'CST') -> datetime:
    """获取当前时间"""
    return TimeUtils.now(timezone_name)


def utc_now() -> datetime:
    """获取UTC当前时间"""
    return TimeUtils.utc_now()


def timestamp_to_datetime(timestamp: Union[int, float], 
                         timezone_name: str = 'CST') -> datetime:
    """时间戳转datetime"""
    return TimeUtils.timestamp_to_datetime(timestamp, timezone_name)


def datetime_to_timestamp(dt: datetime) -> float:
    """datetime转时间戳"""
    return TimeUtils.datetime_to_timestamp(dt)


def is_trading_time(dt: Optional[datetime] = None, market: str = 'A股') -> bool:
    """判断是否为交易时间"""
    if dt is None:
        dt = now()
    return TimeUtils.is_trading_time(dt, market)


def get_trading_day(dt: Optional[datetime] = None) -> date:
    """获取交易日"""
    return TimeUtils.get_trading_day(dt)


def format_duration(seconds: float) -> str:
    """格式化持续时间"""
    return TimeUtils.format_duration(seconds)