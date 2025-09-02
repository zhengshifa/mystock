#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
异常处理模块

定义项目中使用的各种异常类:
- 基础异常类
- 数据库异常
- API异常
- 配置异常
- 同步异常
- 验证异常
"""

from typing import Any, Dict, Optional, List
from datetime import datetime


class StockDataError(Exception):
    """股票数据系统基础异常类"""
    
    def __init__(self, message: str, error_code: Optional[str] = None, 
                 context: Optional[Dict[str, Any]] = None, cause: Optional[Exception] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or {}
        self.cause = cause
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'error_type': self.__class__.__name__,
            'message': self.message,
            'error_code': self.error_code,
            'context': self.context,
            'timestamp': self.timestamp,
            'cause': str(self.cause) if self.cause else None
        }
    
    def __str__(self) -> str:
        base_msg = f"{self.__class__.__name__}: {self.message}"
        if self.error_code:
            base_msg += f" (Code: {self.error_code})"
        if self.context:
            base_msg += f" Context: {self.context}"
        return base_msg


class DatabaseError(StockDataError):
    """数据库相关异常"""
    
    def __init__(self, message: str, operation: Optional[str] = None, 
                 collection: Optional[str] = None, query: Optional[Dict[str, Any]] = None,
                 **kwargs):
        context = {
            'operation': operation,
            'collection': collection,
            'query': query
        }
        context.update(kwargs.get('context', {}))
        super().__init__(message, context=context, **kwargs)
        self.operation = operation
        self.collection = collection
        self.query = query


class ConnectionError(DatabaseError):
    """数据库连接异常"""
    
    def __init__(self, message: str, host: Optional[str] = None, 
                 port: Optional[int] = None, database: Optional[str] = None, **kwargs):
        context = {
            'host': host,
            'port': port,
            'database': database
        }
        context.update(kwargs.get('context', {}))
        super().__init__(message, context=context, **kwargs)
        self.host = host
        self.port = port
        self.database = database


class QueryError(DatabaseError):
    """数据库查询异常"""
    
    def __init__(self, message: str, query_type: Optional[str] = None, 
                 execution_time: Optional[float] = None, **kwargs):
        context = {
            'query_type': query_type,
            'execution_time': execution_time
        }
        context.update(kwargs.get('context', {}))
        super().__init__(message, context=context, **kwargs)
        self.query_type = query_type
        self.execution_time = execution_time


class APIError(StockDataError):
    """API相关异常"""
    
    def __init__(self, message: str, api_name: Optional[str] = None,
                 endpoint: Optional[str] = None, status_code: Optional[int] = None,
                 response_data: Optional[Dict[str, Any]] = None, **kwargs):
        context = {
            'api_name': api_name,
            'endpoint': endpoint,
            'status_code': status_code,
            'response_data': response_data
        }
        context.update(kwargs.get('context', {}))
        super().__init__(message, context=context, **kwargs)
        self.api_name = api_name
        self.endpoint = endpoint
        self.status_code = status_code
        self.response_data = response_data


class AuthenticationError(APIError):
    """API认证异常"""
    
    def __init__(self, message: str, auth_type: Optional[str] = None, **kwargs):
        context = {'auth_type': auth_type}
        context.update(kwargs.get('context', {}))
        super().__init__(message, context=context, **kwargs)
        self.auth_type = auth_type


class RateLimitError(APIError):
    """API限流异常"""
    
    def __init__(self, message: str, limit: Optional[int] = None,
                 reset_time: Optional[str] = None, **kwargs):
        context = {
            'limit': limit,
            'reset_time': reset_time
        }
        context.update(kwargs.get('context', {}))
        super().__init__(message, context=context, **kwargs)
        self.limit = limit
        self.reset_time = reset_time


class TimeoutError(APIError):
    """API超时异常"""
    
    def __init__(self, message: str, timeout_duration: Optional[float] = None, **kwargs):
        context = {'timeout_duration': timeout_duration}
        context.update(kwargs.get('context', {}))
        super().__init__(message, context=context, **kwargs)
        self.timeout_duration = timeout_duration


class ConfigError(StockDataError):
    """配置相关异常"""
    
    def __init__(self, message: str, config_key: Optional[str] = None,
                 config_file: Optional[str] = None, expected_type: Optional[str] = None,
                 actual_value: Optional[Any] = None, **kwargs):
        context = {
            'config_key': config_key,
            'config_file': config_file,
            'expected_type': expected_type,
            'actual_value': actual_value
        }
        context.update(kwargs.get('context', {}))
        super().__init__(message, context=context, **kwargs)
        self.config_key = config_key
        self.config_file = config_file
        self.expected_type = expected_type
        self.actual_value = actual_value


class ConfigValidationError(ConfigError):
    """配置验证异常"""
    
    def __init__(self, message: str, validation_errors: Optional[List[str]] = None, **kwargs):
        context = {'validation_errors': validation_errors or []}
        context.update(kwargs.get('context', {}))
        super().__init__(message, context=context, **kwargs)
        self.validation_errors = validation_errors or []


class ConfigNotFoundError(ConfigError):
    """配置文件未找到异常"""
    pass


class SyncError(StockDataError):
    """数据同步相关异常"""
    
    def __init__(self, message: str, sync_type: Optional[str] = None,
                 data_type: Optional[str] = None, symbols: Optional[List[str]] = None,
                 start_date: Optional[str] = None, end_date: Optional[str] = None, **kwargs):
        context = {
            'sync_type': sync_type,
            'data_type': data_type,
            'symbols': symbols,
            'start_date': start_date,
            'end_date': end_date
        }
        context.update(kwargs.get('context', {}))
        super().__init__(message, context=context, **kwargs)
        self.sync_type = sync_type
        self.data_type = data_type
        self.symbols = symbols
        self.start_date = start_date
        self.end_date = end_date


class SyncTimeoutError(SyncError):
    """同步超时异常"""
    
    def __init__(self, message: str, timeout_duration: Optional[float] = None, **kwargs):
        context = {'timeout_duration': timeout_duration}
        context.update(kwargs.get('context', {}))
        super().__init__(message, context=context, **kwargs)
        self.timeout_duration = timeout_duration


class SyncConflictError(SyncError):
    """同步冲突异常"""
    
    def __init__(self, message: str, conflicting_sync: Optional[str] = None, **kwargs):
        context = {'conflicting_sync': conflicting_sync}
        context.update(kwargs.get('context', {}))
        super().__init__(message, context=context, **kwargs)
        self.conflicting_sync = conflicting_sync


class DataIntegrityError(SyncError):
    """数据完整性异常"""
    
    def __init__(self, message: str, missing_data: Optional[List[Dict[str, Any]]] = None,
                 corrupted_data: Optional[List[Dict[str, Any]]] = None, **kwargs):
        context = {
            'missing_data': missing_data or [],
            'corrupted_data': corrupted_data or []
        }
        context.update(kwargs.get('context', {}))
        super().__init__(message, context=context, **kwargs)
        self.missing_data = missing_data or []
        self.corrupted_data = corrupted_data or []


class ValidationError(StockDataError):
    """数据验证异常"""
    
    def __init__(self, message: str, field: Optional[str] = None,
                 value: Optional[Any] = None, expected_format: Optional[str] = None,
                 validation_rules: Optional[List[str]] = None, **kwargs):
        context = {
            'field': field,
            'value': value,
            'expected_format': expected_format,
            'validation_rules': validation_rules or []
        }
        context.update(kwargs.get('context', {}))
        super().__init__(message, context=context, **kwargs)
        self.field = field
        self.value = value
        self.expected_format = expected_format
        self.validation_rules = validation_rules or []


class DataFormatError(ValidationError):
    """数据格式异常"""
    
    def __init__(self, message: str, data_type: Optional[str] = None,
                 expected_schema: Optional[Dict[str, Any]] = None, **kwargs):
        context = {
            'data_type': data_type,
            'expected_schema': expected_schema
        }
        context.update(kwargs.get('context', {}))
        super().__init__(message, context=context, **kwargs)
        self.data_type = data_type
        self.expected_schema = expected_schema


class SymbolValidationError(ValidationError):
    """股票代码验证异常"""
    
    def __init__(self, message: str, symbol: Optional[str] = None,
                 market: Optional[str] = None, **kwargs):
        context = {
            'symbol': symbol,
            'market': market
        }
        context.update(kwargs.get('context', {}))
        super().__init__(message, context=context, **kwargs)
        self.symbol = symbol
        self.market = market


class DateValidationError(ValidationError):
    """日期验证异常"""
    
    def __init__(self, message: str, date_value: Optional[str] = None,
                 date_format: Optional[str] = None, **kwargs):
        context = {
            'date_value': date_value,
            'date_format': date_format
        }
        context.update(kwargs.get('context', {}))
        super().__init__(message, context=context, **kwargs)
        self.date_value = date_value
        self.date_format = date_format


class ProcessingError(StockDataError):
    """数据处理异常"""
    
    def __init__(self, message: str, processor: Optional[str] = None,
                 stage: Optional[str] = None, data_count: Optional[int] = None, **kwargs):
        context = {
            'processor': processor,
            'stage': stage,
            'data_count': data_count
        }
        context.update(kwargs.get('context', {}))
        super().__init__(message, context=context, **kwargs)
        self.processor = processor
        self.stage = stage
        self.data_count = data_count


class DataProcessingError(ProcessingError):
    """数据处理异常（继承自ProcessingError以保持兼容性）"""
    pass


class TransformationError(ProcessingError):
    """数据转换异常"""
    
    def __init__(self, message: str, source_format: Optional[str] = None,
                 target_format: Optional[str] = None, **kwargs):
        context = {
            'source_format': source_format,
            'target_format': target_format
        }
        context.update(kwargs.get('context', {}))
        super().__init__(message, context=context, **kwargs)
        self.source_format = source_format
        self.target_format = target_format


class ResourceError(StockDataError):
    """资源相关异常"""
    
    def __init__(self, message: str, resource_type: Optional[str] = None,
                 resource_name: Optional[str] = None, **kwargs):
        context = {
            'resource_type': resource_type,
            'resource_name': resource_name
        }
        context.update(kwargs.get('context', {}))
        super().__init__(message, context=context, **kwargs)
        self.resource_type = resource_type
        self.resource_name = resource_name


class ResourceNotFoundError(ResourceError):
    """资源未找到异常"""
    pass


class ResourceExhaustedError(ResourceError):
    """资源耗尽异常"""
    
    def __init__(self, message: str, limit: Optional[int] = None,
                 current_usage: Optional[int] = None, **kwargs):
        context = {
            'limit': limit,
            'current_usage': current_usage
        }
        context.update(kwargs.get('context', {}))
        super().__init__(message, context=context, **kwargs)
        self.limit = limit
        self.current_usage = current_usage


class PermissionError(StockDataError):
    """权限异常"""
    
    def __init__(self, message: str, required_permission: Optional[str] = None,
                 user: Optional[str] = None, resource: Optional[str] = None, **kwargs):
        context = {
            'required_permission': required_permission,
            'user': user,
            'resource': resource
        }
        context.update(kwargs.get('context', {}))
        super().__init__(message, context=context, **kwargs)
        self.required_permission = required_permission
        self.user = user
        self.resource = resource


# 异常处理工具函数
def handle_exception(func):
    """异常处理装饰器"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except StockDataError:
            # 重新抛出自定义异常
            raise
        except Exception as e:
            # 将其他异常包装为StockDataError
            raise StockDataError(
                message=f"Unexpected error in {func.__name__}: {str(e)}",
                context={
                    'function': func.__name__,
                    'args_count': len(args),
                    'kwargs_count': len(kwargs)
                },
                cause=e
            )
    return wrapper


def create_error_context(operation: str, **kwargs) -> Dict[str, Any]:
    """创建错误上下文"""
    context = {
        'operation': operation,
        'timestamp': datetime.now().isoformat()
    }
    context.update(kwargs)
    return context


def format_error_message(error: StockDataError) -> str:
    """格式化错误消息"""
    message_parts = [f"[{error.__class__.__name__}] {error.message}"]
    
    if error.error_code:
        message_parts.append(f"Code: {error.error_code}")
    
    if error.context:
        context_str = ", ".join([f"{k}={v}" for k, v in error.context.items() if v is not None])
        if context_str:
            message_parts.append(f"Context: {context_str}")
    
    if error.cause:
        message_parts.append(f"Caused by: {error.cause}")
    
    return " | ".join(message_parts)