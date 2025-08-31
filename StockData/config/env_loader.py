#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境变量加载器
专门负责从环境变量加载配置
"""

import os
from typing import List
from .settings import AppConfig


class EnvLoader:
    """环境变量加载器类"""
    
    @staticmethod
    def load_config_from_env(config: AppConfig):
        """
        从环境变量加载配置到配置实例
        
        Args:
            config: 配置实例
        """
        # MongoDB配置
        EnvLoader._load_mongodb_config(config.mongodb)
        
        # GM SDK配置
        EnvLoader._load_gm_sdk_config(config.gm_sdk)
        
        # 日志配置
        EnvLoader._load_logging_config(config.logging)
        
        # 调度器配置
        EnvLoader._load_scheduler_config(config.scheduler)
    
    @staticmethod
    def _load_mongodb_config(mongodb_config):
        """加载MongoDB配置"""
        if os.getenv("MONGODB_URL"):
            mongodb_config.url = os.getenv("MONGODB_URL")
            # 从URL中提取数据库名
            mongodb_config._extract_database_from_url()
        if os.getenv("MONGODB_HOST"):
            mongodb_config.host = os.getenv("MONGODB_HOST")
        if os.getenv("MONGODB_PORT"):
            mongodb_config.port = int(os.getenv("MONGODB_PORT"))
        if os.getenv("MONGODB_DATABASE"):
            mongodb_config.database = os.getenv("MONGODB_DATABASE")
        if os.getenv("MONGODB_USERNAME"):
            mongodb_config.username = os.getenv("MONGODB_USERNAME")
        if os.getenv("MONGODB_PASSWORD"):
            mongodb_config.password = os.getenv("MONGODB_PASSWORD")
    
    @staticmethod
    def _load_gm_sdk_config(gm_config):
        """加载GM SDK配置"""
        if os.getenv("GM_TOKEN"):
            gm_config.token = os.getenv("GM_TOKEN")
        if os.getenv("GM_ENDPOINT"):
            gm_config.endpoint = os.getenv("GM_ENDPOINT")
    
    @staticmethod
    def _load_logging_config(logging_config):
        """加载日志配置"""
        if os.getenv("LOG_LEVEL"):
            logging_config.level = os.getenv("LOG_LEVEL")
        if os.getenv("LOG_DIR"):
            logging_config.log_dir = os.getenv("LOG_DIR")
    
    @staticmethod
    def _load_scheduler_config(scheduler_config):
        """加载调度器配置"""
        if os.getenv("REALTIME_INTERVAL"):
            scheduler_config.realtime_interval = int(os.getenv("REALTIME_INTERVAL"))
        if os.getenv("MINUTE_INTERVAL"):
            scheduler_config.minute_interval = int(os.getenv("MINUTE_INTERVAL"))
        if os.getenv("DAILY_INTERVAL"):
            scheduler_config.daily_interval = int(os.getenv("DAILY_INTERVAL"))
        if os.getenv("MAX_RETRIES"):
            scheduler_config.max_retries = int(os.getenv("MAX_RETRIES"))
        if os.getenv("RETRY_DELAY"):
            scheduler_config.retry_delay = int(os.getenv("RETRY_DELAY"))
        
        # 股票代码配置
        stock_codes_env = os.getenv("STOCK_CODES")
        if stock_codes_env is not None:  # 允许空字符串
            if stock_codes_env.strip():  # 如果不为空
                raw_codes = [code.strip() for code in stock_codes_env.split(',') if code.strip()]
                scheduler_config.stock_symbols = EnvLoader._convert_stock_codes_to_gm_format(raw_codes)
            else:  # 如果为空，表示获取全部A股
                scheduler_config.stock_symbols = []
    
    @staticmethod
    def _convert_stock_codes_to_gm_format(codes: List[str]) -> List[str]:
        """
        将股票代码转换为GM SDK格式
        
        Args:
            codes: 股票代码列表，支持多种格式：
                  - 600111.SH -> SHSE.600111
                  - 000001.SZ -> SZSE.000001
                  - SHSE.600111 -> SHSE.600111 (已是GM格式，保持不变)
                  - SZSE.000001 -> SZSE.000001 (已是GM格式，保持不变)
        
        Returns:
            转换后的GM SDK格式股票代码列表
        """
        converted_codes = []
        for code in codes:
            code = code.strip().upper()
            if not code:
                continue
                
            # 如果已经是GM格式（SHSE.xxx或SZSE.xxx），直接使用
            if code.startswith(('SHSE.', 'SZSE.')):
                converted_codes.append(code)
            # 转换.SH格式到SHSE格式
            elif code.endswith('.SH'):
                stock_num = code[:-3]
                converted_codes.append(f'SHSE.{stock_num}')
            # 转换.SZ格式到SZSE格式
            elif code.endswith('.SZ'):
                stock_num = code[:-3]
                converted_codes.append(f'SZSE.{stock_num}')
            # 如果是纯数字，根据开头判断市场
            elif code.isdigit():
                if code.startswith(('6', '9')):
                    # 6开头和9开头的是上海市场
                    converted_codes.append(f'SHSE.{code}')
                elif code.startswith(('0', '3')):
                    # 0开头和3开头的是深圳市场
                    converted_codes.append(f'SZSE.{code}')
                else:
                    # 其他情况，默认添加原代码（可能需要手动处理）
                    converted_codes.append(code)
            else:
                # 其他格式，保持原样
                converted_codes.append(code)
                
        return converted_codes
