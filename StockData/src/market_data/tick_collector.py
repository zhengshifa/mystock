#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tick数据采集器
专门负责Tick数据的获取、存储和分析
"""

import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config import config
from utils import db_manager, gm_client, get_logger
from models import Tick, QuoteLevel

# 获取日志记录器
logger = get_logger(__name__)


class TickDataCollector:
    """Tick数据采集器 - 专门处理Tick数据"""
    
    def __init__(self):
        """初始化Tick数据采集器"""
        self.db_manager = db_manager
        self.gm_client = gm_client
        self._init_connections()
    
    def _init_connections(self):
        """初始化连接"""
        # 初始化数据库连接
        if not self.db_manager.connect():
            raise Exception("数据库连接失败")
        
        # 初始化GM SDK连接
        if not self.gm_client.connect():
            raise Exception("GM SDK连接失败")
    
    def get_history_tick_data(self, symbol: str, start_time: str, end_time: str) -> List[Dict[str, Any]]:
        """获取历史Tick数据
        
        Args:
            symbol: 标的代码
            start_time: 开始时间，格式：'2023-01-01' 或 '2023-01-01 09:30:00'
            end_time: 结束时间，格式：'2023-12-31' 或 '2023-12-31 15:00:00'
        
        Returns:
            历史Tick数据列表
        """
        try:
            logger.info(f"开始获取历史Tick数据: {symbol}, 时间范围: {start_time} 到 {end_time}")
            
            ticks = self.gm_client.get_history_tick_data(symbol, start_time, end_time)
            
            if ticks:
                logger.info(f"成功获取{len(ticks)}条历史Tick数据: {symbol}")
                
                # 记录数据统计信息
                prices = [tick['price'] for tick in ticks if tick['price'] > 0]
                if prices:
                    logger.info(f"Tick数据统计 - 价格范围: {min(prices):.2f} - {max(prices):.2f}, "
                              f"平均价格: {sum(prices)/len(prices):.2f}")
            else:
                logger.warning(f"未获取到历史Tick数据: {symbol}")
            
            return ticks
            
        except Exception as e:
            logger.error(f"获取历史Tick数据失败: {e}")
            return []
    
    def get_multi_symbol_history_tick_data(self, symbols: List[str], start_time: str, end_time: str) -> Dict[str, List[Dict[str, Any]]]:
        """获取多个标的的历史Tick数据
        
        Args:
            symbols: 标的代码列表
            start_time: 开始时间
            end_time: 结束时间
        
        Returns:
            按标的分组的历史Tick数据字典
        """
        try:
            logger.info(f"开始获取多标的历史Tick数据: {symbols}, 时间范围: {start_time} 到 {end_time}")
            
            result = self.gm_client.get_multi_symbol_history_tick_data(symbols, start_time, end_time)
            
            if result:
                total_ticks = sum(len(ticks) for ticks in result.values())
                logger.info(f"成功获取多标的历史Tick数据: 总计{total_ticks}条, "
                          f"标的分布: {dict((k, len(v)) for k, v in result.items())}")
            else:
                logger.warning(f"未获取到多标的历史Tick数据: {symbols}")
            
            return result
            
        except Exception as e:
            logger.error(f"获取多标的历史Tick数据失败: {e}")
            return {}
    
    def get_tick_data_summary(self, symbol: str, start_time: str, end_time: str) -> Dict[str, Any]:
        """获取Tick数据摘要统计
        
        Args:
            symbol: 标的代码
            start_time: 开始时间
            end_time: 结束时间
        
        Returns:
            Tick数据摘要统计信息
        """
        try:
            logger.info(f"开始生成Tick数据摘要: {symbol}, 时间范围: {start_time} 到 {end_time}")
            
            summary = self.gm_client.get_tick_data_summary(symbol, start_time, end_time)
            
            if summary:
                logger.info(f"成功生成Tick数据摘要: {symbol}")
                
                # 记录关键统计信息
                price_stats = summary.get('price_stats', {})
                if price_stats:
                    logger.info(f"价格统计 - 变化: {price_stats.get('change', 0):.2f} "
                              f"({price_stats.get('change_pct', 0):.2f}%), "
                              f"范围: {price_stats.get('min', 0):.2f} - {price_stats.get('max', 0):.2f}")
            else:
                logger.warning(f"未生成Tick数据摘要: {symbol}")
            
            return summary
            
        except Exception as e:
            logger.error(f"生成Tick数据摘要失败: {e}")
            return {}
    
    def save_tick_data_to_mongodb(self, tick_data: List[Dict[str, Any]], 
                                 collection_name: str = 'tick_data_1m') -> bool:
        """保存Tick数据到MongoDB
        
        Args:
            tick_data: Tick数据列表
            collection_name: 集合名称，默认为tick_data_1m
        
        Returns:
            是否保存成功
        """
        if not tick_data:
            logger.warning("没有Tick数据需要保存")
            return False
        
        try:
            logger.info(f"开始保存Tick数据到集合: {collection_name}")
            
            # 为每条Tick数据添加时间信息
            for tick in tick_data:
                # 获取时间信息
                created_at = tick.get('created_at')
                if created_at:
                    if isinstance(created_at, str):
                        try:
                            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        except:
                            created_at = datetime.now()
                    elif not isinstance(created_at, datetime):
                        created_at = datetime.now()
                else:
                    created_at = datetime.now()
                
                # 添加保存时间
                tick['saved_at'] = datetime.now()
                
                # 构建查询条件（标的代码 + 创建时间）
                query = {
                    'symbol': tick['symbol'],
                    'created_at': created_at
                }
                
                # 更新或插入数据
                result = self.db_manager.update_one_upsert(
                    collection_name,
                    query,
                    {'$set': tick}
                )
                
                if result:
                    logger.debug(f"保存Tick数据成功: {tick['symbol']}, {created_at}")
                else:
                    logger.warning(f"保存Tick数据失败: {tick['symbol']}, {created_at}")
            
            logger.info(f"成功保存{len(tick_data)}条Tick数据到集合: {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"保存Tick数据到MongoDB失败: {e}")
            return False
    
    def collect_and_save_tick_data(self, symbols: List[str], 
                                 start_time: str, end_time: str,
                                 save_to_db: bool = True, show_summary: bool = True) -> Dict[str, Any]:
        """采集并保存Tick数据
        
        Args:
            symbols: 标的代码列表
            start_time: 开始时间
            end_time: 结束时间
            save_to_db: 是否保存到数据库
            show_summary: 是否显示数据摘要
        
        Returns:
            采集结果统计
        """
        try:
            logger.info(f"开始采集Tick数据: {symbols}")
            
            # 获取多标的Tick数据
            multi_symbol_data = self.get_multi_symbol_history_tick_data(
                symbols=symbols,
                start_time=start_time,
                end_time=end_time
            )
            
            if not multi_symbol_data:
                logger.warning("未获取到任何Tick数据")
                return {}
            
            # 统计信息
            total_ticks = sum(len(ticks) for ticks in multi_symbol_data.values())
            result = {
                'total_symbols': len(symbols),
                'symbols_with_data': list(multi_symbol_data.keys()),
                'total_ticks': total_ticks,
                'symbol_distribution': {symbol: len(ticks) for symbol, ticks in multi_symbol_data.items()},
                'timestamp': datetime.now().isoformat()
            }
            
            # 显示数据摘要
            if show_summary:
                print(f"\n=== Tick数据采集摘要 ===")
                print(f"标的数量: {result['total_symbols']}")
                print(f"有数据的标的: {', '.join(result['symbols_with_data'])}")
                print(f"总Tick数量: {result['total_ticks']}")
                print(f"标的分布:")
                for symbol, count in result['symbol_distribution'].items():
                    print(f"  {symbol}: {count}条")
                print()
            
            # 保存到数据库
            if save_to_db:
                for symbol, ticks in multi_symbol_data.items():
                    if ticks:
                        self.save_tick_data_to_mongodb(ticks, 'tick_data_1m')
            
            logger.info(f"Tick数据采集完成: {result}")
            return result
            
        except Exception as e:
            logger.error(f"采集Tick数据失败: {e}")
            return {}
    
    def close(self):
        """关闭连接"""
        if self.db_manager:
            self.db_manager.disconnect()
            logger.info("数据库连接已关闭")
        if self.gm_client:
            self.gm_client.disconnect()
            logger.info("GM客户端连接已关闭")


def main():
    """主函数 - 演示Tick数据采集"""
    # 从配置文件读取股票代码
    symbols = config.scheduler.stock_symbols
    if not symbols:
        # 如果配置为空，使用默认的测试股票代码
        symbols = [
            'SZSE.000001',  # 平安银行
            'SZSE.000002',  # 万科A
            'SHSE.600000',  # 浦发银行
        ]
    
    collector = None
    try:
        collector = TickDataCollector()
        
        print("🚀 Tick数据采集系统")
        print("=" * 50)
        
        # 设置时间范围（最近一周）
        end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        start_time = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
        
        # 采集Tick数据
        print("\n1️⃣ 采集Tick数据...")
        tick_result = collector.collect_and_save_tick_data(
            symbols=symbols[:3],  # 只取前3只股票进行演示
            start_time=start_time,
            end_time=end_time,
            save_to_db=True,
            show_summary=True
        )
        
        if tick_result:
            print("✅ Tick数据采集完成")
        
        print("\n🎉 Tick数据采集完成！")
        
    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if collector:
            collector.close()


if __name__ == "__main__":
    main()
