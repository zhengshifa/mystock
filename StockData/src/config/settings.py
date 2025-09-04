"""
配置管理模块
负责加载和管理应用程序的配置信息
"""
import os
from typing import Optional
from datetime import datetime, timedelta
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
        
        # 终端服务地址配置
        self.gm_serv_addr: Optional[str] = os.getenv('GM_SERV_ADDR', '').strip()
        if self.gm_serv_addr:
            # 验证serv_addr格式
            if not self._validate_serv_addr(self.gm_serv_addr):
                raise ValueError(f"GM_SERV_ADDR 格式无效: {self.gm_serv_addr}，应为 'ip:port' 格式")
        
        # 数据时间范围配置
        # 当START_DATE和END_DATE为空时，默认使用最新180天的数据
        start_date_env = os.getenv('START_DATE', '').strip()
        end_date_env = os.getenv('END_DATE', '').strip()
        
        if not start_date_env or not end_date_env:
            # 计算默认180天时间范围
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=180)
            self.start_date = start_date.strftime('%Y-%m-%d')
            self.end_date = end_date.strftime('%Y-%m-%d')
        else:
            self.start_date = start_date_env
            self.end_date = end_date_env
        
        # 测试股票代码
        # 当TEST_SYMBOLS为空时，表示同步全部股票
        test_symbols_str = os.getenv('TEST_SYMBOLS', '').strip()
        if test_symbols_str:
            self.test_symbols: list[str] = [s.strip() for s in test_symbols_str.split(',') if s.strip()]
        else:
            self.test_symbols: list[str] = []  # 空列表表示全部股票
        
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
    
    def get_default_date_range(self, days: int = 180) -> tuple[str, str]:
        """
        获取默认日期范围
        
        Args:
            days: 天数，默认180天
            
        Returns:
            tuple[str, str]: (开始日期, 结束日期)
        """
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')
    
    def is_all_symbols_mode(self) -> bool:
        """
        检查是否使用全部股票模式
        
        Returns:
            bool: 是否使用全部股票
        """
        return len(self.test_symbols) == 0
    
    def validate(self) -> bool:
        """
        验证配置的有效性
        
        Returns:
            bool: 配置是否有效
        """
        if not self.gm_token:
            print("错误: GM_TOKEN 未设置")
            return False
        
        # 允许空股票列表（表示全部股票模式）
        # if not self.test_symbols:
        #     print("错误: 测试股票代码未设置")
        #     return False
        
        # 验证日期格式
        try:
            datetime.strptime(self.start_date, '%Y-%m-%d')
            datetime.strptime(self.end_date, '%Y-%m-%d')
        except ValueError:
            print(f"错误: 日期格式无效 - 开始日期: {self.start_date}, 结束日期: {self.end_date}")
            return False
        
        return True
    
    def _validate_serv_addr(self, serv_addr: str) -> bool:
        """
        验证serv_addr格式是否正确
        
        Args:
            serv_addr: 服务地址，格式应为 'ip:port'
            
        Returns:
            bool: 格式是否正确
        """
        try:
            if ':' not in serv_addr:
                return False
            
            parts = serv_addr.split(':')
            if len(parts) != 2:
                return False
            
            ip, port = parts
            # 验证端口号
            port_num = int(port)
            if not (1 <= port_num <= 65535):
                return False
            
            # 简单验证IP格式（可以是域名）
            if not ip.strip():
                return False
                
            return True
        except (ValueError, IndexError):
            return False


# 全局配置实例
settings = Settings()
