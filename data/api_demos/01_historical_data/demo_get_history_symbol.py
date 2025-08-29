#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GM API - get_history_symbol 接口测试

本脚本测试 gm.get_history_symbol() API，用于获取历史交易标的信息。
该接口可以查询指定时间段内的历史标的信息变化。

主要功能:
1. 获取历史标的信息
2. 分析标的信息变化
3. 数据统计和可视化
4. 结果保存

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


def symbol_info_to_dict(symbol_info) -> Dict[str, Any]:
    """
    将标的信息对象转换为字典
    
    Args:
        symbol_info: 标的信息对象
    
    Returns:
        Dict[str, Any]: 标的信息字典
    """
    if symbol_info is None:
        return {}
    
    result = {}
    
    # 获取所有属性
    for attr in dir(symbol_info):
        if not attr.startswith('_'):
            try:
                value = getattr(symbol_info, attr)
                if not callable(value):
                    # 处理datetime对象
                    if isinstance(value, datetime):
                        result[attr] = value.isoformat()
                    else:
                        result[attr] = value
            except Exception as e:
                result[attr] = f"Error: {str(e)}"
    
    return result


def analyze_history_symbols(symbols_data: List[Dict]) -> Dict[str, Any]:
    """
    分析历史标的信息数据
    
    Args:
        symbols_data: 标的信息数据列表
    
    Returns:
        Dict[str, Any]: 分析结果
    """
    if not symbols_data:
        return {"error": "没有数据可分析"}
    
    df = pd.DataFrame(symbols_data)
    
    analysis = {
        "basic_stats": {
            "total_records": len(df),
            "unique_symbols": df['symbol'].nunique() if 'symbol' in df.columns else 0,
            "date_range": {
                "start": df['created_at'].min() if 'created_at' in df.columns else None,
                "end": df['created_at'].max() if 'created_at' in df.columns else None
            }
        },
        "symbol_distribution": {},
        "exchange_distribution": {},
        "sec_type_distribution": {},
        "status_distribution": {}
    }
    
    # 标的分布
    if 'symbol' in df.columns:
        analysis["symbol_distribution"] = df['symbol'].value_counts().head(10).to_dict()
    
    # 交易所分布
    if 'exchange' in df.columns:
        analysis["exchange_distribution"] = df['exchange'].value_counts().to_dict()
    
    # 证券类型分布
    if 'sec_type' in df.columns:
        analysis["sec_type_distribution"] = df['sec_type'].value_counts().to_dict()
    
    # 状态分布
    if 'status' in df.columns:
        analysis["status_distribution"] = df['status'].value_counts().to_dict()
    
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
    results_dir = Path("results/history_symbol")
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存JSON格式
    json_file = results_dir / f"{filename_prefix}_{timestamp}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"结果已保存到: {json_file}")


def test_get_history_symbol_basic():
    """
    测试基本的历史标的信息查询
    """
    print("\n=== 测试基本历史标的信息查询 ===")
    
    try:
        # 查询最近30天的历史标的信息
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        print(f"查询时间范围: {start_date.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')}")
        
        # 调用API
        symbols_info = gm.get_history_symbol(
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )
        
        if symbols_info:
            print(f"获取到 {len(symbols_info)} 条历史标的信息")
            
            # 转换为字典格式
            symbols_data = [symbol_info_to_dict(info) for info in symbols_info]
            
            # 分析数据
            analysis = analyze_history_symbols(symbols_data)
            
            # 保存结果
            result = {
                "query_params": {
                    "start_date": start_date.strftime('%Y-%m-%d'),
                    "end_date": end_date.strftime('%Y-%m-%d')
                },
                "data": symbols_data[:100],  # 只保存前100条
                "analysis": analysis,
                "total_count": len(symbols_data)
            }
            
            save_results(result, "basic_query")
            
            # 显示部分结果
            print("\n前5条记录:")
            for i, symbol_data in enumerate(symbols_data[:5]):
                print(f"{i+1}. {symbol_data.get('symbol', 'N/A')} - {symbol_data.get('sec_name', 'N/A')}")
            
            print(f"\n分析结果:")
            print(f"- 总记录数: {analysis['basic_stats']['total_records']}")
            print(f"- 唯一标的数: {analysis['basic_stats']['unique_symbols']}")
            
        else:
            print("未获取到历史标的信息")
            
    except Exception as e:
        print(f"测试失败: {e}")


def test_get_history_symbol_with_filters():
    """
    测试带过滤条件的历史标的信息查询
    """
    print("\n=== 测试带过滤条件的历史标的信息查询 ===")
    
    try:
        # 查询特定交易所的历史标的信息
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        exchanges = ['SHSE', 'SZSE']
        
        for exchange in exchanges:
            print(f"\n查询交易所: {exchange}")
            
            # 调用API（注意：实际参数可能需要根据API文档调整）
            symbols_info = gm.get_history_symbol(
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d'),
                exchange=exchange
            )
            
            if symbols_info:
                print(f"获取到 {len(symbols_info)} 条记录")
                
                # 转换为字典格式
                symbols_data = [symbol_info_to_dict(info) for info in symbols_info]
                
                # 分析数据
                analysis = analyze_history_symbols(symbols_data)
                
                # 保存结果
                result = {
                    "query_params": {
                        "start_date": start_date.strftime('%Y-%m-%d'),
                        "end_date": end_date.strftime('%Y-%m-%d'),
                        "exchange": exchange
                    },
                    "data": symbols_data,
                    "analysis": analysis
                }
                
                save_results(result, f"exchange_{exchange.lower()}")
                
            else:
                print(f"交易所 {exchange} 未获取到数据")
                
    except Exception as e:
        print(f"测试失败: {e}")


def test_get_history_symbol_edge_cases():
    """
    测试边界情况
    """
    print("\n=== 测试边界情况 ===")
    
    test_cases = [
        {
            "name": "查询未来日期",
            "start_date": (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
            "end_date": (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        },
        {
            "name": "查询很久以前的日期",
            "start_date": "2000-01-01",
            "end_date": "2000-01-07"
        },
        {
            "name": "开始日期晚于结束日期",
            "start_date": datetime.now().strftime('%Y-%m-%d'),
            "end_date": (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        }
    ]
    
    for case in test_cases:
        print(f"\n测试: {case['name']}")
        try:
            symbols_info = gm.get_history_symbol(
                start_date=case['start_date'],
                end_date=case['end_date']
            )
            
            if symbols_info:
                print(f"获取到 {len(symbols_info)} 条记录")
            else:
                print("未获取到数据")
                
        except Exception as e:
            print(f"出现异常: {e}")


def test_get_history_symbol_data_analysis():
    """
    测试数据分析功能
    """
    print("\n=== 测试数据分析功能 ===")
    
    try:
        # 查询最近一周的数据
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        symbols_info = gm.get_history_symbol(
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )
        
        if symbols_info:
            symbols_data = [symbol_info_to_dict(info) for info in symbols_info]
            analysis = analyze_history_symbols(symbols_data)
            
            print("\n数据分析结果:")
            print(f"总记录数: {analysis['basic_stats']['total_records']}")
            print(f"唯一标的数: {analysis['basic_stats']['unique_symbols']}")
            
            if analysis['exchange_distribution']:
                print("\n交易所分布:")
                for exchange, count in analysis['exchange_distribution'].items():
                    print(f"  {exchange}: {count}")
            
            if analysis['sec_type_distribution']:
                print("\n证券类型分布:")
                for sec_type, count in analysis['sec_type_distribution'].items():
                    print(f"  {sec_type}: {count}")
            
            # 保存详细分析结果
            save_results(analysis, "detailed_analysis")
            
        else:
            print("未获取到数据进行分析")
            
    except Exception as e:
        print(f"数据分析测试失败: {e}")


def main():
    """
    主函数
    """
    print("GM API - get_history_symbol 接口测试")
    print("=" * 50)
    
    # 初始化API
    if not init_gm_api():
        print("API初始化失败，退出测试")
        return
    
    # 执行测试
    test_get_history_symbol_basic()
    test_get_history_symbol_with_filters()
    test_get_history_symbol_edge_cases()
    test_get_history_symbol_data_analysis()
    
    print("\n=== 所有测试完成 ===")


if __name__ == '__main__':
    main()