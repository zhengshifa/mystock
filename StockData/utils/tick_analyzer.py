#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tick数据分析工具模块
提供各种Tick数据的分析功能和工具函数
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)


class TickAnalyzer:
    """Tick数据分析器"""
    
    def __init__(self):
        """初始化分析器"""
        self.logger = logging.getLogger(__name__)
    
    def analyze_price_patterns(self, ticks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析价格模式
        
        Args:
            ticks: Tick数据列表
        
        Returns:
            价格模式分析结果
        """
        if not ticks or len(ticks) < 2:
            return {}
        
        try:
            prices = [tick['price'] for tick in ticks if tick.get('price', 0) > 0]
            if not prices:
                return {}
            
            # 计算价格变化
            price_changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]
            price_changes_pct = [(prices[i] - prices[i-1]) / prices[i-1] * 100 
                               for i in range(1, len(prices)) if prices[i-1] > 0]
            
            # 分析价格变化模式
            positive_changes = [c for c in price_changes if c > 0]
            negative_changes = [c for c in price_changes if c < 0]
            zero_changes = [c for c in price_changes if c == 0]
            
            # 计算统计信息
            analysis = {
                'price_changes': {
                    'total_changes': len(price_changes),
                    'positive_count': len(positive_changes),
                    'negative_count': len(negative_changes),
                    'zero_count': len(zero_changes),
                    'positive_ratio': len(positive_changes) / len(price_changes) if price_changes else 0,
                    'negative_ratio': len(negative_changes) / len(price_changes) if price_changes else 0,
                    'max_up': max(positive_changes) if positive_changes else 0,
                    'max_down': min(negative_changes) if negative_changes else 0,
                    'avg_up': sum(positive_changes) / len(positive_changes) if positive_changes else 0,
                    'avg_down': sum(negative_changes) / len(negative_changes) if negative_changes else 0
                },
                'price_momentum': {
                    'trend': 'up' if prices[-1] > prices[0] else 'down' if prices[-1] < prices[0] else 'flat',
                    'strength': abs(prices[-1] - prices[0]) / prices[0] * 100 if prices[0] > 0 else 0,
                    'total_change': prices[-1] - prices[0],
                    'total_change_pct': (prices[-1] - prices[0]) / prices[0] * 100 if prices[0] > 0 else 0
                },
                'price_volatility': {
                    'std': np.std(price_changes) if len(price_changes) > 1 else 0,
                    'std_pct': np.std(price_changes_pct) if len(price_changes_pct) > 1 else 0,
                    'range': max(prices) - min(prices),
                    'range_pct': (max(prices) - min(prices)) / min(prices) * 100 if min(prices) > 0 else 0
                }
            }
            
            # 分析价格序列的连续性
            consecutive_up = 0
            consecutive_down = 0
            max_consecutive_up = 0
            max_consecutive_down = 0
            
            for change in price_changes:
                if change > 0:
                    consecutive_up += 1
                    consecutive_down = 0
                    max_consecutive_up = max(max_consecutive_up, consecutive_up)
                elif change < 0:
                    consecutive_down += 1
                    consecutive_up = 0
                    max_consecutive_down = max(max_consecutive_down, consecutive_down)
                else:
                    consecutive_up = 0
                    consecutive_down = 0
            
            analysis['price_patterns'] = {
                'max_consecutive_up': max_consecutive_up,
                'max_consecutive_down': max_consecutive_down,
                'avg_consecutive_up': len(positive_changes) / (len(positive_changes) + len(negative_changes)) if (len(positive_changes) + len(negative_changes)) > 0 else 0,
                'avg_consecutive_down': len(negative_changes) / (len(positive_changes) + len(negative_changes)) if (len(positive_changes) + len(negative_changes)) > 0 else 0
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"分析价格模式失败: {e}")
            return {}
    
    def analyze_volume_patterns(self, ticks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析成交量模式
        
        Args:
            ticks: Tick数据列表
        
        Returns:
            成交量模式分析结果
        """
        if not ticks:
            return {}
        
        try:
            volumes = [tick['last_volume'] for tick in ticks if tick.get('last_volume', 0) > 0]
            amounts = [tick['last_amount'] for tick in ticks if tick.get('last_amount', 0) > 0]
            
            if not volumes:
                return {}
            
            # 计算成交量统计
            total_volume = sum(volumes)
            avg_volume = total_volume / len(volumes)
            max_volume = max(volumes)
            min_volume = min(volumes)
            
            # 分析成交量分布
            high_volume_threshold = avg_volume * 2
            low_volume_threshold = avg_volume * 0.5
            
            high_volume_ticks = [v for v in volumes if v > high_volume_threshold]
            low_volume_ticks = [v for v in volumes if v < low_volume_threshold]
            normal_volume_ticks = [v for v in volumes if low_volume_threshold <= v <= high_volume_threshold]
            
            # 计算成交量变化
            volume_changes = []
            if len(volumes) > 1:
                volume_changes = [volumes[i] - volumes[i-1] for i in range(1, len(volumes))]
            
            analysis = {
                'volume_stats': {
                    'total': total_volume,
                    'count': len(volumes),
                    'avg': avg_volume,
                    'max': max_volume,
                    'min': min_volume,
                    'std': np.std(volumes) if len(volumes) > 1 else 0
                },
                'volume_distribution': {
                    'high_volume_count': len(high_volume_ticks),
                    'low_volume_count': len(low_volume_ticks),
                    'normal_volume_count': len(normal_volume_ticks),
                    'high_volume_ratio': len(high_volume_ticks) / len(volumes),
                    'low_volume_ratio': len(low_volume_ticks) / len(volumes),
                    'normal_volume_ratio': len(normal_volume_ticks) / len(volumes)
                },
                'volume_patterns': {
                    'volume_concentration': max_volume / avg_volume if avg_volume > 0 else 0,
                    'volume_variability': np.std(volumes) / avg_volume if avg_volume > 0 else 0
                }
            }
            
            # 分析成交量变化
            if volume_changes:
                positive_volume_changes = [c for c in volume_changes if c > 0]
                negative_volume_changes = [c for c in volume_changes if c < 0]
                
                analysis['volume_changes'] = {
                    'positive_count': len(positive_volume_changes),
                    'negative_count': len(negative_volume_changes),
                    'max_increase': max(positive_volume_changes) if positive_volume_changes else 0,
                    'max_decrease': min(negative_volume_changes) if negative_volume_changes else 0,
                    'avg_increase': sum(positive_volume_changes) / len(positive_volume_changes) if positive_volume_changes else 0,
                    'avg_decrease': sum(negative_volume_changes) / len(negative_volume_changes) if negative_volume_changes else 0
                }
            
            # 分析成交额
            if amounts:
                total_amount = sum(amounts)
                avg_amount = total_amount / len(amounts)
                
                analysis['amount_stats'] = {
                    'total': total_amount,
                    'avg': avg_amount,
                    'max': max(amounts),
                    'min': min(amounts)
                }
                
                # 计算VWAP
                if total_volume > 0:
                    analysis['vwap'] = total_amount / total_volume
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"分析成交量模式失败: {e}")
            return {}
    
    def analyze_market_microstructure(self, ticks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析市场微观结构
        
        Args:
            ticks: Tick数据列表
        
        Returns:
            市场微观结构分析结果
        """
        if not ticks:
            return {}
        
        try:
            bid_ask_spreads = []
            bid_ask_ratios = []
            bid_volumes = []
            ask_volumes = []
            bid_prices = []
            ask_prices = []
            
            for tick in ticks:
                quotes = tick.get('quotes', [])
                if quotes and len(quotes) > 0:
                    first_quote = quotes[0]
                    
                    # 收集买卖价量数据
                    if first_quote.get('bid_p', 0) > 0:
                        bid_prices.append(first_quote['bid_p'])
                        bid_volumes.append(first_quote.get('bid_v', 0))
                    
                    if first_quote.get('ask_p', 0) > 0:
                        ask_prices.append(first_quote['ask_p'])
                        ask_volumes.append(first_quote.get('ask_v', 0))
                    
                    # 计算买卖价差
                    if (first_quote.get('ask_p', 0) > 0 and 
                        first_quote.get('bid_p', 0) > 0):
                        spread = first_quote['ask_p'] - first_quote['bid_p']
                        bid_ask_spreads.append(spread)
                        
                        # 计算买卖比例
                        total_bid = sum(q.get('bid_v', 0) for q in quotes if q.get('bid_v', 0) > 0)
                        total_ask = sum(q.get('ask_v', 0) for q in quotes if q.get('ask_v', 0) > 0)
                        if total_ask > 0:
                            bid_ask_ratios.append(total_bid / total_ask)
            
            analysis = {}
            
            # 分析买卖价差
            if bid_ask_spreads:
                analysis['bid_ask_spread'] = {
                    'avg': sum(bid_ask_spreads) / len(bid_ask_spreads),
                    'min': min(bid_ask_spreads),
                    'max': max(bid_ask_spreads),
                    'std': np.std(bid_ask_spreads) if len(bid_ask_spreads) > 1 else 0,
                    'count': len(bid_ask_spreads)
                }
            
            # 分析买卖比例
            if bid_ask_ratios:
                analysis['bid_ask_ratio'] = {
                    'avg': sum(bid_ask_ratios) / len(bid_ask_ratios),
                    'min': min(bid_ask_ratios),
                    'max': max(bid_ask_ratios),
                    'std': np.std(bid_ask_ratios) if len(bid_ask_ratios) > 1 else 0,
                    'count': len(bid_ask_ratios)
                }
            
            # 分析买卖价格分布
            if bid_prices:
                analysis['bid_price_stats'] = {
                    'avg': sum(bid_prices) / len(bid_prices),
                    'min': min(bid_prices),
                    'max': max(bid_prices),
                    'std': np.std(bid_prices) if len(bid_prices) > 1 else 0
                }
            
            if ask_prices:
                analysis['ask_price_stats'] = {
                    'avg': sum(ask_prices) / len(ask_prices),
                    'min': min(ask_prices),
                    'max': max(ask_prices),
                    'std': np.std(ask_prices) if len(ask_prices) > 1 else 0
                }
            
            # 分析买卖量分布
            if bid_volumes:
                analysis['bid_volume_stats'] = {
                    'avg': sum(bid_volumes) / len(bid_volumes),
                    'min': min(bid_volumes),
                    'max': max(bid_volumes),
                    'total': sum(bid_volumes)
                }
            
            if ask_volumes:
                analysis['ask_volume_stats'] = {
                    'avg': sum(ask_volumes) / len(ask_volumes),
                    'min': min(ask_volumes),
                    'max': max(ask_volumes),
                    'total': sum(ask_volumes)
                }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"分析市场微观结构失败: {e}")
            return {}
    
    def analyze_time_patterns(self, ticks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析时间模式
        
        Args:
            ticks: Tick数据列表
        
        Returns:
            时间模式分析结果
        """
        if not ticks:
            return {}
        
        try:
            # 提取时间信息
            timestamps = []
            for tick in ticks:
                created_at = tick.get('created_at')
                if isinstance(created_at, datetime):
                    timestamps.append(created_at)
                elif isinstance(created_at, str):
                    try:
                        timestamps.append(datetime.fromisoformat(created_at.replace('Z', '+00:00')))
                    except:
                        continue
            
            if not timestamps:
                return {}
            
            # 按小时分组
            hourly_stats = defaultdict(lambda: {'count': 0, 'volumes': [], 'amounts': []})
            
            for i, tick in enumerate(ticks):
                if i < len(timestamps):
                    hour = timestamps[i].hour
                    hourly_stats[hour]['count'] += 1
                    if tick.get('last_volume', 0) > 0:
                        hourly_stats[hour]['volumes'].append(tick['last_volume'])
                    if tick.get('last_amount', 0) > 0:
                        hourly_stats[hour]['amounts'].append(tick['last_amount'])
            
            # 计算每小时统计
            hourly_analysis = {}
            for hour, stats in hourly_stats.items():
                hourly_analysis[hour] = {
                    'tick_count': stats['count'],
                    'avg_volume': sum(stats['volumes']) / len(stats['volumes']) if stats['volumes'] else 0,
                    'total_volume': sum(stats['volumes']),
                    'avg_amount': sum(stats['amounts']) / len(stats['amounts']) if stats['amounts'] else 0,
                    'total_amount': sum(stats['amounts'])
                }
            
            # 计算时间间隔
            time_intervals = []
            if len(timestamps) > 1:
                for i in range(1, len(timestamps)):
                    interval = (timestamps[i] - timestamps[i-1]).total_seconds()
                    time_intervals.append(interval)
            
            analysis = {
                'hourly_distribution': hourly_analysis,
                'time_intervals': {
                    'avg_interval': sum(time_intervals) / len(time_intervals) if time_intervals else 0,
                    'min_interval': min(time_intervals) if time_intervals else 0,
                    'max_interval': max(time_intervals) if time_intervals else 0,
                    'std_interval': np.std(time_intervals) if len(time_intervals) > 1 else 0
                } if time_intervals else {},
                'trading_hours': {
                    'start_time': min(timestamps) if timestamps else None,
                    'end_time': max(timestamps) if timestamps else None,
                    'duration_hours': (max(timestamps) - min(timestamps)).total_seconds() / 3600 if len(timestamps) > 1 else 0
                }
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"分析时间模式失败: {e}")
            return {}
    
    def detect_anomalies(self, ticks: List[Dict[str, Any]], 
                         price_threshold: float = 3.0,
                         volume_threshold: float = 5.0) -> Dict[str, Any]:
        """检测异常数据
        
        Args:
            ticks: Tick数据列表
            price_threshold: 价格异常阈值（标准差倍数）
            volume_threshold: 成交量异常阈值（标准差倍数）
        
        Returns:
            异常检测结果
        """
        if not ticks or len(ticks) < 2:
            return {}
        
        try:
            prices = [tick['price'] for tick in ticks if tick.get('price', 0) > 0]
            volumes = [tick['last_volume'] for tick in ticks if tick.get('last_volume', 0) > 0]
            
            anomalies = {
                'price_anomalies': [],
                'volume_anomalies': [],
                'summary': {}
            }
            
            # 检测价格异常
            if len(prices) > 1:
                price_mean = np.mean(prices)
                price_std = np.std(prices)
                
                for i, price in enumerate(prices):
                    if abs(price - price_mean) > price_threshold * price_std:
                        anomalies['price_anomalies'].append({
                            'index': i,
                            'price': price,
                            'deviation': abs(price - price_mean),
                            'deviation_std': abs(price - price_mean) / price_std if price_std > 0 else 0
                        })
            
            # 检测成交量异常
            if len(volumes) > 1:
                volume_mean = np.mean(volumes)
                volume_std = np.std(volumes)
                
                for i, volume in enumerate(volumes):
                    if abs(volume - volume_mean) > volume_threshold * volume_std:
                        anomalies['volume_anomalies'].append({
                            'index': i,
                            'volume': volume,
                            'deviation': abs(volume - volume_mean),
                            'deviation_std': abs(volume - volume_mean) / volume_std if volume_std > 0 else 0
                        })
            
            # 生成摘要
            anomalies['summary'] = {
                'total_anomalies': len(anomalies['price_anomalies']) + len(anomalies['volume_anomalies']),
                'price_anomalies_count': len(anomalies['price_anomalies']),
                'volume_anomalies_count': len(anomalies['volume_anomalies']),
                'anomaly_rate': (len(anomalies['price_anomalies']) + len(anomalies['volume_anomalies'])) / len(ticks)
            }
            
            return anomalies
            
        except Exception as e:
            self.logger.error(f"检测异常数据失败: {e}")
            return {}
    
    def generate_comprehensive_report(self, ticks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成综合分析报告
        
        Args:
            ticks: Tick数据列表
        
        Returns:
            综合分析报告
        """
        if not ticks:
            return {}
        
        try:
            report = {
                'summary': {
                    'total_ticks': len(ticks),
                    'analysis_time': datetime.now().isoformat(),
                    'data_quality': self._assess_data_quality(ticks)
                },
                'price_analysis': self.analyze_price_patterns(ticks),
                'volume_analysis': self.analyze_volume_patterns(ticks),
                'microstructure_analysis': self.analyze_market_microstructure(ticks),
                'time_analysis': self.analyze_time_patterns(ticks),
                'anomaly_detection': self.detect_anomalies(ticks),
                'recommendations': self._generate_recommendations(ticks)
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"生成综合分析报告失败: {e}")
            return {}
    
    def _assess_data_quality(self, ticks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """评估数据质量
        
        Args:
            ticks: Tick数据列表
        
        Returns:
            数据质量评估结果
        """
        if not ticks:
            return {}
        
        try:
            total_fields = 0
            missing_fields = 0
            required_fields = ['price', 'last_volume', 'last_amount', 'quotes']
            
            for tick in ticks:
                for field in required_fields:
                    total_fields += 1
                    if field not in tick or tick[field] is None:
                        missing_fields += 1
            
            completeness = (total_fields - missing_fields) / total_fields if total_fields > 0 else 0
            
            return {
                'completeness': completeness,
                'missing_fields': missing_fields,
                'total_fields': total_fields,
                'quality_score': completeness * 100
            }
            
        except Exception as e:
            self.logger.error(f"评估数据质量失败: {e}")
            return {}
    
    def _generate_recommendations(self, ticks: List[Dict[str, Any]]) -> List[str]:
        """生成数据分析和交易建议
        
        Args:
            ticks: Tick数据列表
        
        Returns:
            建议列表
        """
        recommendations = []
        
        try:
            if not ticks:
                recommendations.append("数据为空，无法生成建议")
                return recommendations
            
            # 基于数据量的建议
            if len(ticks) < 100:
                recommendations.append("Tick数据量较少，建议收集更多数据以提高分析准确性")
            
            # 基于价格变化的建议
            price_analysis = self.analyze_price_patterns(ticks)
            if price_analysis and 'price_momentum' in price_analysis:
                momentum = price_analysis['price_momentum']
                if momentum.get('trend') == 'up' and momentum.get('strength', 0) > 2:
                    recommendations.append("价格呈现明显上涨趋势，可考虑顺势交易策略")
                elif momentum.get('trend') == 'down' and momentum.get('strength', 0) > 2:
                    recommendations.append("价格呈现明显下跌趋势，注意风险控制")
            
            # 基于成交量的建议
            volume_analysis = self.analyze_volume_patterns(ticks)
            if volume_analysis and 'volume_distribution' in volume_analysis:
                dist = volume_analysis['volume_distribution']
                if dist.get('high_volume_ratio', 0) > 0.3:
                    recommendations.append("高成交量Tick占比较高，市场活跃度较高")
                elif dist.get('low_volume_ratio', 0) > 0.5:
                    recommendations.append("低成交量Tick占比较高，市场活跃度较低")
            
            # 基于市场微观结构的建议
            microstructure = self.analyze_market_microstructure(ticks)
            if microstructure and 'bid_ask_spread' in microstructure:
                spread = microstructure['bid_ask_spread']
                if spread.get('avg', 0) > 0.01:
                    recommendations.append("买卖价差较大，市场流动性可能不足")
                elif spread.get('avg', 0) < 0.001:
                    recommendations.append("买卖价差较小，市场流动性较好")
            
            if not recommendations:
                recommendations.append("数据表现正常，建议继续监控市场变化")
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"生成建议失败: {e}")
            return ["生成建议时发生错误"]


# 便捷函数
def analyze_ticks(ticks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """便捷的Tick数据分析函数
    
    Args:
        ticks: Tick数据列表
    
    Returns:
        分析结果
    """
    analyzer = TickAnalyzer()
    return analyzer.generate_comprehensive_report(ticks)


def detect_price_anomalies(ticks: List[Dict[str, Any]], threshold: float = 3.0) -> List[Dict[str, Any]]:
    """检测价格异常
    
    Args:
        ticks: Tick数据列表
        threshold: 异常阈值
    
    Returns:
        异常列表
    """
    analyzer = TickAnalyzer()
    anomalies = analyzer.detect_anomalies(ticks, price_threshold=threshold)
    return anomalies.get('price_anomalies', [])


def calculate_vwap(ticks: List[Dict[str, Any]]) -> float:
    """计算成交量加权平均价格
    
    Args:
        ticks: Tick数据列表
    
    Returns:
        VWAP值
    """
    try:
        total_volume = 0
        total_amount = 0
        
        for tick in ticks:
            volume = tick.get('last_volume', 0)
            amount = tick.get('last_amount', 0)
            
            if volume > 0 and amount > 0:
                total_volume += volume
                total_amount += amount
        
        return total_amount / total_volume if total_volume > 0 else 0
        
    except Exception as e:
        logger.error(f"计算VWAP失败: {e}")
        return 0
