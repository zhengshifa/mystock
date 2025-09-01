"""
调度配置管理模块
包含定时任务的时间、频率、股票列表等配置
"""
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from datetime import time
from src.config.yaml_loader import get_yaml_config_loader


class TaskSchedule(BaseModel):
    """单个任务的调度配置"""
    name: str = Field(..., description="任务名称")
    enabled: bool = Field(True, description="是否启用")
    interval_type: str = Field(..., description="间隔类型: seconds, minutes, hours, daily")
    interval_value: int = Field(..., description="间隔值")
    at_time: str = Field(None, description="每日执行时间 (HH:MM格式)")
    description: str = Field("", description="任务描述")


class DataCollectionConfig(BaseModel):
    """数据收集配置"""
    # 实时数据收集配置
    realtime_tick_interval: int = Field(30, description="实时Tick数据收集间隔(秒)")
    realtime_bar_interval: int = Field(60, description="实时Bar数据收集间隔(秒)")
    
    # 定时全量同步配置
    daily_sync_times: List[str] = Field(
        ["09:00", "12:00", "15:05"], 
        description="每日全量同步时间点"
    )
    
    # 市场状态检查配置
    market_status_check_interval: int = Field(5, description="市场状态检查间隔(分钟)")
    
    # 数据频率配置
    supported_frequencies: List[str] = Field(
        ["60s", "300s", "900s", "1d"], 
        description="支持的K线数据频率"
    )
    
    # 默认股票列表
    default_sh_symbols: List[str] = Field(
        ["600000", "600036", "600519", "600887", "601318"], 
        description="上海市场默认股票代码"
    )
    default_sz_symbols: List[str] = Field(
        ["000001", "000002", "000858", "002415", "300059"], 
        description="深圳市场默认股票代码"
    )
    
    # 交易时间配置
    trading_hours: Dict[str, List[str]] = Field(
        {
            "morning": ["09:30", "11:30"],
            "afternoon": ["13:00", "15:00"]
        },
        description="交易时间段配置"
    )
    
    # 周末是否交易
    weekend_trading: bool = Field(False, description="周末是否交易")


class SchedulerConfig(BaseModel):
    """调度器总配置"""
    # 数据收集配置
    data_collection: DataCollectionConfig = Field(
        default_factory=DataCollectionConfig,
        description="数据收集配置"
    )
    
    # 任务调度配置
    tasks: List[TaskSchedule] = Field(
        default_factory=list,
        description="任务调度配置列表"
    )
    
    # 调度器运行配置
    scheduler_sleep_interval: int = Field(1, description="调度器主循环休眠间隔(秒)")
    scheduler_exception_wait: int = Field(5, description="调度器异常时等待时间(秒)")
    
    # 重试配置
    max_retry_count: int = Field(3, description="最大重试次数")
    retry_wait_time: int = Field(1, description="重试等待时间(秒)")
    
    # 批处理配置
    batch_size: int = Field(1000, description="批处理大小")
    batch_timeout: int = Field(30, description="批处理超时时间(秒)")


class SchedulerConfigManager:
    """调度配置管理器"""
    
    def __init__(self, config_file: str = "scheduler_config.yaml"):
        """初始化配置管理器"""
        self.config_file = config_file
        self.yaml_loader = get_yaml_config_loader()
        self.config = self._load_config()
    
    def _load_config(self) -> SchedulerConfig:
        """加载配置（优先从YAML文件，失败则使用默认配置）"""
        try:
            # 尝试从YAML文件加载配置
            yaml_config = self.yaml_loader.load_config(self.config_file)
            if yaml_config:
                return self._convert_yaml_to_config(yaml_config)
        except Exception as e:
            print(f"从YAML文件加载配置失败，使用默认配置: {e}")
        
        # 使用默认配置
        return self._load_default_config()
    
    def _convert_yaml_to_config(self, yaml_config: Dict[str, Any]) -> SchedulerConfig:
        """将YAML配置转换为Pydantic配置对象"""
        try:
            # 转换任务配置
            tasks = []
            if 'tasks' in yaml_config:
                for task_data in yaml_config['tasks']:
                    task = TaskSchedule(**task_data)
                    tasks.append(task)
            
            # 转换数据收集配置
            data_collection = DataCollectionConfig()
            if 'data_collection' in yaml_config:
                dc_data = yaml_config['data_collection']
                data_collection = DataCollectionConfig(**dc_data)
            
            # 转换调度器配置
            scheduler_config = {
                'scheduler_sleep_interval': 1,
                'scheduler_exception_wait': 5,
                'max_retry_count': 3,
                'retry_wait_time': 1,
                'batch_size': 1000,
                'batch_timeout': 30
            }
            
            if 'scheduler' in yaml_config:
                scheduler_config.update(yaml_config['scheduler'])
            
            return SchedulerConfig(
                data_collection=data_collection,
                tasks=tasks,
                **scheduler_config
            )
            
        except Exception as e:
            print(f"转换YAML配置失败: {e}")
            return self._load_default_config()
    
    def _load_default_config(self) -> SchedulerConfig:
        """加载默认配置"""
        # 定义默认任务配置
        default_tasks = [
            TaskSchedule(
                name="实时数据同步",
                enabled=True,
                interval_type="seconds",
                interval_value=30,
                description="交易时间每30秒同步实时数据"
            ),
            TaskSchedule(
                name="开盘前全量同步",
                enabled=True,
                interval_type="daily",
                interval_value=1,
                at_time="09:00",
                description="每日开盘前全量同步数据"
            ),
            TaskSchedule(
                name="午盘前全量同步",
                enabled=True,
                interval_type="daily",
                interval_value=1,
                at_time="12:00",
                description="每日午盘前全量同步数据"
            ),
            TaskSchedule(
                name="收盘后全量同步",
                enabled=True,
                interval_type="daily",
                interval_value=1,
                at_time="15:05",
                description="每日收盘后全量同步数据"
            ),
            TaskSchedule(
                name="市场状态检查",
                enabled=True,
                interval_type="minutes",
                interval_value=5,
                description="每5分钟检查市场状态"
            )
        ]
        
        return SchedulerConfig(
            tasks=default_tasks
        )
    
    def reload_config(self) -> bool:
        """重新加载配置文件"""
        try:
            self.config = self._load_config()
            return True
        except Exception as e:
            print(f"重新加载配置失败: {e}")
            return False
    
    def save_config(self) -> bool:
        """保存当前配置到YAML文件"""
        try:
            # 将当前配置转换为字典
            config_dict = self.config.dict()
            
            # 保存到YAML文件
            return self.yaml_loader.save_config(self.config_file, config_dict)
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False
    
    def get_config(self) -> SchedulerConfig:
        """获取当前配置"""
        return self.config
    
    def update_config(self, new_config: SchedulerConfig) -> None:
        """更新配置"""
        self.config = new_config
    
    def get_task_config(self, task_name: str) -> TaskSchedule:
        """获取指定任务的配置"""
        for task in self.config.tasks:
            if task.name == task_name:
                return task
        return None
    
    def enable_task(self, task_name: str) -> bool:
        """启用指定任务"""
        task = self.get_task_config(task_name)
        if task:
            task.enabled = True
            return True
        return False
    
    def disable_task(self, task_name: str) -> bool:
        """禁用指定任务"""
        task = self.get_task_config(task_name)
        if task:
            task.enabled = False
            return True
        return False
    
    def get_enabled_tasks(self) -> List[TaskSchedule]:
        """获取所有启用的任务"""
        return [task for task in self.config.tasks if task.enabled]
    
    def get_stock_symbols(self, market: str = None) -> List[str]:
        """获取股票代码列表"""
        if market == "SH":
            return self.config.data_collection.default_sh_symbols
        elif market == "SZ":
            return self.config.data_collection.default_sz_symbols
        else:
            # 返回所有股票代码
            return (self.config.data_collection.default_sh_symbols + 
                   self.config.data_collection.default_sz_symbols)
    
    def get_trading_hours(self) -> Dict[str, List[str]]:
        """获取交易时间配置"""
        return self.config.data_collection.trading_hours
    
    def get_supported_frequencies(self) -> List[str]:
        """获取支持的数据频率"""
        return self.config.data_collection.supported_frequencies
    
    def is_weekend_trading_enabled(self) -> bool:
        """是否启用周末交易"""
        return self.config.data_collection.weekend_trading
    
    def get_realtime_intervals(self) -> Dict[str, int]:
        """获取实时数据收集间隔"""
        return {
            "tick": self.config.data_collection.realtime_tick_interval,
            "bar": self.config.data_collection.realtime_bar_interval
        }
    
    def get_daily_sync_times(self) -> List[str]:
        """获取每日同步时间点"""
        return self.config.data_collection.daily_sync_times
    
    def get_market_check_interval(self) -> int:
        """获取市场状态检查间隔"""
        return self.config.data_collection.market_status_check_interval
    
    def get_scheduler_config(self) -> Dict[str, Any]:
        """获取调度器运行配置"""
        return {
            "sleep_interval": self.config.scheduler_sleep_interval,
            "exception_wait": self.config.scheduler_exception_wait,
            "max_retry": self.config.max_retry_count,
            "retry_wait": self.config.retry_wait_time,
            "batch_size": self.config.batch_size,
            "batch_timeout": self.config.batch_timeout
        }
    
    def update_stock_symbols(self, market: str, symbols: List[str]) -> bool:
        """更新股票代码列表"""
        try:
            if market == "SH":
                self.config.data_collection.default_sh_symbols = symbols
            elif market == "SZ":
                self.config.data_collection.default_sz_symbols = symbols
            else:
                return False
            
            return True
        except Exception as e:
            print(f"更新股票代码列表失败: {e}")
            return False
    
    def update_trading_hours(self, trading_hours: Dict[str, List[str]]) -> bool:
        """更新交易时间配置"""
        try:
            self.config.data_collection.trading_hours = trading_hours
            return True
        except Exception as e:
            print(f"更新交易时间配置失败: {e}")
            return False
    
    def update_task_schedule(self, task_name: str, **kwargs) -> bool:
        """更新任务调度配置"""
        try:
            task = self.get_task_config(task_name)
            if not task:
                return False
            
            # 更新任务属性
            for key, value in kwargs.items():
                if hasattr(task, key):
                    setattr(task, key, value)
            
            return True
        except Exception as e:
            print(f"更新任务调度配置失败: {e}")
            return False


# 全局配置实例 - 延迟初始化
scheduler_config_manager = None

def get_scheduler_config() -> SchedulerConfigManager:
    """获取调度配置管理器实例，延迟初始化"""
    global scheduler_config_manager
    if scheduler_config_manager is None:
        scheduler_config_manager = SchedulerConfigManager()
    return scheduler_config_manager
