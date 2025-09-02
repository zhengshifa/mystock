#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据验证模块

提供各种数据验证功能:
- 股票代码验证
- 日期验证
- 数据格式验证
- 配置验证
- 数值验证
"""

import re
from typing import Any, Dict, List, Optional, Union, Tuple
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
import json

from .exceptions import (
    ValidationError, SymbolValidationError, DateValidationError,
    DataFormatError, ConfigValidationError
)


class DataValidator:
    """数据验证器基类"""
    
    @staticmethod
    def validate_required(value: Any, field_name: str) -> None:
        """验证必填字段"""
        if value is None or (isinstance(value, str) and not value.strip()):
            raise ValidationError(
                f"Field '{field_name}' is required",
                field=field_name,
                value=value
            )
    
    @staticmethod
    def validate_type(value: Any, expected_type: type, field_name: str) -> None:
        """验证数据类型"""
        if not isinstance(value, expected_type):
            raise ValidationError(
                f"Field '{field_name}' must be of type {expected_type.__name__}",
                field=field_name,
                value=value,
                expected_format=expected_type.__name__
            )
    
    @staticmethod
    def validate_range(value: Union[int, float], min_val: Optional[Union[int, float]] = None,
                      max_val: Optional[Union[int, float]] = None, field_name: str = "value") -> None:
        """验证数值范围"""
        if min_val is not None and value < min_val:
            raise ValidationError(
                f"Field '{field_name}' must be >= {min_val}",
                field=field_name,
                value=value
            )
        if max_val is not None and value > max_val:
            raise ValidationError(
                f"Field '{field_name}' must be <= {max_val}",
                field=field_name,
                value=value
            )
    
    @staticmethod
    def validate_length(value: str, min_len: Optional[int] = None,
                       max_len: Optional[int] = None, field_name: str = "value") -> None:
        """验证字符串长度"""
        length = len(value)
        if min_len is not None and length < min_len:
            raise ValidationError(
                f"Field '{field_name}' must be at least {min_len} characters",
                field=field_name,
                value=value
            )
        if max_len is not None and length > max_len:
            raise ValidationError(
                f"Field '{field_name}' must be at most {max_len} characters",
                field=field_name,
                value=value
            )
    
    @staticmethod
    def validate_pattern(value: str, pattern: str, field_name: str = "value") -> None:
        """验证正则表达式模式"""
        if not re.match(pattern, value):
            raise ValidationError(
                f"Field '{field_name}' does not match required pattern",
                field=field_name,
                value=value,
                expected_format=pattern
            )


class SymbolValidator(DataValidator):
    """股票代码验证器"""
    
    # 股票代码模式
    PATTERNS = {
        'A股': r'^[0-9]{6}\.(SH|SZ)$',  # 000001.SZ, 600000.SH
        '港股': r'^[0-9]{5}\.(HK)$',     # 00700.HK
        '美股': r'^[A-Z]{1,5}$',         # AAPL, TSLA
        '期货': r'^[A-Z]{1,4}[0-9]{4}\.(SHF|DCE|CZC|INE)$',  # CU2312.SHF
        '基金': r'^[0-9]{6}\.(OF|SH|SZ)$',  # 000001.OF
    }
    
    # 交易所代码映射
    EXCHANGE_MAP = {
        'SH': '上海证券交易所',
        'SZ': '深圳证券交易所',
        'HK': '香港交易所',
        'SHF': '上海期货交易所',
        'DCE': '大连商品交易所',
        'CZC': '郑州商品交易所',
        'INE': '上海国际能源交易中心',
        'OF': '场外基金'
    }
    
    @classmethod
    def validate_symbol(cls, symbol: str) -> Tuple[str, str]:
        """验证股票代码
        
        Returns:
            Tuple[str, str]: (market_type, exchange)
        """
        if not symbol or not isinstance(symbol, str):
            raise SymbolValidationError(
                "Symbol must be a non-empty string",
                symbol=symbol
            )
        
        symbol = symbol.upper().strip()
        
        # 检查各种模式
        for market_type, pattern in cls.PATTERNS.items():
            if re.match(pattern, symbol):
                # 提取交易所代码
                if '.' in symbol:
                    exchange = symbol.split('.')[1]
                else:
                    exchange = 'US'  # 美股默认
                
                return market_type, exchange
        
        raise SymbolValidationError(
            f"Invalid symbol format: {symbol}",
            symbol=symbol
        )
    
    @classmethod
    def validate_symbol_list(cls, symbols: List[str]) -> List[Tuple[str, str, str]]:
        """验证股票代码列表
        
        Returns:
            List[Tuple[str, str, str]]: [(symbol, market_type, exchange), ...]
        """
        if not symbols:
            raise SymbolValidationError("Symbol list cannot be empty")
        
        results = []
        errors = []
        
        for symbol in symbols:
            try:
                market_type, exchange = cls.validate_symbol(symbol)
                results.append((symbol, market_type, exchange))
            except SymbolValidationError as e:
                errors.append(str(e))
        
        if errors:
            raise SymbolValidationError(
                f"Invalid symbols found: {'; '.join(errors)}",
                context={'invalid_symbols': errors}
            )
        
        return results
    
    @classmethod
    def normalize_symbol(cls, symbol: str) -> str:
        """标准化股票代码"""
        market_type, exchange = cls.validate_symbol(symbol)
        return symbol.upper().strip()
    
    @classmethod
    def get_market_info(cls, symbol: str) -> Dict[str, str]:
        """获取市场信息"""
        market_type, exchange = cls.validate_symbol(symbol)
        return {
            'symbol': symbol,
            'market_type': market_type,
            'exchange': exchange,
            'exchange_name': cls.EXCHANGE_MAP.get(exchange, exchange)
        }


class DateValidator(DataValidator):
    """日期验证器"""
    
    # 支持的日期格式
    DATE_FORMATS = [
        '%Y-%m-%d',
        '%Y%m%d',
        '%Y/%m/%d',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M:%S.%f',
        '%Y%m%d %H%M%S'
    ]
    
    @classmethod
    def validate_date(cls, date_str: str, date_format: Optional[str] = None) -> datetime:
        """验证日期字符串"""
        if not date_str or not isinstance(date_str, str):
            raise DateValidationError(
                "Date must be a non-empty string",
                date_value=date_str
            )
        
        date_str = date_str.strip()
        
        # 如果指定了格式，直接使用
        if date_format:
            try:
                return datetime.strptime(date_str, date_format)
            except ValueError as e:
                raise DateValidationError(
                    f"Date '{date_str}' does not match format '{date_format}'",
                    date_value=date_str,
                    date_format=date_format,
                    cause=e
                )
        
        # 尝试所有支持的格式
        for fmt in cls.DATE_FORMATS:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        raise DateValidationError(
            f"Date '{date_str}' does not match any supported format",
            date_value=date_str,
            validation_rules=cls.DATE_FORMATS
        )
    
    @classmethod
    def validate_date_range(cls, start_date: str, end_date: str) -> Tuple[datetime, datetime]:
        """验证日期范围"""
        start_dt = cls.validate_date(start_date)
        end_dt = cls.validate_date(end_date)
        
        if start_dt > end_dt:
            raise DateValidationError(
                f"Start date '{start_date}' must be before end date '{end_date}'",
                context={
                    'start_date': start_date,
                    'end_date': end_date
                }
            )
        
        return start_dt, end_dt
    
    @classmethod
    def validate_trading_date(cls, date_str: str) -> datetime:
        """验证交易日期（工作日）"""
        dt = cls.validate_date(date_str)
        
        # 检查是否为工作日（周一到周五）
        if dt.weekday() >= 5:  # 5=Saturday, 6=Sunday
            raise DateValidationError(
                f"Date '{date_str}' is not a trading day (weekend)",
                date_value=date_str
            )
        
        return dt
    
    @classmethod
    def format_date(cls, dt: datetime, format_str: str = '%Y-%m-%d') -> str:
        """格式化日期"""
        return dt.strftime(format_str)
    
    @classmethod
    def normalize_date(cls, date_str: str) -> str:
        """标准化日期格式"""
        dt = cls.validate_date(date_str)
        return cls.format_date(dt)


class DataFormatValidator(DataValidator):
    """数据格式验证器"""
    
    @staticmethod
    def validate_json(data: str) -> Dict[str, Any]:
        """验证JSON格式"""
        try:
            return json.loads(data)
        except json.JSONDecodeError as e:
            raise DataFormatError(
                f"Invalid JSON format: {str(e)}",
                data_type='json',
                cause=e
            )
    
    @staticmethod
    def validate_decimal(value: Union[str, int, float], precision: Optional[int] = None) -> Decimal:
        """验证decimal格式"""
        try:
            decimal_val = Decimal(str(value))
            
            if precision is not None:
                # 检查小数位数
                if decimal_val.as_tuple().exponent < -precision:
                    raise DataFormatError(
                        f"Decimal precision exceeds {precision} places",
                        data_type='decimal',
                        expected_schema={'precision': precision}
                    )
            
            return decimal_val
        except (InvalidOperation, ValueError) as e:
            raise DataFormatError(
                f"Invalid decimal format: {value}",
                data_type='decimal',
                cause=e
            )
    
    @staticmethod
    def validate_price(price: Union[str, int, float]) -> Decimal:
        """验证价格格式"""
        decimal_price = DataFormatValidator.validate_decimal(price, precision=4)
        
        if decimal_price < 0:
            raise ValidationError(
                "Price cannot be negative",
                field='price',
                value=price
            )
        
        return decimal_price
    
    @staticmethod
    def validate_volume(volume: Union[str, int]) -> int:
        """验证成交量格式"""
        try:
            vol = int(volume)
            if vol < 0:
                raise ValidationError(
                    "Volume cannot be negative",
                    field='volume',
                    value=volume
                )
            return vol
        except (ValueError, TypeError) as e:
            raise DataFormatError(
                f"Invalid volume format: {volume}",
                data_type='volume',
                cause=e
            )
    
    @staticmethod
    def validate_percentage(percentage: Union[str, int, float]) -> float:
        """验证百分比格式"""
        try:
            pct = float(percentage)
            # 百分比通常在-100到100之间
            if not -100 <= pct <= 100:
                raise ValidationError(
                    "Percentage must be between -100 and 100",
                    field='percentage',
                    value=percentage
                )
            return pct
        except (ValueError, TypeError) as e:
            raise DataFormatError(
                f"Invalid percentage format: {percentage}",
                data_type='percentage',
                cause=e
            )


class ConfigValidator(DataValidator):
    """配置验证器"""
    
    @staticmethod
    def validate_config_schema(config: Dict[str, Any], schema: Dict[str, Any]) -> None:
        """验证配置模式"""
        errors = []
        
        # 检查必填字段
        required_fields = schema.get('required', [])
        for field in required_fields:
            if field not in config:
                errors.append(f"Missing required field: {field}")
        
        # 检查字段类型
        properties = schema.get('properties', {})
        for field, field_schema in properties.items():
            if field in config:
                value = config[field]
                expected_type = field_schema.get('type')
                
                if expected_type == 'string' and not isinstance(value, str):
                    errors.append(f"Field '{field}' must be string")
                elif expected_type == 'integer' and not isinstance(value, int):
                    errors.append(f"Field '{field}' must be integer")
                elif expected_type == 'number' and not isinstance(value, (int, float)):
                    errors.append(f"Field '{field}' must be number")
                elif expected_type == 'boolean' and not isinstance(value, bool):
                    errors.append(f"Field '{field}' must be boolean")
                elif expected_type == 'array' and not isinstance(value, list):
                    errors.append(f"Field '{field}' must be array")
                elif expected_type == 'object' and not isinstance(value, dict):
                    errors.append(f"Field '{field}' must be object")
        
        if errors:
            raise ConfigValidationError(
                "Configuration validation failed",
                validation_errors=errors
            )
    
    @staticmethod
    def validate_database_config(config: Dict[str, Any]) -> None:
        """验证数据库配置"""
        schema = {
            'required': ['host', 'port', 'database'],
            'properties': {
                'host': {'type': 'string'},
                'port': {'type': 'integer'},
                'database': {'type': 'string'},
                'username': {'type': 'string'},
                'password': {'type': 'string'},
                'max_connections': {'type': 'integer'},
                'timeout': {'type': 'number'}
            }
        }
        
        ConfigValidator.validate_config_schema(config, schema)
        
        # 额外验证
        if 'port' in config:
            port = config['port']
            if not 1 <= port <= 65535:
                raise ConfigValidationError(
                    f"Invalid port number: {port}",
                    config_key='port',
                    actual_value=port
                )
    
    @staticmethod
    def validate_api_config(config: Dict[str, Any]) -> None:
        """验证API配置"""
        schema = {
            'required': ['base_url'],
            'properties': {
                'base_url': {'type': 'string'},
                'api_key': {'type': 'string'},
                'timeout': {'type': 'number'},
                'max_retries': {'type': 'integer'},
                'rate_limit': {'type': 'integer'}
            }
        }
        
        ConfigValidator.validate_config_schema(config, schema)
        
        # 验证URL格式
        if 'base_url' in config:
            url = config['base_url']
            if not url.startswith(('http://', 'https://')):
                raise ConfigValidationError(
                    f"Invalid URL format: {url}",
                    config_key='base_url',
                    actual_value=url
                )


# 便捷验证函数
def validate_symbol(symbol: str) -> Tuple[str, str]:
    """验证股票代码"""
    return SymbolValidator.validate_symbol(symbol)


def validate_date(date_str: str) -> datetime:
    """验证日期"""
    return DateValidator.validate_date(date_str)


def validate_date_range(start_date: str, end_date: str) -> Tuple[datetime, datetime]:
    """验证日期范围"""
    return DateValidator.validate_date_range(start_date, end_date)


def validate_price(price: Union[str, int, float]) -> Decimal:
    """验证价格"""
    return DataFormatValidator.validate_price(price)


def validate_volume(volume: Union[str, int]) -> int:
    """验证成交量"""
    return DataFormatValidator.validate_volume(volume)


def validate_config(config: Dict[str, Any], config_type: str) -> None:
    """验证配置"""
    if config_type == 'database':
        ConfigValidator.validate_database_config(config)
    elif config_type == 'api':
        ConfigValidator.validate_api_config(config)
    else:
        raise ValidationError(f"Unknown config type: {config_type}")