"""
配置管理工具
提供动态调整调度配置、股票列表、交易时间等功能
"""
import json
from typing import List, Dict, Any, Optional
from src.config.scheduler_config import get_scheduler_config
from src.config.yaml_loader import get_yaml_config_loader
from src.utils.logger import get_logger


class ConfigManager:
    """配置管理器"""
    
    def __init__(self):
        """初始化配置管理器"""
        self.logger = get_logger("ConfigManager")
        self.scheduler_config = get_scheduler_config()
        self.yaml_loader = get_yaml_config_loader()
    
    def get_current_config(self) -> Dict[str, Any]:
        """获取当前配置的完整信息"""
        try:
            config = self.scheduler_config.get_config()
            return config.dict()
        except Exception as e:
            self.logger.error(f"获取当前配置失败: {e}")
            return {}
    
    def update_stock_symbols(self, market: str, symbols: List[str]) -> bool:
        """更新股票代码列表"""
        try:
            if self.scheduler_config.update_stock_symbols(market, symbols):
                # 保存到YAML文件
                if self.scheduler_config.save_config():
                    self.logger.info(f"成功更新{market}市场股票代码列表: {len(symbols)}只股票")
                    return True
                else:
                    self.logger.error("保存配置到文件失败")
                    return False
            else:
                self.logger.error(f"更新{market}市场股票代码列表失败")
                return False
        except Exception as e:
            self.logger.error(f"更新股票代码列表异常: {e}")
            return False
    
    def add_stock_symbol(self, market: str, symbol: str) -> bool:
        """添加单个股票代码"""
        try:
            current_symbols = self.scheduler_config.get_stock_symbols(market)
            if symbol not in current_symbols:
                current_symbols.append(symbol)
                return self.update_stock_symbols(market, current_symbols)
            else:
                self.logger.warning(f"股票代码 {symbol} 已存在于{market}市场")
                return True
        except Exception as e:
            self.logger.error(f"添加股票代码异常: {e}")
            return False
    
    def remove_stock_symbol(self, market: str, symbol: str) -> bool:
        """移除单个股票代码"""
        try:
            current_symbols = self.scheduler_config.get_stock_symbols(market)
            if symbol in current_symbols:
                current_symbols.remove(symbol)
                return self.update_stock_symbols(market, current_symbols)
            else:
                self.logger.warning(f"股票代码 {symbol} 不存在于{market}市场")
                return True
        except Exception as e:
            self.logger.error(f"移除股票代码异常: {e}")
            return False
    
    def update_trading_hours(self, trading_hours: Dict[str, List[str]]) -> bool:
        """更新交易时间配置"""
        try:
            if self.scheduler_config.update_trading_hours(trading_hours):
                # 保存到YAML文件
                if self.scheduler_config.save_config():
                    self.logger.info("成功更新交易时间配置")
                    return True
                else:
                    self.logger.error("保存配置到文件失败")
                    return False
            else:
                self.logger.error("更新交易时间配置失败")
                return False
        except Exception as e:
            self.logger.error(f"更新交易时间配置异常: {e}")
            return False
    
    def update_task_schedule(self, task_name: str, **kwargs) -> bool:
        """更新任务调度配置"""
        try:
            if self.scheduler_config.update_task_schedule(task_name, **kwargs):
                # 保存到YAML文件
                if self.scheduler_config.save_config():
                    self.logger.info(f"成功更新任务 {task_name} 的调度配置")
                    return True
                else:
                    self.logger.error("保存配置到文件失败")
                    return False
            else:
                self.logger.error(f"更新任务 {task_name} 的调度配置失败")
                return False
        except Exception as e:
            self.logger.error(f"更新任务调度配置异常: {e}")
            return False
    
    def enable_task(self, task_name: str) -> bool:
        """启用指定任务"""
        try:
            if self.scheduler_config.enable_task(task_name):
                if self.scheduler_config.save_config():
                    self.logger.info(f"成功启用任务: {task_name}")
                    return True
                else:
                    self.logger.error("保存配置到文件失败")
                    return False
            else:
                self.logger.error(f"启用任务失败: {task_name}")
                return False
        except Exception as e:
            self.logger.error(f"启用任务异常: {e}")
            return False
    
    def disable_task(self, task_name: str) -> bool:
        """禁用指定任务"""
        try:
            if self.scheduler_config.disable_task(task_name):
                if self.scheduler_config.save_config():
                    self.logger.info(f"成功禁用任务: {task_name}")
                    return True
                else:
                    self.logger.error("保存配置到文件失败")
                    return False
            else:
                self.logger.error(f"禁用任务失败: {task_name}")
                return False
        except Exception as e:
            self.logger.error(f"禁用任务异常: {e}")
            return False
    
    def update_realtime_intervals(self, tick_interval: int = None, bar_interval: int = None) -> bool:
        """更新实时数据收集间隔"""
        try:
            config = self.scheduler_config.get_config()
            
            if tick_interval is not None:
                config.data_collection.realtime_tick_interval = tick_interval
            
            if bar_interval is not None:
                config.data_collection.realtime_bar_interval = bar_interval
            
            self.scheduler_config.update_config(config)
            
            if self.scheduler_config.save_config():
                self.logger.info("成功更新实时数据收集间隔")
                return True
            else:
                self.logger.error("保存配置到文件失败")
                return False
        except Exception as e:
            self.logger.error(f"更新实时数据收集间隔异常: {e}")
            return False
    
    def update_supported_frequencies(self, frequencies: List[str]) -> bool:
        """更新支持的数据频率"""
        try:
            config = self.scheduler_config.get_config()
            config.data_collection.supported_frequencies = frequencies
            self.scheduler_config.update_config(config)
            
            if self.scheduler_config.save_config():
                self.logger.info(f"成功更新支持的数据频率: {frequencies}")
                return True
            else:
                self.logger.error("保存配置到文件失败")
                return False
        except Exception as e:
            self.logger.error(f"更新支持的数据频率异常: {e}")
            return False
    
    def reload_config(self) -> bool:
        """重新加载配置"""
        try:
            if self.scheduler_config.reload_config():
                self.logger.info("配置重新加载成功")
                return True
            else:
                self.logger.error("配置重新加载失败")
                return False
        except Exception as e:
            self.logger.error(f"重新加载配置异常: {e}")
            return False
    
    def export_config(self, filename: str = None) -> bool:
        """导出配置到JSON文件"""
        try:
            if not filename:
                filename = f"config_export_{self._get_timestamp()}.json"
            
            config_data = self.get_current_config()
            
            with open(filename, 'w', encoding='utf-8') as file:
                json.dump(config_data, file, ensure_ascii=False, indent=2)
            
            self.logger.info(f"配置导出成功: {filename}")
            return True
        except Exception as e:
            self.logger.error(f"导出配置异常: {e}")
            return False
    
    def import_config(self, filename: str) -> bool:
        """从JSON文件导入配置"""
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                config_data = json.load(file)
            
            # 这里可以添加配置验证逻辑
            # 暂时直接更新配置
            config = self.scheduler_config.get_config()
            
            # 更新数据收集配置
            if 'data_collection' in config_data:
                dc_data = config_data['data_collection']
                for key, value in dc_data.items():
                    if hasattr(config.data_collection, key):
                        setattr(config.data_collection, key, value)
            
            # 更新任务配置
            if 'tasks' in config_data:
                tasks = []
                for task_data in config_data['tasks']:
                    from src.config.scheduler_config import TaskSchedule
                    task = TaskSchedule(**task_data)
                    tasks.append(task)
                config.tasks = tasks
            
            self.scheduler_config.update_config(config)
            
            if self.scheduler_config.save_config():
                self.logger.info(f"配置导入成功: {filename}")
                return True
            else:
                self.logger.error("保存配置到文件失败")
                return False
        except Exception as e:
            self.logger.error(f"导入配置异常: {e}")
            return False
    
    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要信息"""
        try:
            config = self.scheduler_config.get_config()
            
            summary = {
                "股票配置": {
                    "上海市场": len(config.data_collection.default_sh_symbols),
                    "深圳市场": len(config.data_collection.default_sz_symbols),
                    "总计": len(config.data_collection.default_sh_symbols) + len(config.data_collection.default_sz_symbols)
                },
                "任务配置": {
                    "总任务数": len(config.tasks),
                    "启用任务数": len([t for t in config.tasks if t.enabled]),
                    "禁用任务数": len([t for t in config.tasks if not t.enabled])
                },
                "数据收集配置": {
                    "Tick数据间隔": f"{config.data_collection.realtime_tick_interval}秒",
                    "Bar数据间隔": f"{config.data_collection.realtime_bar_interval}秒",
                    "支持频率": config.data_collection.supported_frequencies
                },
                "交易时间": config.data_collection.trading_hours
            }
            
            return summary
        except Exception as e:
            self.logger.error(f"获取配置摘要异常: {e}")
            return {}
    
    def _get_timestamp(self) -> str:
        """获取时间戳字符串"""
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d_%H%M%S")


# 全局配置管理器实例
config_manager = ConfigManager()


def get_config_manager() -> ConfigManager:
    """获取配置管理器实例"""
    return config_manager
