"""
数据同步模块
实现增量数据同步和实时数据获取
"""
import asyncio
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from ..services import GMService
from ..database import mongodb_client
from ..config import settings
from ..models import Tick, Bar


class DataSyncService:
    """数据同步服务"""
    
    def __init__(self):
        """初始化数据同步服务"""
        self.logger = logging.getLogger(__name__)
        self.gm_service = GMService()
        self.is_running = False
    
    async def sync_history_data(self, symbols: List[str], 
                               start_date: Optional[str] = None,
                               end_date: Optional[str] = None,
                               frequency: str = '1d') -> Dict[str, bool]:
        """
        同步历史数据
        
        Args:
            symbols: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            frequency: 数据频率
            
        Returns:
            Dict[str, bool]: 每个股票的同步结果
        """
        results = {}
        
        for symbol in symbols:
            try:
                self.logger.info(f"开始同步历史数据: {symbol}")
                start_time = datetime.now()
                
                # 获取最新的Bar时间
                latest_time = await mongodb_client.get_latest_bar_time(symbol, frequency)
                
                if latest_time:
                    # 增量同步：从最新时间开始
                    if frequency == '1d':
                        sync_start = latest_time + timedelta(days=1)
                        sync_start_str = sync_start.strftime('%Y-%m-%d')
                    else:
                        # 对于分钟级数据，从最新时间开始
                        sync_start_str = latest_time.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    # 全量同步：使用配置的开始日期
                    sync_start_str = start_date or settings.start_date
                
                sync_end_str = end_date or settings.end_date
                
                # 获取历史数据
                history_data = self.gm_service.get_history_data(
                    symbol=symbol,
                    frequency=frequency,
                    start_time=sync_start_str,
                    end_time=sync_end_str,
                    df=False
                )
                
                if history_data:
                    # 转换为字典格式
                    bar_data = [bar.to_dict() for bar in history_data]
                    
                    # 保存到数据库
                    success = await mongodb_client.upsert_bar_data(bar_data, frequency)
                    
                    # 记录同步日志
                    await mongodb_client.log_sync_operation(
                        symbol=symbol,
                        operation_type=f'bar_{frequency}',
                        start_time=start_time,
                        end_time=datetime.now(),
                        record_count=len(bar_data),
                        status='success' if success else 'failed'
                    )
                    
                    results[symbol] = success
                    self.logger.info(f"{frequency}历史数据同步完成: {symbol}, 记录数: {len(bar_data)}")
                else:
                    results[symbol] = True
                    self.logger.info(f"{frequency}历史数据同步完成: {symbol}, 无新数据")
                
            except Exception as e:
                self.logger.error(f"同步历史数据失败: {symbol}, 错误: {e}")
                
                # 记录错误日志
                await mongodb_client.log_sync_operation(
                    symbol=symbol,
                    operation_type=f'bar_{frequency}',
                    start_time=datetime.now(),
                    end_time=datetime.now(),
                    record_count=0,
                    status='failed',
                    error_message=str(e)
                )
                
                results[symbol] = False
        
        return results
    
    async def sync_realtime_data(self, symbols: List[str]) -> Dict[str, bool]:
        """
        同步实时数据
        
        Args:
            symbols: 股票代码列表
            
        Returns:
            Dict[str, bool]: 每个股票的同步结果
        """
        results = {}
        
        try:
            self.logger.info(f"开始同步实时数据: {symbols}")
            start_time = datetime.now()
            
            # 获取实时数据
            current_data = self.gm_service.get_current_data(symbols=symbols)
            
            if current_data:
                # 转换为字典格式
                tick_data = [tick.to_dict() for tick in current_data]
                
                # 保存到数据库
                success = await mongodb_client.insert_tick_data(tick_data)
                
                # 记录同步日志
                for tick in current_data:
                    await mongodb_client.log_sync_operation(
                        symbol=tick.symbol,
                        operation_type='tick',
                        start_time=start_time,
                        end_time=datetime.now(),
                        record_count=1,
                        status='success' if success else 'failed'
                    )
                
                results = {tick.symbol: success for tick in current_data}
                self.logger.info(f"实时数据同步完成, 记录数: {len(tick_data)}")
            else:
                self.logger.warning("未获取到实时数据")
                results = {symbol: False for symbol in symbols}
        
        except Exception as e:
            self.logger.error(f"同步实时数据失败: {e}")
            
            # 记录错误日志
            for symbol in symbols:
                await mongodb_client.log_sync_operation(
                    symbol=symbol,
                    operation_type='tick',
                    start_time=start_time,
                    end_time=datetime.now(),
                    record_count=0,
                    status='failed',
                    error_message=str(e)
                )
            
            results = {symbol: False for symbol in symbols}
        
        return results
    
    async def sync_minute_data(self, symbols: List[str], 
                              minutes_back: int = 60,
                              frequency: str = '60s') -> Dict[str, bool]:
        """
        同步分钟级数据
        
        Args:
            symbols: 股票代码列表
            minutes_back: 回溯分钟数
            frequency: 数据频率
            
        Returns:
            Dict[str, bool]: 每个股票的同步结果
        """
        results = {}
        
        for symbol in symbols:
            try:
                self.logger.info(f"开始同步分钟数据: {symbol}")
                start_time = datetime.now()
                
                # 计算时间范围
                end_time = datetime.now()
                start_time_range = end_time - timedelta(minutes=minutes_back)
                
                # 获取分钟数据
                minute_data = self.gm_service.get_history_data(
                    symbol=symbol,
                    frequency=frequency,
                    start_time=start_time_range.strftime('%Y-%m-%d %H:%M:%S'),
                    end_time=end_time.strftime('%Y-%m-%d %H:%M:%S'),
                    df=False
                )
                
                if minute_data:
                    # 转换为字典格式
                    bar_data = [bar.to_dict() for bar in minute_data]
                    
                    # 保存到数据库
                    success = await mongodb_client.upsert_bar_data(bar_data, frequency)
                    
                    # 记录同步日志
                    await mongodb_client.log_sync_operation(
                        symbol=symbol,
                        operation_type=f'bar_{frequency}',
                        start_time=start_time,
                        end_time=datetime.now(),
                        record_count=len(bar_data),
                        status='success' if success else 'failed'
                    )
                    
                    results[symbol] = success
                    self.logger.info(f"{frequency}分钟数据同步完成: {symbol}, 记录数: {len(bar_data)}")
                else:
                    results[symbol] = True
                    self.logger.info(f"{frequency}分钟数据同步完成: {symbol}, 无新数据")
                
            except Exception as e:
                self.logger.error(f"同步分钟数据失败: {symbol}, 错误: {e}")
                
                # 记录错误日志
                await mongodb_client.log_sync_operation(
                    symbol=symbol,
                    operation_type=f'bar_{frequency}',
                    start_time=start_time,
                    end_time=datetime.now(),
                    record_count=0,
                    status='failed',
                    error_message=str(e)
                )
                
                results[symbol] = False
        
        return results
    
    async def sync_all_frequencies(self, symbols: List[str], 
                                  start_date: Optional[str] = None,
                                  end_date: Optional[str] = None) -> Dict[str, Dict[str, bool]]:
        """
        同步所有频率的历史数据
        
        Args:
            symbols: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            Dict[str, Dict[str, bool]]: 每个频率每个股票的同步结果
        """
        all_results = {}
        
        for frequency in settings.enabled_frequencies:
            if settings.is_frequency_enabled(frequency):
                self.logger.info(f"开始同步 {frequency} 频率数据")
                results = await self.sync_history_data(symbols, start_date, end_date, frequency)
                all_results[frequency] = results
            else:
                self.logger.info(f"跳过 {frequency} 频率数据同步（已禁用）")
                all_results[frequency] = {symbol: False for symbol in symbols}
        
        return all_results
    
    async def sync_realtime_frequencies(self, symbols: List[str]) -> Dict[str, Dict[str, bool]]:
        """
        同步实时多频率数据
        
        Args:
            symbols: 股票代码列表
            
        Returns:
            Dict[str, Dict[str, bool]]: 每个频率每个股票的同步结果
        """
        all_results = {}
        
        # 同步实时Tick数据
        tick_results = await self.sync_realtime_data(symbols)
        all_results['tick'] = tick_results
        
        # 同步各频率的分钟数据
        for frequency in settings.enabled_frequencies:
            if settings.is_frequency_enabled(frequency) and frequency != '1d':
                self.logger.info(f"开始同步 {frequency} 实时数据")
                results = await self.sync_minute_data(symbols, minutes_back=10, frequency=frequency)
                all_results[frequency] = results
            else:
                all_results[frequency] = {symbol: False for symbol in symbols}
        
        return all_results
    
    async def sync_incremental_data(self, symbols: List[str], days_back: int = 1) -> Dict[str, Dict[str, bool]]:
        """
        执行增量数据同步
        
        Args:
            symbols: 股票代码列表
            days_back: 向前同步的天数，0表示当日，1表示前一日
            
        Returns:
            Dict[str, Dict[str, bool]]: 每个频率每个股票的同步结果
        """
        all_results = {}
        
        try:
            self.logger.info(f"开始执行增量数据同步，向前{days_back}天")
            
            # 计算同步的日期范围
            from datetime import datetime, timedelta
            end_date = datetime.now().date() - timedelta(days=days_back)
            start_date = end_date - timedelta(days=1)
            
            start_date_str = start_date.strftime('%Y-%m-%d')
            end_date_str = end_date.strftime('%Y-%m-%d')
            
            self.logger.info(f"增量同步日期范围: {start_date_str} 到 {end_date_str}")
            
            # 同步所有频率的历史数据
            for frequency in settings.enabled_frequencies:
                if settings.is_frequency_enabled(frequency):
                    self.logger.info(f"开始增量同步 {frequency} 数据")
                    results = await self.sync_history_data(
                        symbols, 
                        start_date=start_date_str, 
                        end_date=end_date_str, 
                        frequency=frequency
                    )
                    all_results[frequency] = results
                else:
                    all_results[frequency] = {symbol: False for symbol in symbols}
            
            # 统计总体成功率
            total_success = 0
            total_count = 0
            for freq_results in all_results.values():
                for success in freq_results.values():
                    total_count += 1
                    if success:
                        total_success += 1
            
            self.logger.info(f"增量数据同步完成: {total_success}/{total_count} 成功")
            
        except Exception as e:
            self.logger.error(f"增量数据同步失败: {e}")
            # 返回失败结果
            for frequency in settings.enabled_frequencies:
                all_results[frequency] = {symbol: False for symbol in symbols}
        
        return all_results
    
    async def is_trading_time(self) -> bool:
        """
        判断是否在交易时间
        
        Returns:
            bool: 是否在交易时间
        """
        now = datetime.now()
        current_time = now.strftime('%H:%M')
        
        # 周末不交易
        if now.weekday() >= 5:  # 周末
            return False
        
        # 从配置文件读取交易时间
        morning_start = settings.trading_morning_start
        morning_end = settings.trading_morning_end
        afternoon_start = settings.trading_afternoon_start
        afternoon_end = settings.trading_afternoon_end
        
        # 上午交易时间
        if morning_start <= current_time <= morning_end:
            return True
        
        # 下午交易时间
        if afternoon_start <= current_time <= afternoon_end:
            return True
        
        return False
    
    async def is_pre_market_time(self) -> bool:
        """
        判断是否在开盘前时间（适合做增量同步）
        
        Returns:
            bool: 是否在开盘前时间
        """
        now = datetime.now()
        current_time = now.strftime('%H:%M')
        
        # 周末不执行
        if now.weekday() >= 5:
            return False
        
        # 开盘前时间：08:30-09:30
        pre_market_start = "08:30"
        pre_market_end = "09:30"
        
        return pre_market_start <= current_time <= pre_market_end
    
    async def is_post_market_time(self) -> bool:
        """
        判断是否在收盘后时间（适合做增量同步）
        
        Returns:
            bool: 是否在收盘后时间
        """
        now = datetime.now()
        current_time = now.strftime('%H:%M')
        
        # 周末不执行
        if now.weekday() >= 5:
            return False
        
        # 收盘后时间：15:30-16:30
        post_market_start = "15:30"
        post_market_end = "16:30"
        
        return post_market_start <= current_time <= post_market_end
    
    async def start_realtime_sync(self, symbols: List[str]):
        """
        启动实时数据同步
        
        Args:
            symbols: 股票代码列表
        """
        self.is_running = True
        self.logger.info(f"启动实时数据同步: {symbols}")
        
        while self.is_running:
            try:
                if await self.is_trading_time():
                    # 在交易时间内同步实时数据
                    await self.sync_realtime_frequencies(symbols)
                
                # 等待下次同步
                await asyncio.sleep(settings.realtime_interval_seconds)
                
            except Exception as e:
                self.logger.error(f"实时数据同步异常: {e}")
                await asyncio.sleep(settings.retry_delay_seconds)
    
    def stop_realtime_sync(self):
        """停止实时数据同步"""
        self.is_running = False
        self.logger.info("停止实时数据同步")
    
    async def get_sync_status(self) -> Dict:
        """
        获取同步状态
        
        Returns:
            Dict: 同步状态信息
        """
        try:
            # 获取最近的同步记录
            recent_logs = await mongodb_client.get_sync_history(limit=10)
            
            # 统计成功和失败次数
            success_count = sum(1 for log in recent_logs if log['status'] == 'success')
            failed_count = sum(1 for log in recent_logs if log['status'] == 'failed')
            
            return {
                'is_running': self.is_running,
                'is_trading_time': await self.is_trading_time(),
                'recent_sync_count': len(recent_logs),
                'success_count': success_count,
                'failed_count': failed_count,
                'last_sync_time': recent_logs[0]['sync_time'] if recent_logs else None
            }
            
        except Exception as e:
            self.logger.error(f"获取同步状态失败: {e}")
            return {
                'is_running': self.is_running,
                'is_trading_time': False,
                'error': str(e)
            }
