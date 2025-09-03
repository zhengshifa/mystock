"""
配置管理模块
负责加载和管理应用程序的配置信息
"""
import os
from typing import Optional
from dotenv import load_dotenv


class Settings:
    """应用程序配置类"""
    
    def __init__(self):
        """初始化配置"""
        # 加载环境变量
        load_dotenv('config.env')
        
        # 掘金量化API配置
        self.gm_token: str = os.getenv('GM_TOKEN', '')
        if not self.gm_token:
            raise ValueError("GM_TOKEN 环境变量未设置")
        
        # 数据时间范围配置
        self.start_date: str = os.getenv('START_DATE', '2024-01-01')
        self.end_date: str = os.getenv('END_DATE', '2024-12-31')
        
        # 测试股票代码
        test_symbols_str = os.getenv('TEST_SYMBOLS', 'SZSE.000001,SHSE.000300')
        self.test_symbols: list[str] = [s.strip() for s in test_symbols_str.split(',')]
        
        # 日志配置
        self.log_level: str = os.getenv('LOG_LEVEL', 'INFO')
        
        # MongoDB配置
        self.mongodb_url: str = os.getenv('MONGODB_URL', 'mongodb://localhost:27017')
        self.mongodb_database: str = os.getenv('MONGODB_DATABASE', 'stockdata')
        self.mongodb_collection_tick: str = os.getenv('MONGODB_COLLECTION_TICK', 'tick_data')
        self.mongodb_collection_sync_log: str = os.getenv('MONGODB_COLLECTION_SYNC_LOG', 'sync_log')
        
        # 多频率集合配置
        self.mongodb_collection_bar_60s: str = os.getenv('MONGODB_COLLECTION_BAR_60S', 'bar_60s')
        self.mongodb_collection_bar_300s: str = os.getenv('MONGODB_COLLECTION_BAR_300S', 'bar_300s')
        self.mongodb_collection_bar_900s: str = os.getenv('MONGODB_COLLECTION_BAR_900S', 'bar_900s')
        self.mongodb_collection_bar_1800s: str = os.getenv('MONGODB_COLLECTION_BAR_1800S', 'bar_1800s')
        self.mongodb_collection_bar_3600s: str = os.getenv('MONGODB_COLLECTION_BAR_3600S', 'bar_3600s')
        self.mongodb_collection_bar_1d: str = os.getenv('MONGODB_COLLECTION_BAR_1D', 'bar_1d')
        
        # 调度配置
        self.scheduler_enabled: bool = os.getenv('SCHEDULER_ENABLED', 'true').lower() == 'true'
        self.sync_interval_minutes: int = int(os.getenv('SYNC_INTERVAL_MINUTES', '5'))
        self.realtime_interval_seconds: int = int(os.getenv('REALTIME_INTERVAL_SECONDS', '30'))
        self.history_sync_time: str = os.getenv('HISTORY_SYNC_TIME', '09:30')
        
        # 交易时间配置
        self.trading_morning_start: str = os.getenv('TRADING_MORNING_START', '09:30')
        self.trading_morning_end: str = os.getenv('TRADING_MORNING_END', '11:30')
        self.trading_afternoon_start: str = os.getenv('TRADING_AFTERNOON_START', '13:00')
        self.trading_afternoon_end: str = os.getenv('TRADING_AFTERNOON_END', '15:00')
        
        # 增量同步配置
        self.pre_market_sync_time: str = os.getenv('PRE_MARKET_SYNC_TIME', '08:30')
        self.post_market_sync_time: str = os.getenv('POST_MARKET_SYNC_TIME', '15:30')
        self.incremental_sync_enabled: bool = os.getenv('INCREMENTAL_SYNC_ENABLED', 'true').lower() == 'true'
        
        # 数据频率配置
        enabled_frequencies_str = os.getenv('ENABLED_FREQUENCIES', '60s,300s,900s,1800s,3600s,1d')
        self.enabled_frequencies: list[str] = [f.strip() for f in enabled_frequencies_str.split(',')]
        
        # 各频率同步开关
        self.sync_frequency_60s: bool = os.getenv('SYNC_FREQUENCY_60S', 'true').lower() == 'true'
        self.sync_frequency_300s: bool = os.getenv('SYNC_FREQUENCY_300S', 'true').lower() == 'true'
        self.sync_frequency_900s: bool = os.getenv('SYNC_FREQUENCY_900S', 'true').lower() == 'true'
        self.sync_frequency_1800s: bool = os.getenv('SYNC_FREQUENCY_1800S', 'true').lower() == 'true'
        self.sync_frequency_3600s: bool = os.getenv('SYNC_FREQUENCY_3600S', 'true').lower() == 'true'
        self.sync_frequency_1d: bool = os.getenv('SYNC_FREQUENCY_1D', 'true').lower() == 'true'
        
        # 数据同步配置
        self.batch_size: int = int(os.getenv('BATCH_SIZE', '100'))
        self.max_retry_times: int = int(os.getenv('MAX_RETRY_TIMES', '3'))
        self.retry_delay_seconds: int = int(os.getenv('RETRY_DELAY_SECONDS', '5'))
        
        # 标的基本信息同步配置
        self.symbol_sync_enabled: bool = os.getenv('SYMBOL_SYNC_ENABLED', 'true').lower() == 'true'
        self.symbol_sync_time: str = os.getenv('SYMBOL_SYNC_TIME', '09:00')
        self.symbol_sync_all_types: bool = os.getenv('SYMBOL_SYNC_ALL_TYPES', 'true').lower() == 'true'
    
    def get_frequency_collection_name(self, frequency: str) -> str:
        """
        根据频率获取对应的集合名称
        
        Args:
            frequency: 数据频率
            
        Returns:
            str: 集合名称
        """
        frequency_mapping = {
            '60s': self.mongodb_collection_bar_60s,
            '300s': self.mongodb_collection_bar_300s,
            '900s': self.mongodb_collection_bar_900s,
            '1800s': self.mongodb_collection_bar_1800s,
            '3600s': self.mongodb_collection_bar_3600s,
            '1d': self.mongodb_collection_bar_1d
        }
        return frequency_mapping.get(frequency, f'bar_{frequency}')
    
    def is_frequency_enabled(self, frequency: str) -> bool:
        """
        检查指定频率是否启用
        
        Args:
            frequency: 数据频率
            
        Returns:
            bool: 是否启用
        """
        frequency_switches = {
            '60s': self.sync_frequency_60s,
            '300s': self.sync_frequency_300s,
            '900s': self.sync_frequency_900s,
            '1800s': self.sync_frequency_1800s,
            '3600s': self.sync_frequency_3600s,
            '1d': self.sync_frequency_1d
        }
        return frequency_switches.get(frequency, False)
    
    def validate(self) -> bool:
        """
        验证配置的有效性
        
        Returns:
            bool: 配置是否有效
        """
        if not self.gm_token:
            print("错误: GM_TOKEN 未设置")
            return False
        
        if not self.test_symbols:
            print("错误: 测试股票代码未设置")
            return False
        
        return True


# 全局配置实例
settings = Settings()
