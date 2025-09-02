#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置验证器

验证配置文件的完整性和正确性
"""

from typing import Dict, Any, List


class ConfigValidator:
    """配置验证器"""
    
    def __init__(self):
        self.required_sections = [
            'gm',
            'mongodb',
            'sync',
            'logging',
            'scheduler',
            'stock_data_types'
        ]
        
        self.required_gm_fields = [
            'username',
            'password'
        ]
        
        self.required_mongodb_fields = [
            'host',
            'port',
            'username',
            'password',
            'database'
        ]
    
    def validate(self, config: Dict[str, Any]) -> bool:
        """验证配置"""
        errors = []
        
        # 验证必需的配置段
        errors.extend(self._validate_required_sections(config))
        
        # 验证掘金量化配置
        errors.extend(self._validate_gm_config(config.get('gm', {})))
        
        # 验证MongoDB配置
        errors.extend(self._validate_mongodb_config(config.get('mongodb', {})))
        
        # 验证同步配置
        errors.extend(self._validate_sync_config(config.get('sync', {})))
        
        # 验证股票数据类型配置
        errors.extend(self._validate_stock_data_types(config.get('stock_data_types', {})))
        
        if errors:
            raise ValueError(f"配置验证失败:\n" + "\n".join(errors))
        
        return True
    
    def _validate_required_sections(self, config: Dict[str, Any]) -> List[str]:
        """验证必需的配置段"""
        errors = []
        
        for section in self.required_sections:
            if section not in config:
                errors.append(f"缺少必需的配置段: {section}")
        
        return errors
    
    def _validate_gm_config(self, gm_config: Dict[str, Any]) -> List[str]:
        """验证掘金量化配置"""
        errors = []
        
        for field in self.required_gm_fields:
            if field not in gm_config or not gm_config[field]:
                errors.append(f"掘金量化配置缺少必需字段: {field}")
        
        # 验证服务器URL
        if 'server_url' in gm_config:
            server_url = gm_config['server_url']
            if not isinstance(server_url, str) or not server_url.strip():
                errors.append("掘金量化服务器URL无效")
        
        # 验证超时时间
        if 'timeout' in gm_config:
            timeout = gm_config['timeout']
            if not isinstance(timeout, (int, float)) or timeout <= 0:
                errors.append("掘金量化超时时间必须为正数")
        
        return errors
    
    def _validate_mongodb_config(self, mongodb_config: Dict[str, Any]) -> List[str]:
        """验证MongoDB配置"""
        errors = []
        
        for field in self.required_mongodb_fields:
            if field not in mongodb_config or not mongodb_config[field]:
                errors.append(f"MongoDB配置缺少必需字段: {field}")
        
        # 验证端口号
        if 'port' in mongodb_config:
            port = mongodb_config['port']
            if not isinstance(port, int) or port <= 0 or port > 65535:
                errors.append("MongoDB端口号必须为1-65535之间的整数")
        
        # 验证连接池配置
        if 'max_pool_size' in mongodb_config:
            max_pool_size = mongodb_config['max_pool_size']
            if not isinstance(max_pool_size, int) or max_pool_size <= 0:
                errors.append("MongoDB最大连接池大小必须为正整数")
        
        if 'min_pool_size' in mongodb_config:
            min_pool_size = mongodb_config['min_pool_size']
            if not isinstance(min_pool_size, int) or min_pool_size < 0:
                errors.append("MongoDB最小连接池大小必须为非负整数")
        
        return errors
    
    def _validate_sync_config(self, sync_config: Dict[str, Any]) -> List[str]:
        """验证同步配置"""
        errors = []
        
        # 验证实时同步间隔
        if 'realtime_interval' in sync_config:
            interval = sync_config['realtime_interval']
            if not isinstance(interval, (int, float)) or interval <= 0:
                errors.append("实时同步间隔必须为正数")
        
        # 验证历史数据同步配置
        if 'history' in sync_config:
            history_config = sync_config['history']
            
            if 'batch_size' in history_config:
                batch_size = history_config['batch_size']
                if not isinstance(batch_size, int) or batch_size <= 0:
                    errors.append("历史数据批量大小必须为正整数")
            
            if 'batch_interval' in history_config:
                batch_interval = history_config['batch_interval']
                if not isinstance(batch_interval, (int, float)) or batch_interval < 0:
                    errors.append("历史数据批次间隔必须为非负数")
            
            if 'max_retries' in history_config:
                max_retries = history_config['max_retries']
                if not isinstance(max_retries, int) or max_retries < 0:
                    errors.append("最大重试次数必须为非负整数")
        
        return errors
    
    def _validate_stock_data_types(self, stock_data_types: Dict[str, Any]) -> List[str]:
        """验证股票数据类型配置"""
        errors = []
        
        required_categories = ['basic', 'market', 'financial', 'others']
        
        for category in required_categories:
            if category not in stock_data_types:
                errors.append(f"股票数据类型配置缺少类别: {category}")
            elif not isinstance(stock_data_types[category], list):
                errors.append(f"股票数据类型 {category} 必须为列表")
            elif not stock_data_types[category]:
                errors.append(f"股票数据类型 {category} 不能为空")
        
        return errors
    
    def validate_runtime_config(self, config: Dict[str, Any]) -> bool:
        """验证运行时配置"""
        errors = []
        
        # 验证掘金量化连接
        gm_config = config.get('gm', {})
        auth_type = gm_config.get('auth_type', 'username_password')
        
        if auth_type == 'token':
            if not gm_config.get('token'):
                errors.append("Token认证模式下掘金量化token为空")
        else:
            if not gm_config.get('username') or not gm_config.get('password'):
                errors.append("用户名密码认证模式下掘金量化用户名或密码为空")
        
        # 验证MongoDB连接信息
        mongodb_config = config.get('mongodb', {})
        if not mongodb_config.get('username') or not mongodb_config.get('password'):
            errors.append("MongoDB用户名或密码为空")
        
        if errors:
            raise ValueError(f"运行时配置验证失败:\n" + "\n".join(errors))
        
        return True