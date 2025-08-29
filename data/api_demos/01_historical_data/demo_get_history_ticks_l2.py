#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GM API - get_history_ticks_l2 接口测试

本脚本测试 gm.get_history_ticks_l2() API，用于获取历史L2逐笔成交数据。
该接口提供更详细的历史逐笔成交信息，包括买卖方向、成交类型等。

主要功能:
1. 获取历史L2逐笔成交数据
2. 分析成交数据特征
3. 统计成交量价分布
4. 数据可视化和保存

作者: Assistant
创建时间: 2024-01-XX
"""

import gm.api as gm
import pandas as pd
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path


def init_gm_api() -> bool:
    """
    初始化GM API
    
    Returns:
        bool: 初始化是否成功
    """
    try:
        # 设置token（实际使用时需要替换为真实token）
        gm.set_token('your_token_here')
        print("GM API初始化成功")
        return True
    except Exception as e:
        print(f"GM API初始化失败: {e}")
        return False


def l2tick_to_dict(l2tick) -> Dict[str, Any]:
    """
    将L2逐笔成交对象转换为字典
    
    Args:
        l2tick: L2逐笔成交对象
    
    Returns:
        Dict[str, Any]: L2逐笔成交字典
    """
    if l2tick is None:
        return {}
    
    result = {}
    
    # 获取所有属性
    for attr in dir(l2tick):
        if not attr.startswith('_'):
            try:
                value = getattr(l2tick, attr)
                if not callable(value):
                    # 处理datetime对象
                    if isinstance(value, datetime):
                        result[attr] = value.isoformat()
                    else:
                        result[attr] = value
            except Exception as e:
                result[attr] = f"Error: {str(e)}"
    
    return result


def analyze_l2ticks(ticks_data: List[Dict]) -> Dict[str, Any]:
    """
    分析L2逐笔成交数据
    
    Args:
        ticks_data: L2逐笔成交数据列表
    
    Returns:
        Dict[str, Any]: 分析结果
    """
    if not ticks_data:
        return {"error": "没有数据可分析"}
    
    df = pd.DataFrame(ticks_data)
    
    analysis = {
        "basic_stats": {
            "total_ticks": len(df),
            "unique_symbols": df['symbol'].nunique() if 'symbol' in df.columns else 0,
            "time_range": {
                "start": df['created_at'].min() if 'created_at' in df.columns else None,
                "end": df['created_at'].max() if 'created_at' in df.columns else None
            }
        },
        "price_stats": {},
        "volume_stats": {},
        "side_distribution": {},
        "exec_type_distribution": {},
        "symbol_stats": {}
    }
    
    # 价格统计
    if 'price' in df.columns:
        analysis["price_stats"] = {
            "min": float(df['price'].min()),
            "max": float(df['price'].max()),
            "mean": float(df['price'].mean()),
            "median": float(df['price'].median()),
            "std": float(df['price'].std())
        }
    
    # 成交量统计
    if 'volume' in df.columns:
        analysis["volume_stats"] = {
            "total": int(df['volume'].sum()),
            "min": int(df['volume'].min()),
            "max": int(df['volume'].max()),
            "mean": float(df['volume'].mean()),
            "median": float(df['volume'].median())
        }
    
    # 买卖方向分布
    if 'side' in df.columns:
        analysis["side_distribution"] = df['side'].value_counts().to_dict()
    
    # 成交类型分布
    if 'exec_type' in df.columns:
        analysis["exec_type_distribution"] = df['exec_type'].value_counts().to_dict()
    
    # 按标的统计
    if 'symbol' in df.columns:
        symbol_stats = df.groupby('symbol').agg({
            'volume': ['count', 'sum', 'mean'],
            'price': ['min', 'max', 'mean']
        }).round(4)
        
        analysis["symbol_stats"] = symbol_stats.head(10).to_dict()
    
    return analysis


def save_results(data: Dict[str, Any], filename_prefix: str) -> None:
    """
    保存结果到文件
    
    Args:
        data: 要保存的数据
        filename_prefix: 文件名前缀
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 创建结果目录
    results_dir = Path("results/history_ticks_l2")
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存JSON格式
    json_file = results_dir / f"{filename_prefix}_{timestamp}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    
    # 如果有DataFrame数据，也保存为CSV
    if 'data' in data and data['data']:
        try:
            df = pd.DataFrame(data['data'])
            csv_file = results_dir / f"{filename_prefix}_{timestamp}.csv"
            df.to_csv(csv_file, index=False, encoding='utf-8-sig')
            print(f"CSV结果已保存到: {csv_file}")
        except Exception as e:
            print(f"保存CSV失败: {e}")
    
    print(f"JSON结果已保存到: {json_file}")


def test_get_history_ticks_l2_single_symbol():
    """
    测试单个标的的历史L2逐笔成交数据查询
    """
    print("\n=== 测试单个标的历史L2逐笔成交数据查询 ===")
    
    try:
        # 查询单个股票的L2逐笔成交数据
        symbol = "SHSE.000001"  # 上证指数
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=1)  # 查询最近1小时
        
        print(f"查询标的: {symbol}")
        print(f"时间范围: {start_time.strftime('%Y-%m-%d %H:%M:%S')} 到 {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 调用API
        ticks = gm.get_history_ticks_l2(
            symbol=symbol,
            start_time=start_time.strftime('%Y-%m-%d %H:%M:%S'),
            end_time=end_time.strftime('%Y-%m-%d %H:%M:%S')
        )
        
        if ticks:
            print(f"获取到 {len(ticks)} 条L2逐笔成交数据")
            
            # 转换为字典格式
            ticks_data = [l2tick_to_dict(tick) for tick in ticks]
            
            # 分析数据
            analysis = analyze_l2ticks(ticks_data)
            
            # 保存结果
            result = {
                "query_params": {
                    "symbol": symbol,
                    "start_time": start_time.strftime('%Y-%m-%d %H:%M:%S'),
                    "end_time": end_time.strftime('%Y-%m-%d %H:%M:%S')
                },
                "data": ticks_data,
                "analysis": analysis
            }
            
            save_results(result, "single_symbol")
            
            # 显示部分结果
            print("\n前5条记录:")
            for i, tick_data in enumerate(ticks_data[:5]):
                print(f"{i+1}. 价格: {tick_data.get('price', 'N/A')}, "
                      f"成交量: {tick_data.get('volume', 'N/A')}, "
                      f"方向: {tick_data.get('side', 'N/A')}")
            
            print(f"\n统计信息:")
            if 'price_stats' in analysis:
                print(f"- 价格范围: {analysis['price_stats']['min']:.4f} - {analysis['price_stats']['max']:.4f}")
            if 'volume_stats' in analysis:
                print(f"- 总成交量: {analysis['volume_stats']['total']:,}")
            
        else:
            print("未获取到L2逐笔成交数据")
            
    except Exception as e:
        print(f"测试失败: {e}")


def test_get_history_ticks_l2_multiple_symbols():
    """
    测试多个标的的历史L2逐笔成交数据查询
    """
    print("\n=== 测试多个标的历史L2逐笔成交数据查询 ===")
    
    try:
        # 查询多个股票的L2逐笔成交数据
        symbols = ["SHSE.600000", "SHSE.600036", "SZSE.000001"]
        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=30)  # 查询最近30分钟
        
        all_results = {}
        
        for symbol in symbols:
            print(f"\n查询标的: {symbol}")
            
            try:
                ticks = gm.get_history_ticks_l2(
                    symbol=symbol,
                    start_time=start_time.strftime('%Y-%m-%d %H:%M:%S'),
                    end_time=end_time.strftime('%Y-%m-%d %H:%M:%S')
                )
                
                if ticks:
                    print(f"获取到 {len(ticks)} 条记录")
                    ticks_data = [l2tick_to_dict(tick) for tick in ticks]
                    analysis = analyze_l2ticks(ticks_data)
                    
                    all_results[symbol] = {
                        "data_count": len(ticks_data),
                        "analysis": analysis
                    }
                    
                else:
                    print("未获取到数据")
                    all_results[symbol] = {"data_count": 0}
                    
            except Exception as e:
                print(f"查询 {symbol} 失败: {e}")
                all_results[symbol] = {"error": str(e)}
        
        # 保存汇总结果
        summary_result = {
            "query_params": {
                "symbols": symbols,
                "start_time": start_time.strftime('%Y-%m-%d %H:%M:%S'),
                "end_time": end_time.strftime('%Y-%m-%d %H:%M:%S')
            },
            "results": all_results
        }
        
        save_results(summary_result, "multiple_symbols")
        
        # 显示汇总信息
        print("\n汇总结果:")
        for symbol, result in all_results.items():
            if 'error' in result:
                print(f"{symbol}: 查询失败 - {result['error']}")
            else:
                print(f"{symbol}: {result['data_count']} 条记录")
        
    except Exception as e:
        print(f"测试失败: {e}")


def test_get_history_ticks_l2_time_periods():
    """
    测试不同时间段的历史L2逐笔成交数据查询
    """
    print("\n=== 测试不同时间段的历史L2逐笔成交数据查询 ===")
    
    symbol = "SHSE.600000"  # 浦发银行
    
    time_periods = [
        {"name": "最近5分钟", "minutes": 5},
        {"name": "最近15分钟", "minutes": 15},
        {"name": "最近1小时", "minutes": 60}
    ]
    
    results = {}
    
    for period in time_periods:
        print(f"\n测试时间段: {period['name']}")
        
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(minutes=period['minutes'])
            
            ticks = gm.get_history_ticks_l2(
                symbol=symbol,
                start_time=start_time.strftime('%Y-%m-%d %H:%M:%S'),
                end_time=end_time.strftime('%Y-%m-%d %H:%M:%S')
            )
            
            if ticks:
                ticks_data = [l2tick_to_dict(tick) for tick in ticks]
                analysis = analyze_l2ticks(ticks_data)
                
                results[period['name']] = {
                    "data_count": len(ticks_data),
                    "time_range": f"{start_time.strftime('%H:%M:%S')} - {end_time.strftime('%H:%M:%S')}",
                    "analysis": analysis
                }
                
                print(f"获取到 {len(ticks_data)} 条记录")
                if 'volume_stats' in analysis:
                    print(f"总成交量: {analysis['volume_stats']['total']:,}")
                
            else:
                print("未获取到数据")
                results[period['name']] = {"data_count": 0}
                
        except Exception as e:
            print(f"查询失败: {e}")
            results[period['name']] = {"error": str(e)}
    
    # 保存时间段对比结果
    comparison_result = {
        "symbol": symbol,
        "time_periods": results
    }
    
    save_results(comparison_result, "time_periods_comparison")


def test_get_history_ticks_l2_data_analysis():
    """
    测试L2逐笔成交数据的深度分析
    """
    print("\n=== 测试L2逐笔成交数据深度分析 ===")
    
    try:
        symbol = "SHSE.600036"  # 招商银行
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=2)
        
        ticks = gm.get_history_ticks_l2(
            symbol=symbol,
            start_time=start_time.strftime('%Y-%m-%d %H:%M:%S'),
            end_time=end_time.strftime('%Y-%m-%d %H:%M:%S')
        )
        
        if ticks:
            ticks_data = [l2tick_to_dict(tick) for tick in ticks]
            df = pd.DataFrame(ticks_data)
            
            # 深度分析
            detailed_analysis = {
                "basic_info": {
                    "symbol": symbol,
                    "total_ticks": len(df),
                    "time_span_hours": 2
                },
                "trading_intensity": {},
                "price_movement": {},
                "volume_analysis": {},
                "side_analysis": {}
            }
            
            # 交易强度分析
            if 'created_at' in df.columns:
                df['created_at'] = pd.to_datetime(df['created_at'])
                df['minute'] = df['created_at'].dt.floor('T')
                minute_counts = df.groupby('minute').size()
                
                detailed_analysis["trading_intensity"] = {
                    "avg_ticks_per_minute": float(minute_counts.mean()),
                    "max_ticks_per_minute": int(minute_counts.max()),
                    "min_ticks_per_minute": int(minute_counts.min())
                }
            
            # 价格波动分析
            if 'price' in df.columns:
                prices = df['price'].astype(float)
                detailed_analysis["price_movement"] = {
                    "price_range": float(prices.max() - prices.min()),
                    "price_volatility": float(prices.std()),
                    "price_change_pct": float((prices.iloc[-1] - prices.iloc[0]) / prices.iloc[0] * 100)
                }
            
            # 成交量分析
            if 'volume' in df.columns:
                volumes = df['volume'].astype(int)
                detailed_analysis["volume_analysis"] = {
                    "total_volume": int(volumes.sum()),
                    "avg_volume_per_tick": float(volumes.mean()),
                    "large_trades_count": int((volumes > volumes.quantile(0.9)).sum())
                }
            
            # 买卖方向分析
            if 'side' in df.columns:
                side_counts = df['side'].value_counts()
                detailed_analysis["side_analysis"] = {
                    "buy_ratio": float(side_counts.get('Buy', 0) / len(df)),
                    "sell_ratio": float(side_counts.get('Sell', 0) / len(df)),
                    "side_distribution": side_counts.to_dict()
                }
            
            # 保存详细分析结果
            save_results(detailed_analysis, "detailed_analysis")
            
            print("\n详细分析结果:")
            print(f"总逐笔数: {detailed_analysis['basic_info']['total_ticks']}")
            if detailed_analysis['trading_intensity']:
                print(f"平均每分钟逐笔数: {detailed_analysis['trading_intensity']['avg_ticks_per_minute']:.1f}")
            if detailed_analysis['price_movement']:
                print(f"价格波动范围: {detailed_analysis['price_movement']['price_range']:.4f}")
            
        else:
            print("未获取到数据进行分析")
            
    except Exception as e:
        print(f"深度分析测试失败: {e}")


def main():
    """
    主函数
    """
    print("GM API - get_history_ticks_l2 接口测试")
    print("=" * 50)
    
    # 初始化API
    if not init_gm_api():
        print("API初始化失败，退出测试")
        return
    
    # 执行测试
    test_get_history_ticks_l2_single_symbol()
    test_get_history_ticks_l2_multiple_symbols()
    test_get_history_ticks_l2_time_periods()
    test_get_history_ticks_l2_data_analysis()
    
    print("\n=== 所有测试完成 ===")


if __name__ == '__main__':
    main()