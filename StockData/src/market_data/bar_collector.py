#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bar数据采集器
专门负责Bar数据的获取、存储和管理
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
from models import Bar

# 获取日志记录器
logger = get_logger(__name__)


class BarDataCollector:
    """Bar数据采集器 - 专门处理Bar数据"""
    
    def __init__(self):
        """初始化Bar数据采集器"""
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
    
    def get_bar_data(self, symbols: List[str], frequency: str = '1d', 
                    start_time: str = None, end_time: str = None,
                    fields: str = None, adjust: str = 'PREV') -> List[Dict[str, Any]]:
        """获取Bar数据 - 各种频率的行情数据
        
        Args:
            symbols: 标的代码列表
            frequency: 频率，支持多种频率
            start_time: 开始时间，格式：'2023-01-01' 或 '2023-01-01 09:30:00'
            end_time: 结束时间，格式：'2023-12-31' 或 '2023-12-31 15:00:00'
            fields: 字段列表，默认获取OHLCV数据
            adjust: 复权类型，'PREV'前复权, 'NEXT'后复权, 'NONE'不复权
        
        Returns:
            Bar数据列表
        """
        try:
            logger.info(f"开始获取Bar数据: {symbols}, 频率: {frequency}")
            
            bars = self.gm_client.get_bar_data(
                symbols=symbols,
                frequency=frequency,
                start_time=start_time,
                end_time=end_time,
                fields=fields,
                adjust=adjust
            )
            
            if bars:
                logger.info(f"成功获取{len(bars)}条Bar数据: {symbols}, 频率: {frequency}")
            else:
                logger.warning(f"未获取到Bar数据: {symbols}, 频率: {frequency}")
            
            return bars
            
        except Exception as e:
            logger.error(f"获取Bar数据失败: {e}")
            return []
    
    def get_multi_frequency_bars(self, symbols: List[str], 
                                frequencies: List[str] = None,
                                start_time: str = None, end_time: str = None) -> Dict[str, List[Dict[str, Any]]]:
        """获取多种频率的Bar数据
        
        Args:
            symbols: 标的代码列表
            frequencies: 频率列表，默认获取常用频率
            start_time: 开始时间
            end_time: 结束时间
        
        Returns:
            按频率分组的Bar数据字典
        """
        try:
            if not frequencies:
                frequencies = ['1m', '5m', '15m', '30m', '1h', '1d']
            
            logger.info(f"开始获取多频率Bar数据: {symbols}, 频率: {frequencies}")
            
            result = self.gm_client.get_multi_frequency_bars(
                symbols=symbols,
                frequencies=frequencies,
                start_time=start_time,
                end_time=end_time
            )
            
            total_bars = sum(len(bars) for bars in result.values())
            logger.info(f"成功获取多频率Bar数据: 总计{total_bars}条, 频率分布: {dict((k, len(v)) for k, v in result.items())}")
            
            return result
            
        except Exception as e:
            logger.error(f"获取多频率Bar数据失败: {e}")
            return {}
    
    def get_latest_bar(self, symbol: str, frequency: str = '1d') -> Optional[Dict[str, Any]]:
        """获取最新的Bar数据
        
        Args:
            symbol: 标的代码
            frequency: 频率
        
        Returns:
            最新的Bar数据，如果没有则返回None
        """
        try:
            logger.info(f"获取最新Bar数据: {symbol}, 频率: {frequency}")
            
            latest_bar = self.gm_client.get_latest_bar(symbol, frequency)
            
            if latest_bar:
                logger.info(f"获取到最新{frequency}频率数据: {symbol}, 时间: {latest_bar['eob']}")
            else:
                logger.warning(f"未获取到最新{frequency}频率数据: {symbol}")
            
            return latest_bar
            
        except Exception as e:
            logger.error(f"获取最新Bar数据失败: {e}")
            return None
    
    def save_bar_data_to_mongodb(self, bar_data: List[Dict[str, Any]], 
                                collection_name: str = 'bar_data') -> bool:
        """保存Bar数据到MongoDB - 按频率分别存储到指定集合
        
        Args:
            bar_data: Bar数据列表
            collection_name: 基础集合名称
        
        Returns:
            是否保存成功
        """
        if not bar_data:
            logger.warning("没有Bar数据需要保存")
            return False
        
        # 支持的频率类型及其对应的集合名称
        frequency_collections = {
            '1m': 'tick_data_1m',    # 1分钟数据存储到tick_data_1m
            '5m': 'bar_data_5m',     # 5分钟数据存储到bar_data_5m
            '15m': 'bar_data_15m',   # 15分钟数据存储到bar_data_15m
            '30m': 'bar_data_30m',   # 30分钟数据存储到bar_data_30m
            '1h': 'bar_data_1h',     # 1小时数据存储到bar_data_1h
            '1d': 'bar_data_1d',     # 1天数据存储到bar_data_1d
            '1w': 'bar_data_1w',     # 1周数据存储到bar_data_1w
            '1M': 'bar_data_1M'      # 1月数据存储到bar_data_1M
        }
        
        try:
            # 按频率分组数据
            frequency_groups = {}
            for bar in bar_data:
                frequency = bar.get('frequency', '1d')
                
                # 验证频率是否支持
                if frequency not in frequency_collections:
                    logger.warning(f"不支持的频率类型: {frequency}，使用默认频率1d")
                    frequency = '1d'
                
                if frequency not in frequency_groups:
                    frequency_groups[frequency] = []
                frequency_groups[frequency].append(bar)
            
            # 按频率分别保存到不同集合
            total_saved = 0
            for frequency, bars in frequency_groups.items():
                if not bars:
                    continue
                
                # 获取对应的集合名称
                target_collection = frequency_collections[frequency]
                
                logger.info(f"开始保存{frequency}频率数据到集合: {target_collection}, 数据量: {len(bars)}条")
                
                # 为每条数据添加频率标识和保存时间
                for bar in bars:
                    # 确保数据包含必要的字段
                    if 'symbol' not in bar or 'bob' not in bar or 'eob' not in bar:
                        logger.warning(f"Bar数据缺少必要字段: {bar}")
                        continue
                    
                    # 添加频率标识和保存时间
                    bar['frequency'] = frequency
                    bar['saved_at'] = datetime.now()
                    
                    # 构建查询条件（标的代码 + 开始时间 + 结束时间 + 频率）
                    query = {
                        'symbol': bar['symbol'],
                        'bob': bar['bob'],
                        'eob': bar['eob'],
                        'frequency': frequency
                    }
                    
                    # 更新或插入数据
                    result = self.db_manager.update_one_upsert(
                        target_collection,
                        query,
                        {'$set': bar}
                    )
                    
                    if result:
                        total_saved += 1
                        logger.debug(f"保存{frequency}频率Bar数据成功: {bar['symbol']}, {bar['bob']} - {bar['eob']}")
                    else:
                        logger.warning(f"保存{frequency}频率Bar数据失败: {bar['symbol']}, {bar['bob']} - {bar['eob']}")
                
                logger.info(f"完成保存{frequency}频率数据到集合: {target_collection}")
            
            logger.info(f"成功保存{total_saved}条Bar数据到MongoDB，涉及{len(frequency_groups)}个频率")
            return total_saved > 0
            
        except Exception as e:
            logger.error(f"保存Bar数据到MongoDB失败: {e}")
            return False
    
    def collect_and_save_bars(self, symbols: List[str], frequencies: List[str] = None,
                             start_time: str = None, end_time: str = None,
                             save_to_db: bool = True, show_summary: bool = True) -> Dict[str, Any]:
        """采集并保存Bar数据
        
        Args:
            symbols: 标的代码列表
            frequencies: 频率列表
            start_time: 开始时间
            end_time: 结束时间
            save_to_db: 是否保存到数据库
            show_summary: 是否显示数据摘要
        
        Returns:
            采集结果统计
        """
        try:
            logger.info(f"开始采集Bar数据: {symbols}")
            
            # 获取多频率Bar数据
            multi_freq_data = self.get_multi_frequency_bars(
                symbols=symbols,
                frequencies=frequencies,
                start_time=start_time,
                end_time=end_time
            )
            
            if not multi_freq_data:
                logger.warning("未获取到任何Bar数据")
                return {}
            
            # 统计信息
            total_bars = sum(len(bars) for bars in multi_freq_data.values())
            result = {
                'total_symbols': len(symbols),
                'frequencies': list(multi_freq_data.keys()),
                'total_bars': total_bars,
                'frequency_distribution': {freq: len(bars) for freq, bars in multi_freq_data.items()},
                'timestamp': datetime.now().isoformat()
            }
            
            # 显示数据摘要
            if show_summary:
                print(f"\n=== Bar数据采集摘要 ===")
                print(f"标的数量: {result['total_symbols']}")
                print(f"频率类型: {', '.join(result['frequencies'])}")
                print(f"总Bar数量: {result['total_bars']}")
                print(f"频率分布:")
                for freq, count in result['frequency_distribution'].items():
                    print(f"  {freq}: {count}条")
                print()
            
            # 保存到数据库
            if save_to_db:
                for frequency, bars in multi_freq_data.items():
                    if bars:
                        self.save_bar_data_to_mongodb(bars, 'bar_data')
            
            logger.info(f"Bar数据采集完成: {result}")
            return result
            
        except Exception as e:
            logger.error(f"采集Bar数据失败: {e}")
            return {}
    
    def get_bar_summary(self, symbols: List[str], frequency: str = '1d') -> Dict[str, Any]:
        """获取Bar数据摘要信息
        
        Args:
            symbols: 标的代码列表
            frequency: 频率
        
        Returns:
            Bar数据摘要
        """
        try:
            bars = self.get_bar_data(symbols, frequency)
            if not bars:
                return {}
            
            summary = {
                'symbols': symbols,
                'frequency': frequency,
                'total_bars': len(bars),
                'timestamp': datetime.now().isoformat(),
                'data': []
            }
            
            for bar in bars:
                summary_item = {
                    'symbol': bar['symbol'],
                    'open': bar['open'],
                    'close': bar['close'],
                    'high': bar['high'],
                    'low': bar['low'],
                    'volume': bar['volume'],
                    'amount': bar['amount'],
                    'change': bar.get('change', 0),
                    'change_pct': bar.get('change_pct', 0),
                    'amplitude': bar.get('amplitude', 0),
                    'bob': bar['bob'],
                    'eob': bar['eob']
                }
                summary['data'].append(summary_item)
            
            return summary
            
        except Exception as e:
            logger.error(f"获取Bar数据摘要失败: {e}")
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
    """主函数 - 演示Bar数据采集"""
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
        collector = BarDataCollector()
        
        print("🚀 Bar数据采集系统")
        print("=" * 50)
        
        # 设置时间范围（最近一个月）
        end_time = datetime.now().strftime('%Y-%m-%d')
        start_time = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        # 采集多种频率的Bar数据
        frequencies = ['1d', '1h', '30m', '15m', '5m']
        
        bar_result = collector.collect_and_save_bars(
            symbols=symbols[:3],  # 只取前3只股票进行演示
            frequencies=frequencies,
            start_time=start_time,
            end_time=end_time,
            save_to_db=True,
            show_summary=True
        )
        
        if bar_result:
            print("✅ Bar数据采集完成")
            
            # 获取最新Bar数据示例
            print("\n3️⃣ 获取最新Bar数据示例...")
            for symbol in symbols[:2]:  # 只演示前2只股票
                latest_daily = collector.get_latest_bar(symbol, '1d')
                if latest_daily:
                    print(f"\n{symbol} 最新日线数据:")
                    print(f"  时间: {latest_daily['eob']}")
                    print(f"  开盘: {latest_daily['open']:.2f}")
                    print(f"  最高: {latest_daily['high']:.2f}")
                    print(f"  最低: {latest_daily['low']:.2f}")
                    print(f"  收盘: {latest_daily['close']:.2f}")
                    print(f"  成交量: {latest_daily['volume']:,}")
                    print(f"  成交额: {latest_daily['amount']:,.2f}")
                    print(f"  涨跌幅: {latest_daily.get('change_pct', 0):.2f}%")
                    print(f"  振幅: {latest_daily.get('amplitude', 0):.2f}%")
        
        print("\n🎉 Bar数据采集完成！")
        
    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if collector:
            collector.close()


if __name__ == "__main__":
    main()
