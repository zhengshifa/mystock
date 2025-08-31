#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础数据模型
提供所有数据模型的通用基类和配置
"""

from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional, Any, Dict


class BaseConfig:
    """基础配置类"""
    
    # Pydantic配置
    model_config = ConfigDict(
        # 允许额外字段
        extra='allow',
        # 允许从属性赋值
        populate_by_name=True,
        # 验证时使用别名
        alias_generator=None,
        # 序列化时包含默认值
        exclude_unset=False,
        # 序列化时包含默认值
        exclude_defaults=False,
        # 序列化时包含None值
        exclude_none=False,
        # 使用枚举值
        use_enum_values=True,
        # 验证时严格类型检查
        strict=False,
        # 允许任意类型
        arbitrary_types_allowed=True,
        # 序列化时使用别名
        serialize_default_excludes=False,
        # 验证时使用别名
        validate_assignment=True
    )


class AppBaseModel(BaseModel):
    """基础数据模型类"""
    
    model_config = BaseConfig.model_config
    
    # 通用字段
    created_at: Optional[datetime] = Field(
        default_factory=datetime.now,
        description="创建时间"
    )
    updated_at: Optional[datetime] = Field(
        default_factory=datetime.now,
        description="更新时间"
    )
    
    def update_timestamp(self):
        """更新时间戳"""
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.model_dump()
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return self.model_dump_json()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """从字典创建实例"""
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str):
        """从JSON字符串创建实例"""
        return cls.model_validate_json(json_str)


class TimestampedModel(AppBaseModel):
    """带时间戳的模型基类"""
    
    model_config = BaseConfig.model_config
    
    # 时间戳字段
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="创建时间"
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        description="更新时间"
    )
    
    def update_timestamp(self):
        """更新时间戳"""
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.model_dump()
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return self.model_dump_json()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """从字典创建实例"""
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str):
        """从JSON字符串创建实例"""
        return cls.model_validate_json(json_str)


class IdentifiableModel(AppBaseModel):
    """可识别的模型基类"""
    
    model_config = BaseConfig.model_config
    
    # 标识字段
    id: Optional[str] = Field(
        default=None,
        description="唯一标识符"
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.model_dump()
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return self.model_dump_json()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """从字典创建实例"""
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str):
        """从JSON字符串创建实例"""
        return cls.model_validate_json(json_str)
