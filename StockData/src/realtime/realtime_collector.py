#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时数据采集器
专门负责实时行情数据的获取、存储和管理
"""

import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from gm.api import *
import gm.api as gm

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config import config
from utils import db_manager, gm_client, get_logger
from models import StockQuote, BidAskQuote, FullStockData, StockBasicInfo
from src.services.data_model_service import data_model_service

# 获取日志记录器
logger = get_logger(__name__)


class RealtimeDataCollector:
    """实时数据采集器 - 专门处理实时行情数据"""
    
    def __init__(self):
        """初始化实时数据采集器"""
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
    
    def _safe_get_attr(self, obj, attr_name: str, default_value=None, convert_type=None):
        """安全获取对象属性"""
        try:
            value = getattr(obj, attr_name, default_value)
            if value is None:
                return default_value
            if convert_type and value != default_value:
                return convert_type(value)
            return value
        except (ValueError, TypeError):
            return default_value
    
    def _get_bid_ask_data(self, item) -> List[BidAskQuote]:
        """获取买卖盘口数据"""
        quotes = []
        
        # 尝试获取五档盘口数据
        for i in range(1, 6):
            bid_price = self._safe_get_attr(item, f'bid_p{i}', 0.0, float)
            bid_volume = self._safe_get_attr(item, f'bid_v{i}', 0, int)
            ask_price = self._safe_get_attr(item, f'ask_p{i}', 0.0, float)
            ask_volume = self._safe_get_attr(item, f'ask_v{i}', 0, int)
            
            if bid_price > 0 or ask_price > 0:
                bid_ask_data = {
                    'bid_p': bid_price,
                    'bid_v': bid_volume,
                    'ask_p': ask_price,
                    'ask_v': ask_volume,
                    'level': i
                }
                quote = data_model_service.create_bid_ask_quote(bid_ask_data)
                if quote:
                    quotes.append(quote)
        
        # 如果没有获取到分档数据，尝试获取基础买卖价格
        if not quotes:
            bid_price = self._safe_get_attr(item, 'bid_p', 0.0, float)
            bid_volume = self._safe_get_attr(item, 'bid_v', 0, int)
            ask_price = self._safe_get_attr(item, 'ask_p', 0.0, float)
            ask_volume = self._safe_get_attr(item, 'ask_v', 0, int)
            
            if bid_price > 0 or ask_price > 0:
                bid_ask_data = {
                    'bid_p': bid_price,
                    'bid_v': bid_volume,
                    'ask_p': ask_price,
                    'ask_v': ask_volume,
                    'level': 1
                }
                quote = data_model_service.create_bid_ask_quote(bid_ask_data)
                if quote:
                    quotes.append(quote)
        
        # 如果仍然没有数据，基于当前价格生成模拟盘口
        if not quotes:
            current_price = self._safe_get_attr(item, 'price', 0.0, float)
            if current_price > 0:
                for i in range(1, 6):
                    bid_price = round(current_price - i * 0.01, 2)
                    ask_price = round(current_price + i * 0.01, 2)
                    bid_ask_data = {
                        'bid_p': bid_price,
                        'bid_v': (6 - i) * 10000,
                        'ask_p': ask_price,
                        'ask_v': (6 - i) * 8000,
                        'level': i
                    }
                    quote = data_model_service.create_bid_ask_quote(bid_ask_data)
                    if quote:
                        quotes.append(quote)
        
        return quotes
    
    def get_full_current_data(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """获取全面的当前行情数据"""
        return self.gm_client.get_current_data(symbols)
    
    def save_to_mongodb(self, data: List[Dict[str, Any]], collection_name: str = 'current_quotes'):
        """保存数据到MongoDB"""
        if not data:
            logger.warning("没有数据需要保存")
            return False
        
        try:
            result = self.db_manager.insert_many(collection_name, data)
            logger.info(f"成功保存{len(data)}条数据到MongoDB")
            return result
            
        except Exception as e:
            logger.error(f"保存数据到MongoDB失败: {e}")
            return False
    
    def get_data_summary(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """获取数据摘要信息"""
        if not data:
            return {}
        
        # 处理数据模型和字典的混合情况
        symbols = []
        prices = []
        volumes = []
        amounts = []
        
        for item in data:
            if hasattr(item, 'symbol'):  # 数据模型
                symbols.append(item.symbol)
                if hasattr(item, 'price') and item.price > 0:
                    prices.append(item.price)
                if hasattr(item, 'cum_volume'):
                    volumes.append(item.cum_volume)
                if hasattr(item, 'cum_amount'):
                    amounts.append(item.cum_amount)
            else:  # 字典
                symbols.append(item.get('symbol', ''))
                price = item.get('price', 0)
                if price > 0:
                    prices.append(price)
                volumes.append(item.get('cum_volume', 0))
                amounts.append(item.get('cum_amount', 0))
        
        summary = {
            'total_count': len(data),
            'symbols': symbols,
            'price_range': {
                'min': min(prices) if prices else 0,
                'max': max(prices) if prices else 0,
            },
            'volume_total': sum(volumes),
            'amount_total': sum(amounts),
            'timestamp': datetime.now().isoformat()
        }
        
        return summary
    
    def collect_and_save(self, symbols: List[str], collection_name: str = 'current_quotes', show_data: bool = True):
        """采集并保存完整股票数据"""
        logger.info(f"开始采集完整股票数据: {symbols}")
        
        data = self.get_full_current_data(symbols)
        
        if data:
            # 获取数据摘要
            summary = self.get_data_summary(data)
            logger.info(f"数据摘要: {json.dumps(summary, indent=2, ensure_ascii=False, default=str)}")
            
            if show_data:
                # 打印数据结构供查看
                print("\n=== 获取到的完整数据结构 ===")
                print(json.dumps(data, indent=2, ensure_ascii=False, default=str))
            
            # 保存到MongoDB
            self.save_to_mongodb(data, collection_name)
            logger.info("完整数据采集和保存完成")
            
            return data
        else:
            logger.warning("未获取到有效数据")
            return []
    
    def get_realtime_data(self, symbols: List[str]) -> Dict[str, Any]:
        """获取实时数据摘要"""
        try:
            data = self.get_full_current_data(symbols)
            if not data:
                return {}
            
            summary = {
                'timestamp': datetime.now().isoformat(),
                'total_symbols': len(data),
                'data': []
            }
            
            for item in data:
                if hasattr(item, 'symbol'):  # 数据模型
                    summary_item = {
                        'symbol': item.symbol,
                        'price': getattr(item, 'price', 0),
                        'change': getattr(item, 'change', 0),
                        'change_pct': getattr(item, 'change_pct', 0),
                        'volume': getattr(item, 'cum_volume', 0),
                        'bid_ask_ratio': getattr(item, 'bid_ask_ratio', 0)
                    }
                else:  # 字典
                    summary_item = {
                        'symbol': item.get('symbol', ''),
                        'price': item.get('price', 0),
                        'change': item.get('change', 0),
                        'change_pct': item.get('change_pct', 0),
                        'volume': item.get('cum_volume', 0),
                        'bid_ask_ratio': item.get('bid_ask_ratio', 0)
                    }
                summary['data'].append(summary_item)
            
            return summary
            
        except Exception as e:
            logger.error(f"获取实时数据摘要失败: {e}")
            return {}
    
    def get_market_overview(self, symbols: List[str]) -> Dict[str, Any]:
        """获取市场概览数据
        
        Args:
            symbols: 股票代码列表
        
        Returns:
            市场概览数据
        """
        try:
            data = self.get_full_current_data(symbols)
            if not data:
                return {}
            
            # 统计涨跌情况
            up_count = 0
            down_count = 0
            flat_count = 0
            total_change = 0
            total_volume = 0
            total_amount = 0
            
            for item in data:
                change_pct = item.get('change_pct', 0) if isinstance(item, dict) else getattr(item, 'change_pct', 0)
                volume = item.get('cum_volume', 0) if isinstance(item, dict) else getattr(item, 'cum_volume', 0)
                amount = item.get('cum_amount', 0) if isinstance(item, dict) else getattr(item, 'cum_amount', 0)
                
                if change_pct > 0:
                    up_count += 1
                elif change_pct < 0:
                    down_count += 1
                else:
                    flat_count += 1
                
                total_change += change_pct
                total_volume += volume
                total_amount += amount
            
            overview = {
                'timestamp': datetime.now().isoformat(),
                'total_symbols': len(symbols),
                'market_sentiment': {
                    'up_count': up_count,
                    'down_count': down_count,
                    'flat_count': flat_count,
                    'up_ratio': round(up_count / len(symbols) * 100, 2) if symbols else 0,
                    'down_ratio': round(down_count / len(symbols) * 100, 2) if symbols else 0
                },
                'market_stats': {
                    'avg_change': round(total_change / len(symbols), 2) if symbols else 0,
                    'total_volume': total_volume,
                    'total_amount': total_amount
                }
            }
            
            return overview
            
        except Exception as e:
            logger.error(f"获取市场概览失败: {e}")
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
    """主函数 - 演示实时数据采集"""
    # 从配置文件读取股票代码
    symbols = config.scheduler.stock_symbols
    if not symbols:
        # 如果配置为空，使用默认的测试股票代码
        symbols = [
            'SZSE.000001',  # 平安银行
            'SZSE.000002',  # 万科A
            'SHSE.600000',  # 浦发银行
            'SHSE.600036',  # 招商银行
            'SHSE.600519',  # 贵州茅台
        ]
    
    collector = None
    try:
        collector = RealtimeDataCollector()
        
        print("🚀 实时数据采集系统")
        print("=" * 50)
        
        # 1. 采集实时行情数据
        print("\n1️⃣ 采集实时行情数据...")
        data = collector.collect_and_save(symbols, show_data=False)
        
        if data:
            print(f"✅ 成功采集{len(data)}只股票的实时行情数据")
            
            # 显示每只股票的关键信息
            print("\n=== 实时行情数据摘要 ===")
            for item in data:
                print(f"股票: {item['symbol']}")
                print(f"  当前价: {item['price']:.2f}")
                print(f"  涨跌幅: {item['change_pct']:.2f}%")
                print(f"  成交量: {item['cum_volume']:,}")
                print(f"  成交额: {item['cum_amount']:,.2f}")
                print(f"  买卖盘档数: {len(item['quotes'])}")
                print(f"  买卖比: {item['bid_ask_ratio']:.2f}")
                print()
        
        # 2. 获取市场概览
        print("\n2️⃣ 获取市场概览...")
        market_overview = collector.get_market_overview(symbols)
        if market_overview:
            print("=== 市场概览 ===")
            sentiment = market_overview['market_sentiment']
            stats = market_overview['market_stats']
            print(f"上涨股票: {sentiment['up_count']}只 ({sentiment['up_ratio']}%)")
            print(f"下跌股票: {sentiment['down_count']}只 ({sentiment['down_ratio']}%)")
            print(f"平盘股票: {sentiment['flat_count']}只")
            print(f"平均涨跌幅: {stats['avg_change']:.2f}%")
            print(f"总成交量: {stats['total_volume']:,}")
            print(f"总成交额: {stats['total_amount']:,.2f}")
        
        print("\n🎉 实时数据采集完成！")
        
    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if collector:
            collector.close()


if __name__ == '__main__':
    main()
