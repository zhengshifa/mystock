#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
市场数据分析器
专门负责市场数据的分析、统计和技术指标计算
"""

import sys
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils import get_logger

# 获取日志记录器
logger = get_logger(__name__)


class MarketDataAnalyzer:
    """市场数据分析器 - 专门负责数据分析功能"""
    
    def __init__(self):
        """初始化市场数据分析器"""
        self.logger = logger
    
    def analyze_tick_data(self, ticks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析Tick数据，计算各种技术指标和统计信息
        
        Args:
            ticks: Tick数据列表
        
        Returns:
            分析结果字典
        """
        try:
            if not ticks:
                return {}
            
            # 提取价格和成交量数据
            prices = [tick['price'] for tick in ticks if tick['price'] > 0]
            volumes = [tick['last_volume'] for tick in ticks if tick['last_volume'] > 0]
            amounts = [tick['last_amount'] for tick in ticks if tick['last_amount'] > 0]
            
            if not prices:
                return {}
            
            analysis = {
                'price_analysis': {},
                'volume_analysis': {},
                'volatility_analysis': {},
                'liquidity_analysis': {},
                'market_microstructure': {}
            }
            
            # 价格分析
            if len(prices) >= 2:
                price_changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]
                analysis['price_analysis'] = {
                    'price_changes': {
                        'positive_count': len([c for c in price_changes if c > 0]),
                        'negative_count': len([c for c in price_changes if c < 0]),
                        'zero_count': len([c for c in price_changes if c == 0]),
                        'max_up': max(price_changes) if price_changes else 0,
                        'max_down': min(price_changes) if price_changes else 0
                    },
                    'price_momentum': {
                        'trend': 'up' if prices[-1] > prices[0] else 'down' if prices[-1] < prices[0] else 'flat',
                        'strength': abs(prices[-1] - prices[0]) / prices[0] * 100 if prices[0] > 0 else 0
                    }
                }
            
            # 成交量分析
            if volumes:
                analysis['volume_analysis'] = {
                    'volume_distribution': {
                        'high_volume_ticks': len([v for v in volumes if v > sum(volumes) / len(volumes) * 2]),
                        'low_volume_ticks': len([v for v in volumes if v > sum(volumes) / len(volumes) * 0.5]),
                        'volume_concentration': max(volumes) / (sum(volumes) / len(volumes)) if volumes else 0
                    }
                }
            
            # 波动性分析
            if len(prices) >= 2:
                returns = [(prices[i] - prices[i-1]) / prices[i-1] * 100 for i in range(1, len(prices)) if prices[i-1] > 0]
                if returns:
                    analysis['volatility_analysis'] = {
                        'return_volatility': {
                            'std': sum((r - sum(returns) / len(returns)) ** 2 for r in returns) / len(returns) if len(returns) > 1 else 0,
                            'max_return': max(returns),
                            'min_return': min(returns),
                            'avg_return': sum(returns) / len(returns)
                        }
                    }
            
            # 流动性分析
            if amounts and volumes:
                analysis['volume_weighted_avg_price'] = sum(a * v for a, v in zip(amounts, volumes)) / sum(volumes) if sum(volumes) > 0 else 0
                analysis['liquidity_analysis'] = {
                    'avg_trade_size': sum(amounts) / len(amounts),
                    'volume_weighted_avg_price': analysis['volume_weighted_avg_price']
                }
            
            # 市场微观结构分析
            bid_ask_spreads = []
            bid_ask_ratios = []
            
            for tick in ticks:
                quotes = tick.get('quotes', [])
                if quotes and len(quotes) > 0:
                    first_quote = quotes[0]
                    if first_quote.get('ask_p', 0) > 0 and first_quote.get('bid_p', 0) > 0:
                        spread = first_quote['ask_p'] - first_quote['bid_p']
                        bid_ask_spreads.append(spread)
                        
                        total_bid = sum(q.get('bid_v', 0) for q in quotes if q.get('bid_v', 0) > 0)
                        total_ask = sum(q.get('ask_v', 0) for q in quotes if q.get('ask_v', 0) > 0)
                        if total_ask > 0:
                            bid_ask_ratios.append(total_bid / total_ask)
            
            if bid_ask_spreads:
                analysis['market_microstructure'] = {
                    'bid_ask_spread': {
                        'avg': sum(bid_ask_spreads) / len(bid_ask_spreads),
                        'min': min(bid_ask_spreads),
                        'max': max(bid_ask_spreads)
                    }
                }
            
            if bid_ask_ratios:
                if 'market_microstructure' not in analysis:
                    analysis['market_microstructure'] = {}
                analysis['market_microstructure']['bid_ask_ratio'] = {
                    'avg': sum(bid_ask_ratios) / len(bid_ask_ratios),
                    'min': min(bid_ask_ratios),
                    'max': max(bid_ask_ratios)
                }
            
            return analysis
            
        except Exception as e:
            logger.error(f"分析Tick数据失败: {e}")
            return {}
    
    def analyze_bar_data(self, bars: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析Bar数据，计算技术指标
        
        Args:
            bars: Bar数据列表
        
        Returns:
            分析结果字典
        """
        try:
            if not bars:
                return {}
            
            # 提取OHLCV数据
            opens = [bar['open'] for bar in bars if bar.get('open', 0) > 0]
            highs = [bar['high'] for bar in bars if bar.get('high', 0) > 0]
            lows = [bar['low'] for bar in bars if bar.get('low', 0) > 0]
            closes = [bar['close'] for bar in bars if bar.get('close', 0) > 0]
            volumes = [bar['volume'] for bar in bars if bar.get('volume', 0) > 0]
            
            if not closes:
                return {}
            
            analysis = {
                'price_analysis': {},
                'volume_analysis': {},
                'technical_indicators': {}
            }
            
            # 价格分析
            if len(closes) >= 2:
                price_changes = [(closes[i] - closes[i-1]) / closes[i-1] * 100 for i in range(1, len(closes))]
                analysis['price_analysis'] = {
                    'price_changes': {
                        'positive_count': len([c for c in price_changes if c > 0]),
                        'negative_count': len([c for c in price_changes if c < 0]),
                        'max_up': max(price_changes) if price_changes else 0,
                        'max_down': min(price_changes) if price_changes else 0,
                        'avg_change': sum(price_changes) / len(price_changes) if price_changes else 0
                    },
                    'price_range': {
                        'min': min(closes),
                        'max': max(closes),
                        'avg': sum(closes) / len(closes)
                    }
                }
            
            # 成交量分析
            if volumes:
                analysis['volume_analysis'] = {
                    'volume_stats': {
                        'total': sum(volumes),
                        'avg': sum(volumes) / len(volumes),
                        'max': max(volumes),
                        'min': min(volumes)
                    }
                }
            
            # 技术指标
            if len(closes) >= 14:  # 至少需要14个数据点计算RSI
                analysis['technical_indicators'] = {
                    'rsi': self._calculate_rsi(closes),
                    'sma_5': self._calculate_sma(closes, 5),
                    'sma_10': self._calculate_sma(closes, 10),
                    'sma_20': self._calculate_sma(closes, 20)
                }
            
            return analysis
            
        except Exception as e:
            logger.error(f"分析Bar数据失败: {e}")
            return {}
    
    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """计算RSI指标
        
        Args:
            prices: 价格列表
            period: 计算周期
        
        Returns:
            RSI值
        """
        try:
            if len(prices) < period + 1:
                return 0.0
            
            # 计算价格变化
            changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]
            
            # 分离上涨和下跌
            gains = [change if change > 0 else 0 for change in changes]
            losses = [-change if change < 0 else 0 for change in changes]
            
            # 计算平均上涨和下跌
            avg_gain = sum(gains[-period:]) / period
            avg_loss = sum(losses[-period:]) / period
            
            if avg_loss == 0:
                return 100.0
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            return round(rsi, 2)
            
        except Exception as e:
            logger.error(f"计算RSI失败: {e}")
            return 0.0
    
    def _calculate_sma(self, prices: List[float], period: int) -> float:
        """计算简单移动平均线
        
        Args:
            prices: 价格列表
            period: 计算周期
        
        Returns:
            SMA值
        """
        try:
            if len(prices) < period:
                return 0.0
            
            recent_prices = prices[-period:]
            sma = sum(recent_prices) / period
            
            return round(sma, 2)
            
        except Exception as e:
            logger.error(f"计算SMA失败: {e}")
            return 0.0
    
    def generate_market_report(self, tick_data: List[Dict[str, Any]] = None, 
                              bar_data: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """生成市场数据报告
        
        Args:
            tick_data: Tick数据列表
            bar_data: Bar数据列表
        
        Returns:
            市场数据报告
        """
        try:
            report = {
                'timestamp': datetime.now().isoformat(),
                'tick_analysis': {},
                'bar_analysis': {},
                'summary': {}
            }
            
            # 分析Tick数据
            if tick_data:
                report['tick_analysis'] = self.analyze_tick_data(tick_data)
            
            # 分析Bar数据
            if bar_data:
                report['bar_analysis'] = self.analyze_bar_data(bar_data)
            
            # 生成摘要
            report['summary'] = self._generate_summary(report)
            
            return report
            
        except Exception as e:
            logger.error(f"生成市场数据报告失败: {e}")
            return {}
    
    def _generate_summary(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """生成报告摘要
        
        Args:
            report: 完整报告
        
        Returns:
            报告摘要
        """
        try:
            summary = {
                'data_quality': 'good',
                'key_insights': [],
                'recommendations': []
            }
            
            # 评估数据质量
            if report.get('tick_analysis'):
                tick_analysis = report['tick_analysis']
                if tick_analysis.get('price_analysis', {}).get('price_changes', {}).get('positive_count', 0) > 0:
                    summary['key_insights'].append("价格呈现上涨趋势")
                if tick_analysis.get('volatility_analysis'):
                    summary['key_insights'].append("存在明显的价格波动")
            
            if report.get('bar_analysis'):
                bar_analysis = report['bar_analysis']
                if bar_analysis.get('technical_indicators', {}).get('rsi', 0) > 70:
                    summary['recommendations'].append("RSI指标显示可能超买，注意风险")
                elif bar_analysis.get('technical_indicators', {}).get('rsi', 0) < 30:
                    summary['recommendations'].append("RSI指标显示可能超卖，关注机会")
            
            return summary
            
        except Exception as e:
            logger.error(f"生成报告摘要失败: {e}")
            return {}


def main():
    """主函数 - 演示市场数据分析"""
    analyzer = MarketDataAnalyzer()
    
    print("🚀 市场数据分析器")
    print("=" * 50)
    
    # 模拟数据
    sample_ticks = [
        {'price': 10.0, 'last_volume': 1000, 'last_amount': 10000, 'quotes': [{'bid_p': 9.99, 'ask_p': 10.01, 'bid_v': 500, 'ask_v': 500}]},
        {'price': 10.02, 'last_volume': 1200, 'last_amount': 12024, 'quotes': [{'bid_p': 10.01, 'ask_p': 10.03, 'bid_v': 600, 'ask_v': 400}]},
        {'price': 10.01, 'last_volume': 800, 'last_amount': 8008, 'quotes': [{'bid_p': 10.00, 'ask_p': 10.02, 'bid_v': 400, 'ask_v': 600}]}
    ]
    
    sample_bars = [
        {'open': 10.0, 'high': 10.05, 'low': 9.98, 'close': 10.02, 'volume': 3000},
        {'open': 10.02, 'high': 10.08, 'low': 10.00, 'close': 10.06, 'volume': 3500},
        {'open': 10.06, 'high': 10.10, 'low': 10.03, 'close': 10.08, 'volume': 4000}
    ]
    
    # 分析数据
    print("\n1️⃣ 分析Tick数据...")
    tick_analysis = analyzer.analyze_tick_data(sample_ticks)
    print(f"Tick数据分析结果: {tick_analysis}")
    
    print("\n2️⃣ 分析Bar数据...")
    bar_analysis = analyzer.analyze_bar_data(sample_bars)
    print(f"Bar数据分析结果: {bar_analysis}")
    
    print("\n3️⃣ 生成市场报告...")
    market_report = analyzer.generate_market_report(sample_ticks, sample_bars)
    print(f"市场数据报告: {market_report}")
    
    print("\n🎉 市场数据分析完成！")


if __name__ == "__main__":
    main()
