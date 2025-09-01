"""
数据调度器类
包含定时任务管理
"""
import schedule
import time
import threading
from datetime import datetime, timedelta
from typing import List, Optional, Callable, Dict
from src.config.settings import get_settings
from src.config.scheduler_config import get_scheduler_config
from src.utils.logger import get_logger
from src.utils.helpers import is_trading_time
from src.collectors.gm_collector import GMCollector
from src.database.mongodb_client import MongoDBClient


class DataScheduler:
    """数据调度器"""
    
    def __init__(self):
        """初始化数据调度器"""
        self.logger = get_logger("DataScheduler")
        self.gm_collector = GMCollector()
        self.mongodb_client = MongoDBClient()
        self.is_running = False
        self.scheduler_thread = None
        
        # 获取调度配置
        self.scheduler_config = get_scheduler_config()
        
        # 从配置获取股票列表
        self.default_symbols = self.scheduler_config.get_stock_symbols()
    
    def start(self) -> None:
        """启动调度器"""
        if self.is_running:
            self.logger.warning("调度器已在运行中")
            return
        
        try:
            self.logger.info("启动数据调度器")
            
            # 设置定时任务
            self._setup_schedule()
            
            # 启动调度器线程
            self.is_running = True
            self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self.scheduler_thread.start()
            
            self.logger.info("数据调度器启动成功")
            
        except Exception as e:
            self.logger.error(f"启动调度器失败: {e}")
            raise
    
    def stop(self) -> None:
        """停止调度器"""
        if not self.is_running:
            self.logger.warning("调度器未在运行")
            return
        
        try:
            self.logger.info("停止数据调度器")
            self.is_running = False
            
            # 等待调度器线程结束
            if self.scheduler_thread and self.scheduler_thread.is_alive():
                self.scheduler_thread.join(timeout=5)
            
            self.logger.info("数据调度器已停止")
            
        except Exception as e:
            self.logger.error(f"停止调度器失败: {e}")
    
    def _setup_schedule(self) -> None:
        """设置定时任务"""
        try:
            # 清除所有现有任务
            schedule.clear()
            
            # 从配置获取启用的任务
            enabled_tasks = self.scheduler_config.get_enabled_tasks()
            
            for task in enabled_tasks:
                if not task.enabled:
                    continue
                
                try:
                    if task.interval_type == "seconds":
                        schedule.every(task.interval_value).seconds.do(
                            self._get_task_function(task.name)
                        )
                    elif task.interval_type == "minutes":
                        schedule.every(task.interval_value).minutes.do(
                            self._get_task_function(task.name)
                        )
                    elif task.interval_type == "hours":
                        schedule.every(task.interval_value).hours.do(
                            self._get_task_function(task.name)
                        )
                    elif task.interval_type == "daily" and task.at_time:
                        schedule.every().day.at(task.at_time).do(
                            self._get_task_function(task.name)
                        )
                    
                    self.logger.info(f"任务调度设置成功: {task.name} ({task.interval_type}: {task.interval_value})")
                    
                except Exception as e:
                    self.logger.error(f"设置任务调度失败 {task.name}: {e}")
            
            self.logger.info(f"定时任务设置完成，共 {len(enabled_tasks)} 个任务")
            
        except Exception as e:
            self.logger.error(f"设置定时任务失败: {e}")
            raise
    
    def _get_task_function(self, task_name: str) -> Callable:
        """根据任务名称获取对应的函数"""
        task_functions = {
            "实时数据同步": self._sync_realtime_data,
            "开盘前全量同步": self._sync_all_data,
            "午盘前全量同步": self._sync_all_data,
            "收盘后全量同步": self._sync_all_data,
            "市场状态检查": self._check_market_status
        }
        return task_functions.get(task_name, self._default_task)
    
    def _default_task(self) -> None:
        """默认任务处理函数"""
        self.logger.warning("未找到对应的任务处理函数")
    
    def _run_scheduler(self) -> None:
        """运行调度器主循环"""
        self.logger.info("调度器主循环开始运行")
        
        # 从配置获取调度器运行参数
        scheduler_params = self.scheduler_config.get_scheduler_config()
        sleep_interval = scheduler_params.get("sleep_interval", 1)
        exception_wait = scheduler_params.get("exception_wait", 5)
        
        while self.is_running:
            try:
                # 运行待执行的任务
                schedule.run_pending()
                
                # 短暂休眠
                time.sleep(sleep_interval)
                
            except Exception as e:
                self.logger.error(f"调度器运行异常: {e}")
                time.sleep(exception_wait)  # 异常时等待更长时间
        
        self.logger.info("调度器主循环已停止")
    
    def _collect_tick_data(self) -> None:
        """收集Tick数据"""
        try:
            # 检查是否为交易时间
            if not is_trading_time():
                self.logger.debug("非交易时间，跳过Tick数据收集")
                return
            
            self.logger.info("开始收集Tick数据")
            
            # 获取Tick数据
            tick_data_list = self.gm_collector.get_tick_data(self.default_symbols)
            
            if tick_data_list:
                # 批量插入数据库
                result = self.mongodb_client.batch_insert_tick_data(tick_data_list)
                self.logger.info(f"Tick数据收集完成: {result}")
            else:
                self.logger.warning("未获取到Tick数据")
                
        except Exception as e:
            self.logger.error(f"收集Tick数据失败: {e}")
    
    def _collect_bar_data(self, frequency: str = '60s') -> None:
        """收集指定频率的Bar数据"""
        try:
            # 检查是否为交易时间
            if not is_trading_time():
                self.logger.debug(f"非交易时间，跳过{frequency}数据收集")
                return
            
            self.logger.info(f"开始收集{frequency}数据")
            
            # 获取指定频率的K线数据
            bar_data_list = self.gm_collector.get_bar_data(
                symbols=self.default_symbols,
                frequency=frequency
            )
            
            if bar_data_list:
                # 批量插入数据库
                result = self.mongodb_client.batch_insert_bar_data(bar_data_list, frequency)
                self.logger.info(f"{frequency}数据收集完成: {result}")
            else:
                self.logger.warning(f"未获取到{frequency}数据")
                
        except Exception as e:
            self.logger.error(f"收集{frequency}数据失败: {e}")
    
    def _collect_daily_data(self) -> None:
        """收集每日数据"""
        try:
            self.logger.info("开始收集每日数据")
            
            # 获取日线数据
            bar_data_list = self.gm_collector.get_bar_data(
                symbols=self.default_symbols,
                frequency='1d',
                start_date=(datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
                end_date=datetime.now().strftime('%Y-%m-%d')
            )
            
            if bar_data_list:
                # 批量插入数据库到1d集合
                result = self.mongodb_client.batch_insert_bar_data(bar_data_list, '1d')
                self.logger.info(f"每日数据收集完成: {result}")
            else:
                self.logger.warning("未获取到每日数据")
                
        except Exception as e:
            self.logger.error(f"收集每日数据失败: {e}")
    
    def _sync_realtime_data(self) -> None:
        """同步实时数据（交易时间每30秒执行）"""
        try:
            # 检查是否为交易时间
            if not is_trading_time():
                self.logger.debug("非交易时间，跳过实时数据同步")
                return
            
            self.logger.info("开始同步实时数据...")
            
            # 从配置获取实时数据间隔
            realtime_intervals = self.scheduler_config.get_realtime_intervals()
            tick_interval = realtime_intervals.get("tick", 30)
            bar_interval = realtime_intervals.get("bar", 60)
            
            # 同步Tick数据
            tick_data_list = self.gm_collector.get_tick_data(self.default_symbols)
            if tick_data_list:
                result = self.mongodb_client.batch_insert_tick_data(tick_data_list)
                self.logger.info(f"Tick数据同步完成: {result}")
            
            # 同步1分钟K线数据
            bar_data_list = self.gm_collector.get_bar_data(
                symbols=self.default_symbols,
                frequency='60s'
            )
            if bar_data_list:
                result = self.mongodb_client.batch_insert_bar_data(bar_data_list, '60s')
                self.logger.info(f"1分钟K线数据同步完成: {result}")
            
            self.logger.info("实时数据同步完成")
            
        except Exception as e:
            self.logger.error(f"实时数据同步失败: {e}")
    
    def _sync_all_data(self) -> None:
        """全量同步所有数据"""
        try:
            self.logger.info("开始全量同步所有数据...")
            
            # 同步Tick数据
            tick_data_list = self.gm_collector.get_tick_data(self.default_symbols)
            if tick_data_list:
                result = self.mongodb_client.batch_insert_tick_data(tick_data_list)
                self.logger.info(f"Tick数据全量同步完成: {result}")
            
            # 从配置获取支持的数据频率
            supported_frequencies = self.scheduler_config.get_supported_frequencies()
            
            # 同步不同频率的K线数据
            for freq in supported_frequencies:
                bar_data_list = self.gm_collector.get_bar_data(
                    symbols=self.default_symbols,
                    frequency=freq
                )
                if bar_data_list:
                    result = self.mongodb_client.batch_insert_bar_data(bar_data_list, freq)
                    self.logger.info(f"{freq}数据全量同步完成: {result}")
            
            self.logger.info("全量数据同步完成")
            
        except Exception as e:
            self.logger.error(f"全量数据同步失败: {e}")
    
    def _check_market_status(self) -> None:
        """检查市场状态"""
        try:
            is_open = self.gm_collector.is_market_open()
            if is_open:
                self.logger.debug("市场开放")
            else:
                self.logger.debug("市场关闭")
                
        except Exception as e:
            self.logger.error(f"检查市场状态失败: {e}")
    
    def add_custom_task(self, task_func: Callable, interval: str, 
                        at_time: str = None) -> None:
        """添加自定义任务"""
        try:
            if interval == 'minutes':
                schedule.every(1).minutes.do(task_func)
            elif interval == 'hours':
                schedule.every(1).hours.do(task_func)
            elif interval == 'daily' and at_time:
                schedule.every().day.at(at_time).do(task_func)
            else:
                self.logger.warning(f"不支持的定时任务类型: {interval}")
                return
            
            self.logger.info(f"自定义任务添加成功: {task_func.__name__}")
            
        except Exception as e:
            self.logger.error(f"添加自定义任务失败: {e}")
    
    def get_scheduled_jobs(self) -> List[Dict]:
        """获取已调度的任务列表"""
        try:
            jobs = []
            for job in schedule.jobs:
                jobs.append({
                    'function': job.job_func.__name__,
                    'next_run': job.next_run,
                    'interval': str(job.interval),
                    'unit': job.unit
                })
            return jobs
        except Exception as e:
            self.logger.error(f"获取任务列表失败: {e}")
            return []
    
    def clear_all_jobs(self) -> None:
        """清除所有任务"""
        try:
            schedule.clear()
            self.logger.info("所有定时任务已清除")
        except Exception as e:
            self.logger.error(f"清除任务失败: {e}")
    
    def reload_config(self) -> bool:
        """重新加载配置"""
        try:
            if self.scheduler_config.reload_config():
                # 更新股票列表
                self.default_symbols = self.scheduler_config.get_stock_symbols()
                self.logger.info("配置重新加载成功")
                return True
            else:
                self.logger.error("配置重新加载失败")
                return False
        except Exception as e:
            self.logger.error(f"重新加载配置失败: {e}")
            return False
    
    def close(self) -> None:
        """关闭调度器"""
        try:
            self.stop()
            self.gm_collector.close()
            self.mongodb_client.close()
            self.logger.info("调度器已完全关闭")
        except Exception as e:
            self.logger.error(f"关闭调度器失败: {e}")
