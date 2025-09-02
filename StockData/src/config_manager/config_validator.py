#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置验证器模块

提供配置数据验证功能:
- 数据类型验证
- 值范围验证
- 必填字段验证
- 自定义验证规则
- 配置模式验证
"""

import re
from typing import Dict, Any, List, Optional, Union, Callable, Type
from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path
import ipaddress
from urllib.parse import urlparse

from ..utils import get_logger, ValidationError as BaseValidationError


class ValidationError(BaseValidationError):
    """配置验证错误"""
    pass


class ValidationType(Enum):
    """验证类型枚举"""
    TYPE = "type"              # 类型验证
    REQUIRED = "required"      # 必填验证
    RANGE = "range"            # 范围验证
    LENGTH = "length"          # 长度验证
    PATTERN = "pattern"        # 正则验证
    ENUM = "enum"              # 枚举验证
    CUSTOM = "custom"          # 自定义验证
    NESTED = "nested"          # 嵌套验证
    LIST = "list"              # 列表验证
    DICT = "dict"              # 字典验证


@dataclass
class ValidationRule:
    """验证规则"""
    field_path: str  # 字段路径，如 "database.host" 或 "api.endpoints[0].url"
    validation_type: ValidationType
    
    # 类型验证
    expected_type: Optional[Type] = None
    allow_none: bool = False
    
    # 必填验证
    required: bool = False
    
    # 范围验证
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    
    # 长度验证
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    
    # 正则验证
    pattern: Optional[str] = None
    pattern_flags: int = 0
    
    # 枚举验证
    allowed_values: Optional[List[Any]] = None
    
    # 自定义验证
    custom_validator: Optional[Callable[[Any], bool]] = None
    custom_message: Optional[str] = None
    
    # 嵌套验证
    nested_rules: Optional[List['ValidationRule']] = None
    
    # 列表验证
    list_item_rules: Optional[List['ValidationRule']] = None
    
    # 字典验证
    dict_key_rules: Optional[List['ValidationRule']] = None
    dict_value_rules: Optional[List['ValidationRule']] = None
    
    # 验证选项
    stop_on_first_error: bool = True
    error_message: Optional[str] = None


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    field_errors: Dict[str, List[str]] = field(default_factory=dict)
    
    def add_error(self, field_path: str, message: str):
        """添加错误"""
        self.is_valid = False
        self.errors.append(f"{field_path}: {message}")
        
        if field_path not in self.field_errors:
            self.field_errors[field_path] = []
        self.field_errors[field_path].append(message)
    
    def add_warning(self, field_path: str, message: str):
        """添加警告"""
        self.warnings.append(f"{field_path}: {message}")
    
    def merge(self, other: 'ValidationResult'):
        """合并验证结果"""
        if not other.is_valid:
            self.is_valid = False
        
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        
        for field_path, errors in other.field_errors.items():
            if field_path not in self.field_errors:
                self.field_errors[field_path] = []
            self.field_errors[field_path].extend(errors)


class ConfigValidator:
    """配置验证器"""
    
    def __init__(self, logger_name: str = "ConfigValidator"):
        self.logger = get_logger(logger_name)
        self.rules: List[ValidationRule] = []
        
        # 内置验证器
        self._builtin_validators = {
            'email': self._validate_email,
            'url': self._validate_url,
            'ip': self._validate_ip,
            'port': self._validate_port,
            'path': self._validate_path,
            'file_exists': self._validate_file_exists,
            'dir_exists': self._validate_dir_exists,
            'positive': lambda x: isinstance(x, (int, float)) and x > 0,
            'non_negative': lambda x: isinstance(x, (int, float)) and x >= 0,
            'non_empty_string': lambda x: isinstance(x, str) and len(x.strip()) > 0
        }
    
    def add_rule(self, rule: ValidationRule):
        """添加验证规则"""
        self.rules.append(rule)
        self.logger.debug(f"Added validation rule for field: {rule.field_path}")
    
    def add_rules(self, rules: List[ValidationRule]):
        """批量添加验证规则"""
        for rule in rules:
            self.add_rule(rule)
    
    def validate(self, config: Dict[str, Any], 
                raise_on_error: bool = False) -> ValidationResult:
        """验证配置
        
        Args:
            config: 要验证的配置字典
            raise_on_error: 是否在验证失败时抛出异常
            
        Returns:
            验证结果
        """
        result = ValidationResult(is_valid=True)
        
        for rule in self.rules:
            try:
                field_result = self._validate_field(config, rule)
                result.merge(field_result)
                
                if not field_result.is_valid and rule.stop_on_first_error:
                    break
                    
            except Exception as e:
                self.logger.error(f"Error validating field {rule.field_path}: {e}")
                result.add_error(rule.field_path, f"Validation error: {e}")
        
        if raise_on_error and not result.is_valid:
            error_msg = "\n".join(result.errors)
            raise ValidationError(f"Config validation failed:\n{error_msg}")
        
        self.logger.info(f"Config validation completed. Valid: {result.is_valid}, "
                        f"Errors: {len(result.errors)}, Warnings: {len(result.warnings)}")
        
        return result
    
    def validate_schema(self, config: Dict[str, Any], 
                       schema: Dict[str, Any]) -> ValidationResult:
        """根据模式验证配置
        
        Args:
            config: 要验证的配置
            schema: 验证模式
            
        Returns:
            验证结果
        """
        rules = self._schema_to_rules(schema)
        original_rules = self.rules.copy()
        
        try:
            self.rules = rules
            return self.validate(config)
        finally:
            self.rules = original_rules
    
    def _validate_field(self, config: Dict[str, Any], 
                       rule: ValidationRule) -> ValidationResult:
        """验证单个字段"""
        result = ValidationResult(is_valid=True)
        
        try:
            # 获取字段值
            value = self._get_field_value(config, rule.field_path)
            
            # 必填验证
            if rule.required and value is None:
                result.add_error(rule.field_path, "Field is required")
                return result
            
            # 如果值为None且允许None，跳过其他验证
            if value is None and rule.allow_none:
                return result
            
            # 类型验证
            if rule.validation_type == ValidationType.TYPE or rule.expected_type:
                if not self._validate_type(value, rule.expected_type, rule.allow_none):
                    result.add_error(rule.field_path, 
                                   f"Expected type {rule.expected_type.__name__}, got {type(value).__name__}")
            
            # 范围验证
            elif rule.validation_type == ValidationType.RANGE:
                if not self._validate_range(value, rule.min_value, rule.max_value):
                    result.add_error(rule.field_path, 
                                   f"Value {value} is out of range [{rule.min_value}, {rule.max_value}]")
            
            # 长度验证
            elif rule.validation_type == ValidationType.LENGTH:
                if not self._validate_length(value, rule.min_length, rule.max_length):
                    result.add_error(rule.field_path, 
                                   f"Length {len(value)} is out of range [{rule.min_length}, {rule.max_length}]")
            
            # 正则验证
            elif rule.validation_type == ValidationType.PATTERN:
                if not self._validate_pattern(value, rule.pattern, rule.pattern_flags):
                    result.add_error(rule.field_path, 
                                   f"Value '{value}' does not match pattern '{rule.pattern}'")
            
            # 枚举验证
            elif rule.validation_type == ValidationType.ENUM:
                if not self._validate_enum(value, rule.allowed_values):
                    result.add_error(rule.field_path, 
                                   f"Value '{value}' is not in allowed values: {rule.allowed_values}")
            
            # 自定义验证
            elif rule.validation_type == ValidationType.CUSTOM:
                if not self._validate_custom(value, rule.custom_validator):
                    message = rule.custom_message or f"Custom validation failed for value '{value}'"
                    result.add_error(rule.field_path, message)
            
            # 嵌套验证
            elif rule.validation_type == ValidationType.NESTED:
                if isinstance(value, dict) and rule.nested_rules:
                    nested_result = self._validate_nested(value, rule.nested_rules)
                    result.merge(nested_result)
            
            # 列表验证
            elif rule.validation_type == ValidationType.LIST:
                if isinstance(value, list) and rule.list_item_rules:
                    list_result = self._validate_list(value, rule.list_item_rules, rule.field_path)
                    result.merge(list_result)
            
            # 字典验证
            elif rule.validation_type == ValidationType.DICT:
                if isinstance(value, dict):
                    dict_result = self._validate_dict(value, rule.dict_key_rules, 
                                                    rule.dict_value_rules, rule.field_path)
                    result.merge(dict_result)
            
        except Exception as e:
            result.add_error(rule.field_path, f"Validation error: {e}")
        
        return result
    
    def _get_field_value(self, config: Dict[str, Any], field_path: str) -> Any:
        """获取字段值"""
        parts = field_path.split('.')
        value = config
        
        for part in parts:
            # 处理数组索引，如 "endpoints[0]"
            if '[' in part and ']' in part:
                key, index_str = part.split('[', 1)
                index = int(index_str.rstrip(']'))
                
                if key and key in value:
                    value = value[key]
                
                if isinstance(value, list) and 0 <= index < len(value):
                    value = value[index]
                else:
                    return None
            else:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return None
        
        return value
    
    def _validate_type(self, value: Any, expected_type: Type, allow_none: bool) -> bool:
        """验证类型"""
        if value is None:
            return allow_none
        
        if expected_type is None:
            return True
        
        return isinstance(value, expected_type)
    
    def _validate_range(self, value: Any, min_value: Optional[Union[int, float]], 
                       max_value: Optional[Union[int, float]]) -> bool:
        """验证范围"""
        if not isinstance(value, (int, float)):
            return False
        
        if min_value is not None and value < min_value:
            return False
        
        if max_value is not None and value > max_value:
            return False
        
        return True
    
    def _validate_length(self, value: Any, min_length: Optional[int], 
                        max_length: Optional[int]) -> bool:
        """验证长度"""
        if not hasattr(value, '__len__'):
            return False
        
        length = len(value)
        
        if min_length is not None and length < min_length:
            return False
        
        if max_length is not None and length > max_length:
            return False
        
        return True
    
    def _validate_pattern(self, value: Any, pattern: str, flags: int = 0) -> bool:
        """验证正则模式"""
        if not isinstance(value, str):
            return False
        
        if not pattern:
            return True
        
        try:
            return bool(re.match(pattern, value, flags))
        except re.error:
            return False
    
    def _validate_enum(self, value: Any, allowed_values: List[Any]) -> bool:
        """验证枚举值"""
        if not allowed_values:
            return True
        
        return value in allowed_values
    
    def _validate_custom(self, value: Any, validator: Callable[[Any], bool]) -> bool:
        """自定义验证"""
        if not validator:
            return True
        
        try:
            return validator(value)
        except Exception:
            return False
    
    def _validate_nested(self, value: Dict[str, Any], 
                        nested_rules: List[ValidationRule]) -> ValidationResult:
        """验证嵌套对象"""
        result = ValidationResult(is_valid=True)
        
        for rule in nested_rules:
            field_result = self._validate_field(value, rule)
            result.merge(field_result)
        
        return result
    
    def _validate_list(self, value: List[Any], item_rules: List[ValidationRule], 
                      field_path: str) -> ValidationResult:
        """验证列表"""
        result = ValidationResult(is_valid=True)
        
        for i, item in enumerate(value):
            for rule in item_rules:
                # 创建新的规则，更新字段路径
                item_rule = ValidationRule(
                    field_path=f"{field_path}[{i}].{rule.field_path}" if rule.field_path else f"{field_path}[{i}]",
                    validation_type=rule.validation_type,
                    **{k: v for k, v in rule.__dict__.items() if k not in ['field_path', 'validation_type']}
                )
                
                if isinstance(item, dict):
                    item_result = self._validate_field(item, item_rule)
                else:
                    # 对于非字典项，直接验证值
                    item_result = self._validate_field({rule.field_path or 'value': item}, item_rule)
                
                result.merge(item_result)
        
        return result
    
    def _validate_dict(self, value: Dict[str, Any], key_rules: Optional[List[ValidationRule]], 
                      value_rules: Optional[List[ValidationRule]], field_path: str) -> ValidationResult:
        """验证字典"""
        result = ValidationResult(is_valid=True)
        
        for key, val in value.items():
            # 验证键
            if key_rules:
                for rule in key_rules:
                    key_rule = ValidationRule(
                        field_path=f"{field_path}.{key}.__key__",
                        validation_type=rule.validation_type,
                        **{k: v for k, v in rule.__dict__.items() if k not in ['field_path', 'validation_type']}
                    )
                    key_result = self._validate_field({'__key__': key}, key_rule)
                    result.merge(key_result)
            
            # 验证值
            if value_rules:
                for rule in value_rules:
                    val_rule = ValidationRule(
                        field_path=f"{field_path}.{key}",
                        validation_type=rule.validation_type,
                        **{k: v for k, v in rule.__dict__.items() if k not in ['field_path', 'validation_type']}
                    )
                    val_result = self._validate_field({key: val}, val_rule)
                    result.merge(val_result)
        
        return result
    
    def _schema_to_rules(self, schema: Dict[str, Any], 
                        prefix: str = "") -> List[ValidationRule]:
        """将模式转换为验证规则"""
        rules = []
        
        for field, field_schema in schema.items():
            field_path = f"{prefix}.{field}" if prefix else field
            
            if isinstance(field_schema, dict):
                # 类型验证
                if 'type' in field_schema:
                    type_map = {
                        'string': str,
                        'integer': int,
                        'number': float,
                        'boolean': bool,
                        'array': list,
                        'object': dict
                    }
                    expected_type = type_map.get(field_schema['type'])
                    if expected_type:
                        rules.append(ValidationRule(
                            field_path=field_path,
                            validation_type=ValidationType.TYPE,
                            expected_type=expected_type,
                            required=field_schema.get('required', False),
                            allow_none=field_schema.get('nullable', False)
                        ))
                
                # 范围验证
                if 'minimum' in field_schema or 'maximum' in field_schema:
                    rules.append(ValidationRule(
                        field_path=field_path,
                        validation_type=ValidationType.RANGE,
                        min_value=field_schema.get('minimum'),
                        max_value=field_schema.get('maximum')
                    ))
                
                # 长度验证
                if 'minLength' in field_schema or 'maxLength' in field_schema:
                    rules.append(ValidationRule(
                        field_path=field_path,
                        validation_type=ValidationType.LENGTH,
                        min_length=field_schema.get('minLength'),
                        max_length=field_schema.get('maxLength')
                    ))
                
                # 正则验证
                if 'pattern' in field_schema:
                    rules.append(ValidationRule(
                        field_path=field_path,
                        validation_type=ValidationType.PATTERN,
                        pattern=field_schema['pattern']
                    ))
                
                # 枚举验证
                if 'enum' in field_schema:
                    rules.append(ValidationRule(
                        field_path=field_path,
                        validation_type=ValidationType.ENUM,
                        allowed_values=field_schema['enum']
                    ))
                
                # 嵌套对象
                if 'properties' in field_schema:
                    nested_rules = self._schema_to_rules(field_schema['properties'], field_path)
                    rules.append(ValidationRule(
                        field_path=field_path,
                        validation_type=ValidationType.NESTED,
                        nested_rules=nested_rules
                    ))
        
        return rules
    
    # 内置验证器
    def _validate_email(self, value: str) -> bool:
        """验证邮箱格式"""
        if not isinstance(value, str):
            return False
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, value))
    
    def _validate_url(self, value: str) -> bool:
        """验证URL格式"""
        if not isinstance(value, str):
            return False
        
        try:
            result = urlparse(value)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    def _validate_ip(self, value: str) -> bool:
        """验证IP地址"""
        if not isinstance(value, str):
            return False
        
        try:
            ipaddress.ip_address(value)
            return True
        except ValueError:
            return False
    
    def _validate_port(self, value: int) -> bool:
        """验证端口号"""
        return isinstance(value, int) and 1 <= value <= 65535
    
    def _validate_path(self, value: str) -> bool:
        """验证路径格式"""
        if not isinstance(value, str):
            return False
        
        try:
            Path(value)
            return True
        except Exception:
            return False
    
    def _validate_file_exists(self, value: str) -> bool:
        """验证文件是否存在"""
        if not isinstance(value, str):
            return False
        
        return Path(value).is_file()
    
    def _validate_dir_exists(self, value: str) -> bool:
        """验证目录是否存在"""
        if not isinstance(value, str):
            return False
        
        return Path(value).is_dir()
    
    def get_builtin_validator(self, name: str) -> Optional[Callable[[Any], bool]]:
        """获取内置验证器"""
        return self._builtin_validators.get(name)


# 便利函数
def create_type_rule(field_path: str, expected_type: Type, 
                    required: bool = False, allow_none: bool = False) -> ValidationRule:
    """创建类型验证规则"""
    return ValidationRule(
        field_path=field_path,
        validation_type=ValidationType.TYPE,
        expected_type=expected_type,
        required=required,
        allow_none=allow_none
    )


def create_range_rule(field_path: str, min_value: Optional[Union[int, float]] = None,
                     max_value: Optional[Union[int, float]] = None) -> ValidationRule:
    """创建范围验证规则"""
    return ValidationRule(
        field_path=field_path,
        validation_type=ValidationType.RANGE,
        min_value=min_value,
        max_value=max_value
    )


def create_pattern_rule(field_path: str, pattern: str, flags: int = 0) -> ValidationRule:
    """创建正则验证规则"""
    return ValidationRule(
        field_path=field_path,
        validation_type=ValidationType.PATTERN,
        pattern=pattern,
        pattern_flags=flags
    )


def create_enum_rule(field_path: str, allowed_values: List[Any]) -> ValidationRule:
    """创建枚举验证规则"""
    return ValidationRule(
        field_path=field_path,
        validation_type=ValidationType.ENUM,
        allowed_values=allowed_values
    )


def create_custom_rule(field_path: str, validator: Callable[[Any], bool],
                      message: Optional[str] = None) -> ValidationRule:
    """创建自定义验证规则"""
    return ValidationRule(
        field_path=field_path,
        validation_type=ValidationType.CUSTOM,
        custom_validator=validator,
        custom_message=message
    )