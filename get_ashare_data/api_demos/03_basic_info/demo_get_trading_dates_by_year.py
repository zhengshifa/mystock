#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GM API - get_trading_dates_by_year 接口测试

本脚本测试 gm.get_trading_dates_by_year() API，用于获取指定年份的交易日期。
该接口可以快速获取某一年的所有交易日，便于进行年度数据分析。

主要功能:
1. 获取指定年份的交易日期
2. 分析交易日分布特征
3. 统计交易日数量
4. 节假日分析

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
import calendar


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


def analyze_trading_dates(trading_dates: List[str], year: int) -> Dict[str, Any]:
    """
    分析交易日期数据
    
    Args:
        trading_dates: 交易日期列表
        year: 年份
    
    Returns:
        Dict[str, Any]: 分析结果
    """
    if not trading_dates:
        return {"error": "没有交易日期数据"}
    
    # 转换为datetime对象
    dates = [datetime.strptime(date, '%Y-%m-%d') for date in trading_dates]
    
    analysis = {
        "basic_stats": {
            "year": year,
            "total_trading_days": len(dates),
            "first_trading_day": trading_dates[0],
            "last_trading_day": trading_dates[-1],
            "date_range": f"{trading_dates[0]} 到 {trading_dates[-1]}"
        },
        "monthly_distribution": {},
        "weekday_distribution": {},
        "holiday_analysis": {},
        "quarterly_stats": {}
    }
    
    # 按月份分布
    monthly_counts = {}
    for date in dates:
        month = date.month
        monthly_counts[month] = monthly_counts.get(month, 0) + 1
    
    analysis["monthly_distribution"] = {
        f"{month}月": count for month, count in monthly_counts.items()
    }
    
    # 按星期分布
    weekday_counts = {}
    weekday_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    for date in dates:
        weekday = date.weekday()
        weekday_counts[weekday] = weekday_counts.get(weekday, 0) + 1
    
    analysis["weekday_distribution"] = {
        weekday_names[weekday]: count for weekday, count in weekday_counts.items()
    }
    
    # 季度统计
    quarterly_counts = {1: 0, 2: 0, 3: 0, 4: 0}
    for date in dates:
        quarter = (date.month - 1) // 3 + 1
        quarterly_counts[quarter] += 1
    
    analysis["quarterly_stats"] = {
        f"Q{quarter}": count for quarter, count in quarterly_counts.items()
    }
    
    # 节假日分析（通过找出缺失的工作日）
    all_dates_in_year = pd.date_range(start=f'{year}-01-01', end=f'{year}-12-31', freq='D')
    weekdays = all_dates_in_year[all_dates_in_year.weekday < 5]  # 工作日
    trading_date_set = set(dates)
    
    non_trading_weekdays = []
    for date in weekdays:
        if date not in trading_date_set:
            non_trading_weekdays.append(date.strftime('%Y-%m-%d'))
    
    analysis["holiday_analysis"] = {
        "total_weekdays": len(weekdays),
        "non_trading_weekdays": len(non_trading_weekdays),
        "trading_day_ratio": len(dates) / len(weekdays) * 100,
        "major_holidays": non_trading_weekdays[:20]  # 显示前20个非交易工作日
    }
    
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
    results_dir = Path("results/trading_dates_by_year")
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存JSON格式
    json_file = results_dir / f"{filename_prefix}_{timestamp}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    
    # 保存交易日期为文本文件
    if 'trading_dates' in data:
        txt_file = results_dir / f"{filename_prefix}_{timestamp}.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(f"# {data.get('year', 'Unknown')}年交易日期\n")
            f.write(f"# 总计: {len(data['trading_dates'])} 个交易日\n\n")
            for date in data['trading_dates']:
                f.write(f"{date}\n")
        print(f"交易日期文本已保存到: {txt_file}")
    
    print(f"JSON结果已保存到: {json_file}")


def test_get_trading_dates_current_year():
    """
    测试获取当前年份的交易日期
    """
    print("\n=== 测试获取当前年份的交易日期 ===")
    
    try:
        current_year = datetime.now().year
        print(f"查询年份: {current_year}")
        
        # 调用API
        trading_dates = gm.get_trading_dates_by_year(year=current_year)
        
        if trading_dates:
            print(f"获取到 {len(trading_dates)} 个交易日")
            
            # 分析数据
            analysis = analyze_trading_dates(trading_dates, current_year)
            
            # 保存结果
            result = {
                "year": current_year,
                "trading_dates": trading_dates,
                "analysis": analysis
            }
            
            save_results(result, f"year_{current_year}")
            
            # 显示分析结果
            print(f"\n分析结果:")
            print(f"- 总交易日数: {analysis['basic_stats']['total_trading_days']}")
            print(f"- 首个交易日: {analysis['basic_stats']['first_trading_day']}")
            print(f"- 最后交易日: {analysis['basic_stats']['last_trading_day']}")
            
            if analysis['monthly_distribution']:
                print("\n月度分布:")
                for month, count in analysis['monthly_distribution'].items():
                    print(f"  {month}: {count}天")
            
            if analysis['quarterly_stats']:
                print("\n季度分布:")
                for quarter, count in analysis['quarterly_stats'].items():
                    print(f"  {quarter}: {count}天")
            
        else:
            print("未获取到交易日期数据")
            
    except Exception as e:
        print(f"测试失败: {e}")


def test_get_trading_dates_historical_years():
    """
    测试获取历史年份的交易日期
    """
    print("\n=== 测试获取历史年份的交易日期 ===")
    
    # 测试最近几年的交易日期
    current_year = datetime.now().year
    test_years = [current_year - 3, current_year - 2, current_year - 1]
    
    all_results = {}
    
    for year in test_years:
        print(f"\n查询年份: {year}")
        
        try:
            trading_dates = gm.get_trading_dates_by_year(year=year)
            
            if trading_dates:
                print(f"获取到 {len(trading_dates)} 个交易日")
                
                analysis = analyze_trading_dates(trading_dates, year)
                
                all_results[str(year)] = {
                    "trading_dates_count": len(trading_dates),
                    "first_day": trading_dates[0],
                    "last_day": trading_dates[-1],
                    "analysis": analysis
                }
                
                # 保存单年结果
                result = {
                    "year": year,
                    "trading_dates": trading_dates,
                    "analysis": analysis
                }
                save_results(result, f"historical_year_{year}")
                
            else:
                print(f"年份 {year} 未获取到数据")
                all_results[str(year)] = {"error": "无数据"}
                
        except Exception as e:
            print(f"查询年份 {year} 失败: {e}")
            all_results[str(year)] = {"error": str(e)}
    
    # 保存汇总结果
    summary_result = {
        "query_years": test_years,
        "results": all_results
    }
    
    save_results(summary_result, "historical_years_summary")
    
    # 显示汇总信息
    print("\n历史年份汇总:")
    for year, result in all_results.items():
        if 'error' in result:
            print(f"{year}年: 查询失败 - {result['error']}")
        else:
            print(f"{year}年: {result['trading_dates_count']} 个交易日")


def test_get_trading_dates_comparison():
    """
    测试多年交易日期对比分析
    """
    print("\n=== 测试多年交易日期对比分析 ===")
    
    try:
        current_year = datetime.now().year
        comparison_years = [current_year - 2, current_year - 1, current_year]
        
        comparison_data = {}
        
        for year in comparison_years:
            print(f"获取 {year} 年数据...")
            
            trading_dates = gm.get_trading_dates_by_year(year=year)
            
            if trading_dates:
                analysis = analyze_trading_dates(trading_dates, year)
                comparison_data[str(year)] = {
                    "total_days": len(trading_dates),
                    "monthly_distribution": analysis['monthly_distribution'],
                    "quarterly_stats": analysis['quarterly_stats'],
                    "trading_ratio": analysis['holiday_analysis']['trading_day_ratio']
                }
            else:
                comparison_data[str(year)] = {"error": "无数据"}
        
        # 生成对比分析
        comparison_analysis = {
            "years_compared": comparison_years,
            "data": comparison_data,
            "trends": {}
        }
        
        # 分析趋势
        valid_years = [year for year in comparison_years 
                      if str(year) in comparison_data and 'error' not in comparison_data[str(year)]]
        
        if len(valid_years) >= 2:
            total_days_trend = [comparison_data[str(year)]['total_days'] for year in valid_years]
            comparison_analysis['trends'] = {
                "total_days_change": total_days_trend[-1] - total_days_trend[0],
                "avg_trading_days": sum(total_days_trend) / len(total_days_trend),
                "max_trading_days": max(total_days_trend),
                "min_trading_days": min(total_days_trend)
            }
        
        # 保存对比结果
        save_results(comparison_analysis, "years_comparison")
        
        # 显示对比结果
        print("\n多年对比结果:")
        for year in comparison_years:
            year_str = str(year)
            if year_str in comparison_data and 'error' not in comparison_data[year_str]:
                data = comparison_data[year_str]
                print(f"{year}年: {data['total_days']} 个交易日 (交易率: {data['trading_ratio']:.1f}%)")
            else:
                print(f"{year}年: 数据获取失败")
        
        if comparison_analysis['trends']:
            trends = comparison_analysis['trends']
            print(f"\n趋势分析:")
            print(f"- 平均交易日数: {trends['avg_trading_days']:.1f}")
            print(f"- 最多交易日数: {trends['max_trading_days']}")
            print(f"- 最少交易日数: {trends['min_trading_days']}")
        
    except Exception as e:
        print(f"对比分析测试失败: {e}")


def test_get_trading_dates_edge_cases():
    """
    测试边界情况
    """
    print("\n=== 测试边界情况 ===")
    
    test_cases = [
        {"name": "未来年份", "year": datetime.now().year + 1},
        {"name": "很早的年份", "year": 1990},
        {"name": "无效年份", "year": 0},
        {"name": "负数年份", "year": -2023}
    ]
    
    for case in test_cases:
        print(f"\n测试: {case['name']} ({case['year']})")
        
        try:
            trading_dates = gm.get_trading_dates_by_year(year=case['year'])
            
            if trading_dates:
                print(f"获取到 {len(trading_dates)} 个交易日")
                print(f"日期范围: {trading_dates[0]} 到 {trading_dates[-1]}")
            else:
                print("未获取到数据")
                
        except Exception as e:
            print(f"出现异常: {e}")


def main():
    """
    主函数
    """
    print("GM API - get_trading_dates_by_year 接口测试")
    print("=" * 50)
    
    # 初始化API
    if not init_gm_api():
        print("API初始化失败，退出测试")
        return
    
    # 执行测试
    test_get_trading_dates_current_year()
    test_get_trading_dates_historical_years()
    test_get_trading_dates_comparison()
    test_get_trading_dates_edge_cases()
    
    print("\n=== 所有测试完成 ===")


if __name__ == '__main__':
    main()