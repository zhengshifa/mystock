"""
增量同步管理器
支持指定时间范围的数据同步，具备断点续传和数据完整性检查功能
"""
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from src.collectors.gm_collector import GMCollector
from src.database.mongodb_client import MongoDBClient
from src.config.scheduler_config import get_scheduler_config
from src.utils.logger import get_logger
from src.utils.helpers import format_symbol


class IncrementalSyncManager:
    """增量同步管理器"""
    
    def __init__(self):
        """初始化增量同步管理器"""
        self.logger = get_logger("IncrementalSyncManager")
        self.gm_collector = GMCollector()
        self.mongodb_client = MongoDBClient()
        self.scheduler_config = get_scheduler_config()
        
        # 同步状态记录
        self.sync_status = {}
    
    def sync_data_range(self, symbols: List[str], frequency: str, 
                        start_date: str, end_date: str = None,
                        batch_size: int = 1000, force_sync: bool = False) -> Dict[str, Any]:
        """
        同步指定时间范围的数据
        
        Args:
            symbols: 股票代码列表
            frequency: 数据频率 (1m, 5m, 15m, 1h, 1d)
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)，默认为今天
            batch_size: 批处理大小
            force_sync: 是否强制重新同步
        
        Returns:
            同步结果统计
        """
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        self.logger.info(f"开始增量同步 {frequency} 数据: {start_date} 到 {end_date}")
        
        # 创建同步任务ID
        sync_id = f"sync_{frequency}_{start_date}_{end_date}_{int(time.time())}"
        
        try:
            # 检查数据完整性
            if not force_sync:
                missing_ranges = self._check_data_completeness(symbols, frequency, start_date, end_date)
                if not missing_ranges:
                    self.logger.info(f"数据已完整，无需同步: {frequency}")
                    return {
                        "sync_id": sync_id,
                        "status": "completed",
                        "message": "数据已完整",
                        "symbols_count": len(symbols),
                        "frequency": frequency,
                        "start_date": start_date,
                        "end_date": end_date,
                        "records_synced": 0
                    }
            
            # 执行增量同步
            sync_result = self._execute_incremental_sync(
                symbols, frequency, start_date, end_date, batch_size, sync_id
            )
            
            # 更新同步状态
            self.sync_status[sync_id] = {
                "status": "completed",
                "result": sync_result,
                "completed_at": datetime.now().isoformat()
            }
            
            self.logger.info(f"增量同步完成: {sync_id}")
            return sync_result
            
        except Exception as e:
            error_msg = f"增量同步失败: {e}"
            self.logger.error(error_msg)
            
            # 记录失败状态
            self.sync_status[sync_id] = {
                "status": "failed",
                "error": str(e),
                "failed_at": datetime.now().isoformat()
            }
            
            return {
                "sync_id": sync_id,
                "status": "failed",
                "error": str(e),
                "symbols_count": len(symbols),
                "frequency": frequency,
                "start_date": start_date,
                "end_date": end_date
            }
    
    def _check_data_completeness(self, symbols: List[str], frequency: str, 
                                 start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        检查数据完整性，返回缺失的时间范围
        
        Returns:
            缺失数据的时间范围列表
        """
        missing_ranges = []
        
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            
            # 根据频率计算期望的数据条数
            expected_records = self._calculate_expected_records(start_dt, end_dt, frequency)
            
            for symbol in symbols:
                formatted_symbol = format_symbol(symbol)
                
                # 查询数据库中已有的数据
                existing_data = self.mongodb_client.get_bar_data(
                    symbol=formatted_symbol,
                    frequency=frequency,
                    start_date=start_date,
                    end_date=end_date
                )
                
                existing_count = len(existing_data) if existing_data else 0
                
                if existing_count < expected_records:
                    missing_count = expected_records - existing_count
                    missing_ranges.append({
                        "symbol": symbol,
                        "frequency": frequency,
                        "start_date": start_date,
                        "end_date": end_date,
                        "expected": expected_records,
                        "existing": existing_count,
                        "missing": missing_count
                    })
                    
                    self.logger.debug(f"{symbol} {frequency} 数据缺失: {missing_count}/{expected_records}")
        
        except Exception as e:
            self.logger.error(f"检查数据完整性失败: {e}")
        
        return missing_ranges
    
    def _calculate_expected_records(self, start_dt: datetime, end_dt: datetime, 
                                   frequency: str) -> int:
        """计算期望的数据条数"""
        try:
            if frequency == '1d':
                # 日线数据：工作日数量
                days = (end_dt - start_dt).days + 1
                # 简单估算，实际应该排除节假日
                return max(1, days)
            
            elif frequency == '1h':
                # 小时数据：交易时间 9:30-11:30, 13:00-15:00
                trading_hours = 4  # 每天4小时交易时间
                days = (end_dt - start_dt).days + 1
                return max(1, days * trading_hours)
            
            elif frequency in ['1m', '5m', '15m']:
                # 分钟数据
                if frequency == '1m':
                    minutes_per_day = 240  # 4小时 * 60分钟
                elif frequency == '5m':
                    minutes_per_day = 48   # 4小时 * 12个5分钟
                else:  # 15m
                    minutes_per_day = 16   # 4小时 * 4个15分钟
                
                days = (end_dt - start_dt).days + 1
                return max(1, days * minutes_per_day)
            
            else:
                return 1
                
        except Exception as e:
            self.logger.error(f"计算期望记录数失败: {e}")
            return 1
    
    def _execute_incremental_sync(self, symbols: List[str], frequency: str,
                                  start_date: str, end_date: str, 
                                  batch_size: int, sync_id: str) -> Dict[str, Any]:
        """执行增量同步"""
        total_records = 0
        success_symbols = []
        failed_symbols = []
        
        self.logger.info(f"开始执行增量同步: {len(symbols)} 只股票")
        
        # 更新同步状态
        self.sync_status[sync_id] = {
            "status": "running",
            "progress": 0,
            "total_symbols": len(symbols),
            "started_at": datetime.now().isoformat()
        }
        
        for i, symbol in enumerate(symbols):
            try:
                self.logger.info(f"同步 {symbol} {frequency} 数据... ({i+1}/{len(symbols)})")
                
                # 获取数据
                bar_data_list = self.gm_collector.get_bar_data(
                    symbols=[symbol],
                    frequency=frequency,
                    start_date=start_date,
                    end_date=end_date
                )
                
                if bar_data_list:
                    # 批量插入数据库
                    result = self.mongodb_client.batch_insert_bar_data(bar_data_list, frequency)
                    
                    if result and result.get('inserted_count', 0) > 0:
                        total_records += result['inserted_count']
                        success_symbols.append(symbol)
                        self.logger.info(f"{symbol} 同步成功: {result['inserted_count']} 条记录")
                    else:
                        failed_symbols.append(symbol)
                        self.logger.warning(f"{symbol} 同步失败: 无数据插入")
                else:
                    failed_symbols.append(symbol)
                    self.logger.warning(f"{symbol} 同步失败: 未获取到数据")
                
                # 更新进度
                progress = int((i + 1) / len(symbols) * 100)
                self.sync_status[sync_id]["progress"] = progress
                
                # 避免请求过于频繁
                time.sleep(0.5)
                
            except Exception as e:
                failed_symbols.append(symbol)
                self.logger.error(f"{symbol} 同步异常: {e}")
                continue
        
        # 构建结果
        result = {
            "sync_id": sync_id,
            "status": "completed",
            "symbols_count": len(symbols),
            "success_count": len(success_symbols),
            "failed_count": len(failed_symbols),
            "total_records": total_records,
            "frequency": frequency,
            "start_date": start_date,
            "end_date": end_date,
            "success_symbols": success_symbols,
            "failed_symbols": failed_symbols,
            "completed_at": datetime.now().isoformat()
        }
        
        self.logger.info(f"增量同步完成: 成功 {len(success_symbols)} 只，失败 {len(failed_symbols)} 只")
        return result
    
    def sync_from_last_record(self, symbols: List[str], frequency: str, 
                             days_back: int = 30) -> Dict[str, Any]:
        """
        从最后一条记录开始增量同步
        
        Args:
            symbols: 股票代码列表
            frequency: 数据频率
            days_back: 如果找不到最后记录，往前推多少天
        
        Returns:
            同步结果
        """
        self.logger.info(f"开始从最后记录同步 {frequency} 数据")
        
        sync_results = {}
        
        for symbol in symbols:
            try:
                # 查找最后一条记录
                last_record = self.mongodb_client.get_last_bar_data(symbol, frequency)
                
                if last_record and last_record.get('eob'):
                    # 从最后记录的下一个时间点开始
                    start_date = last_record['eob'] + timedelta(days=1)
                    start_date_str = start_date.strftime('%Y-%m-%d')
                else:
                    # 没有记录，使用默认时间
                    start_date_str = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
                
                end_date_str = datetime.now().strftime('%Y-%m-%d')
                
                # 执行增量同步
                result = self.sync_data_range(
                    symbols=[symbol],
                    frequency=frequency,
                    start_date=start_date_str,
                    end_date=end_date_str
                )
                
                sync_results[symbol] = result
                
            except Exception as e:
                self.logger.error(f"{symbol} 从最后记录同步失败: {e}")
                sync_results[symbol] = {
                    "status": "failed",
                    "error": str(e)
                }
        
        return sync_results
    
    def get_sync_status(self, sync_id: str = None) -> Dict[str, Any]:
        """获取同步状态"""
        if sync_id:
            return self.sync_status.get(sync_id, {})
        else:
            return self.sync_status
    
    def resume_failed_sync(self, sync_id: str) -> Dict[str, Any]:
        """恢复失败的同步任务"""
        if sync_id not in self.sync_status:
            return {"status": "failed", "error": "同步任务不存在"}
        
        sync_info = self.sync_status[sync_id]
        if sync_info.get("status") != "failed":
            return {"status": "failed", "error": "同步任务未失败，无法恢复"}
        
        # 这里可以实现恢复逻辑
        # 暂时返回错误信息
        return {"status": "failed", "error": "恢复功能暂未实现"}
    
    def cleanup_sync_status(self, days: int = 7) -> int:
        """清理旧的同步状态记录"""
        try:
            cutoff_time = datetime.now() - timedelta(days=days)
            cleaned_count = 0
            
            sync_ids_to_remove = []
            for sync_id, status_info in self.sync_status.items():
                if "completed_at" in status_info:
                    completed_time = datetime.fromisoformat(status_info["completed_at"])
                    if completed_time < cutoff_time:
                        sync_ids_to_remove.append(sync_id)
                elif "failed_at" in status_info:
                    failed_time = datetime.fromisoformat(status_info["failed_at"])
                    if failed_time < cutoff_time:
                        sync_ids_to_remove.append(sync_id)
            
            for sync_id in sync_ids_to_remove:
                del self.sync_status[sync_id]
                cleaned_count += 1
            
            self.logger.info(f"清理了 {cleaned_count} 条旧的同步状态记录")
            return cleaned_count
            
        except Exception as e:
            self.logger.error(f"清理同步状态失败: {e}")
            return 0
    
    def close(self):
        """关闭增量同步管理器"""
        try:
            self.gm_collector.close()
            self.mongodb_client.close()
            self.logger.info("增量同步管理器已关闭")
        except Exception as e:
            self.logger.error(f"关闭增量同步管理器失败: {e}")


# 全局增量同步管理器实例
incremental_sync_manager = IncrementalSyncManager()


def get_incremental_sync_manager() -> IncrementalSyncManager:
    """获取增量同步管理器实例"""
    return incremental_sync_manager
