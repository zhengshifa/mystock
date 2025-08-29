#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
沪深港通数据查询演示

本脚本演示如何使用GM SDK获取沪深港通相关数据，包括：
1. stk_quota_shszhk_infos - 查询沪深港通额度信息
2. stk_hk_inst_holding_info - 查询港股通机构持股信息
3. stk_hk_inst_holding_detail_info - 查询港股通机构持股明细
4. 沪深港通资金流向分析
5. 港股通持股变化趋势分析

沪深港通数据反映了内地与香港市场的资金流动情况，是重要的市场情绪指标
"""

import pandas as pd
import json
from datetime import datetime, timedelta
from gm.api import *
import os

# ============================================================
# Token配置 - 从配置文件读取
# ============================================================

def configure_token():
    """
    配置GM SDK的token
    支持多种配置方式：
    1. 从配置文件读取（推荐）
    2. 从环境变量读取
    3. 直接设置token
    """
    
    # 方法1: 从配置文件读取（推荐）
    config_file = 'gm_config.json'
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                if 'token' in config and config['token']:
                    set_token(config['token'])
                    print(f"已从配置文件 {config_file} 读取token")
                    return True
        except Exception as e:
            print(f"读取配置文件失败: {e}")
    
    # 方法2: 从环境变量读取
    token = os.getenv('GM_TOKEN')
    if token:
        set_token(token)
        print("已从环境变量 GM_TOKEN 读取token")
        return True
    
    # 方法3: 直接设置token（备用）
    set_token('d5791ecb0f33260e9fd719227c36f5c28b42e11c')
    print("使用默认token")
    return True

def test_hk_connect_quota():
    """
    测试沪深港通额度信息
    """
    print("\n=== 测试 stk_quota_shszhk_infos 函数 - 获取沪深港通额度信息 ===")
    
    test_results = []
    
    try:
        # 获取最近几个交易日的额度信息
        end_date = datetime.now()
        start_date = end_date - timedelta(days=10)
        
        # 格式化日期
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        print(f"查询时间范围: {start_date_str} 到 {end_date_str}")
        
        result = stk_quota_shszhk_infos(
            start_date=start_date_str,
            end_date=end_date_str
        )
        
        if result:
            print(f"✓ 成功获取沪深港通额度数据，共 {len(result)} 条记录")
            
            # 转换为DataFrame
            df = pd.DataFrame(result)
            
            # 显示数据概览
            print(f"\n数据时间范围: {df['trade_date'].min()} 到 {df['trade_date'].max()}")
            
            # 分析额度使用情况
            analyze_quota_usage(df)
            
            # 保存数据
            csv_filename = f"hk_connect_quota_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv"
            df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
            print(f"\n✓ 额度数据已保存到 {csv_filename}")
            
            test_result = {
                'test_name': '沪深港通额度查询',
                'function': 'stk_quota_shszhk_infos',
                'status': 'success',
                'data_count': len(result),
                'date_range': f"{start_date_str} - {end_date_str}",
                'sample_data': result[:3]
            }
        else:
            print("✗ 未获取到沪深港通额度数据")
            test_result = {
                'test_name': '沪深港通额度查询',
                'function': 'stk_quota_shszhk_infos',
                'status': 'no_data',
                'date_range': f"{start_date_str} - {end_date_str}"
            }
            
    except Exception as e:
        print(f"✗ 获取沪深港通额度数据错误: {e}")
        test_result = {
            'test_name': '沪深港通额度查询',
            'function': 'stk_quota_shszhk_infos',
            'status': 'error',
            'error': str(e)
        }
    
    test_results.append(test_result)
    return test_results

def analyze_quota_usage(df):
    """
    分析额度使用情况
    """
    print("\n=== 沪深港通额度使用分析 ===")
    
    try:
        if df.empty:
            print("无数据可分析")
            return
        
        # 分析各通道的额度使用情况
        channels = ['沪股通', '深股通', '港股通(沪)', '港股通(深)']
        
        for channel in channels:
            channel_data = df[df['channel_name'].str.contains(channel, na=False)] if 'channel_name' in df.columns else pd.DataFrame()
            
            if not channel_data.empty:
                print(f"\n{channel}:")
                
                # 计算平均使用率
                if 'quota_balance' in df.columns and 'quota_daily' in df.columns:
                    avg_usage_rate = ((df['quota_daily'] - df['quota_balance']) / df['quota_daily'] * 100).mean()
                    print(f"  平均使用率: {avg_usage_rate:.2f}%")
                
                # 最新额度情况
                latest_data = channel_data.iloc[-1] if not channel_data.empty else None
                if latest_data is not None:
                    daily_quota = latest_data.get('quota_daily', 0)
                    balance = latest_data.get('quota_balance', 0)
                    used = daily_quota - balance
                    usage_rate = (used / daily_quota * 100) if daily_quota > 0 else 0
                    
                    print(f"  最新日期: {latest_data.get('trade_date', 'N/A')}")
                    print(f"  每日额度: {daily_quota:,.0f} 万元")
                    print(f"  已使用: {used:,.0f} 万元")
                    print(f"  剩余额度: {balance:,.0f} 万元")
                    print(f"  使用率: {usage_rate:.2f}%")
        
        # 分析资金流向趋势
        if 'trade_date' in df.columns and 'quota_balance' in df.columns:
            print("\n=== 资金流向趋势 ===")
            
            # 按日期分组计算总使用额度
            daily_usage = df.groupby('trade_date').apply(
                lambda x: (x['quota_daily'] - x['quota_balance']).sum()
            ).reset_index()
            daily_usage.columns = ['trade_date', 'total_usage']
            
            if not daily_usage.empty:
                print(f"最近5个交易日使用情况:")
                for _, row in daily_usage.tail(5).iterrows():
                    print(f"  {row['trade_date']}: {row['total_usage']:,.0f} 万元")
                
                # 计算趋势
                if len(daily_usage) >= 2:
                    recent_avg = daily_usage.tail(3)['total_usage'].mean()
                    earlier_avg = daily_usage.head(3)['total_usage'].mean()
                    trend = "上升" if recent_avg > earlier_avg else "下降"
                    print(f"\n资金流向趋势: {trend}")
                    print(f"近期平均: {recent_avg:,.0f} 万元")
                    print(f"早期平均: {earlier_avg:,.0f} 万元")
        
    except Exception as e:
        print(f"✗ 额度使用分析错误: {e}")

def test_hk_inst_holding():
    """
    测试港股通机构持股信息
    """
    print("\n=== 测试 stk_hk_inst_holding_info 函数 - 获取港股通机构持股信息 ===")
    
    test_results = []
    
    # 热门港股通标的
    hk_connect_stocks = [
        'SHSE.600519',  # 贵州茅台
        'SHSE.600036',  # 招商银行
        'SZSE.000858',  # 五粮液
        'SZSE.300750',  # 宁德时代
        'SHSE.600000',  # 浦发银行
        'SZSE.002415',  # 海康威视
        'SHSE.601318',  # 中国平安
        'SZSE.000002'   # 万科A
    ]
    
    try:
        # 获取最近的交易日
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # 格式化日期
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        all_holding_data = []
        
        for symbol in hk_connect_stocks[:5]:  # 测试前5只股票
            print(f"\n查询 {symbol} 的港股通机构持股信息...")
            
            try:
                result = stk_hk_inst_holding_info(
                    symbols=[symbol]
                )
                
                if result:
                    all_holding_data.extend(result)
                    print(f"  ✓ {symbol}: 成功获取 {len(result)} 条持股记录")
                    
                    # 显示最新持股情况
                    latest_holding = result[-1] if result else None
                    if latest_holding:
                        holding_shares = latest_holding.get('holding_shares', 0)
                        holding_ratio = latest_holding.get('holding_ratio', 0)
                        trade_date = latest_holding.get('trade_date', 'N/A')
                        
                        print(f"    最新日期: {trade_date}")
                        print(f"    持股数量: {holding_shares:,.0f} 股")
                        print(f"    持股比例: {holding_ratio:.4f}%")
                else:
                    print(f"  ✗ {symbol}: 无港股通持股数据")
                    
            except Exception as e:
                print(f"  ✗ {symbol}: 错误 - {e}")
        
        if all_holding_data:
            # 保存所有数据
            df = pd.DataFrame(all_holding_data)
            csv_filename = f"hk_inst_holding_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv"
            df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
            print(f"\n✓ 港股通持股数据已保存到 {csv_filename}")
            
            # 分析持股变化
            analyze_holding_changes(df)
            
            test_result = {
                'test_name': '港股通机构持股查询',
                'function': 'stk_hk_inst_holding_info',
                'status': 'success',
                'symbols_count': len(hk_connect_stocks[:5]),
                'data_count': len(all_holding_data),
                'date_range': f"{start_date_str} - {end_date_str}",
                'sample_data': all_holding_data[:3]
            }
        else:
            test_result = {
                'test_name': '港股通机构持股查询',
                'function': 'stk_hk_inst_holding_info',
                'status': 'no_data',
                'date_range': f"{start_date_str} - {end_date_str}"
            }
            
    except Exception as e:
        print(f"✗ 港股通机构持股查询错误: {e}")
        test_result = {
            'test_name': '港股通机构持股查询',
            'function': 'stk_hk_inst_holding_info',
            'status': 'error',
            'error': str(e)
        }
    
    test_results.append(test_result)
    return test_results

def analyze_holding_changes(df):
    """
    分析持股变化
    """
    print("\n=== 港股通持股变化分析 ===")
    
    try:
        if df.empty:
            print("无数据可分析")
            return
        
        # 按股票分组分析
        if 'symbol' in df.columns:
            symbols = df['symbol'].unique()
            
            for symbol in symbols[:5]:  # 分析前5只股票
                symbol_data = df[df['symbol'] == symbol].sort_values('trade_date')
                
                if len(symbol_data) >= 2:
                    print(f"\n{symbol}:")
                    
                    # 计算持股变化
                    latest = symbol_data.iloc[-1]
                    earliest = symbol_data.iloc[0]
                    
                    shares_change = latest.get('holding_shares', 0) - earliest.get('holding_shares', 0)
                    ratio_change = latest.get('holding_ratio', 0) - earliest.get('holding_ratio', 0)
                    
                    print(f"  时间范围: {earliest.get('trade_date')} 到 {latest.get('trade_date')}")
                    print(f"  持股数量变化: {shares_change:+,.0f} 股")
                    print(f"  持股比例变化: {ratio_change:+.4f}%")
                    
                    # 判断趋势
                    if shares_change > 0:
                        trend = "增持"
                    elif shares_change < 0:
                        trend = "减持"
                    else:
                        trend = "持平"
                    
                    print(f"  持股趋势: {trend}")
        
        # 整体持股统计
        if 'holding_shares' in df.columns and 'holding_ratio' in df.columns:
            print("\n=== 整体持股统计 ===")
            
            total_holding_shares = df['holding_shares'].sum()
            avg_holding_ratio = df['holding_ratio'].mean()
            
            print(f"总持股数量: {total_holding_shares:,.0f} 股")
            print(f"平均持股比例: {avg_holding_ratio:.4f}%")
            
            # 持股比例分布
            high_holding = df[df['holding_ratio'] >= 1.0]  # 持股比例>=1%
            medium_holding = df[(df['holding_ratio'] >= 0.5) & (df['holding_ratio'] < 1.0)]  # 0.5%-1%
            low_holding = df[df['holding_ratio'] < 0.5]  # <0.5%
            
            print(f"\n持股比例分布:")
            print(f"  高持股(>=1%): {len(high_holding)} 条记录")
            print(f"  中持股(0.5%-1%): {len(medium_holding)} 条记录")
            print(f"  低持股(<0.5%): {len(low_holding)} 条记录")
        
    except Exception as e:
        print(f"✗ 持股变化分析错误: {e}")

def test_hk_inst_holding_detail():
    """
    测试港股通机构持股明细
    """
    print("\n=== 测试 stk_hk_inst_holding_detail_info 函数 - 获取港股通机构持股明细 ===")
    
    test_results = []
    
    # 选择几只代表性股票
    test_symbols = ['SHSE.600519', 'SHSE.600036', 'SZSE.000858']
    
    try:
        # 获取最近的交易日
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # 格式化日期
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        all_detail_data = []
        
        for symbol in test_symbols:
            print(f"\n查询 {symbol} 的港股通机构持股明细...")
            
            try:
                result = stk_hk_inst_holding_detail_info(
                    symbols=[symbol]
                )
                
                if result:
                    all_detail_data.extend(result)
                    print(f"  ✓ {symbol}: 成功获取 {len(result)} 条明细记录")
                    
                    # 显示机构类型分布
                    df_symbol = pd.DataFrame(result)
                    if 'participant_code' in df_symbol.columns:
                        participant_counts = df_symbol['participant_code'].value_counts()
                        print(f"  参与机构数: {len(participant_counts)}")
                        print(f"  主要参与机构: {list(participant_counts.head(3).index)}")
                else:
                    print(f"  ✗ {symbol}: 无港股通持股明细数据")
                    
            except Exception as e:
                print(f"  ✗ {symbol}: 错误 - {e}")
        
        if all_detail_data:
            # 保存所有明细数据
            df = pd.DataFrame(all_detail_data)
            csv_filename = f"hk_inst_holding_detail_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv"
            df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
            print(f"\n✓ 港股通持股明细数据已保存到 {csv_filename}")
            
            # 分析机构持股明细
            analyze_institutional_details(df)
            
            test_result = {
                'test_name': '港股通机构持股明细查询',
                'function': 'stk_hk_inst_holding_detail_info',
                'status': 'success',
                'symbols_count': len(test_symbols),
                'data_count': len(all_detail_data),
                'date_range': f"{start_date_str} - {end_date_str}",
                'sample_data': all_detail_data[:3]
            }
        else:
            test_result = {
                'test_name': '港股通机构持股明细查询',
                'function': 'stk_hk_inst_holding_detail_info',
                'status': 'no_data',
                'date_range': f"{start_date_str} - {end_date_str}"
            }
            
    except Exception as e:
        print(f"✗ 港股通机构持股明细查询错误: {e}")
        test_result = {
            'test_name': '港股通机构持股明细查询',
            'function': 'stk_hk_inst_holding_detail_info',
            'status': 'error',
            'error': str(e)
        }
    
    test_results.append(test_result)
    return test_results

def analyze_institutional_details(df):
    """
    分析机构持股明细
    """
    print("\n=== 机构持股明细分析 ===")
    
    try:
        if df.empty:
            print("无数据可分析")
            return
        
        # 机构参与度分析
        if 'participant_code' in df.columns:
            unique_participants = df['participant_code'].nunique()
            total_records = len(df)
            
            print(f"参与机构总数: {unique_participants}")
            print(f"持股记录总数: {total_records}")
            print(f"平均每机构记录数: {total_records/unique_participants:.1f}")
            
            # 最活跃机构
            participant_counts = df['participant_code'].value_counts()
            print(f"\n最活跃的5个机构:")
            for participant, count in participant_counts.head(5).items():
                print(f"  {participant}: {count} 条记录")
        
        # 持股金额分析
        if 'holding_market_cap' in df.columns:
            total_market_cap = df['holding_market_cap'].sum()
            avg_market_cap = df['holding_market_cap'].mean()
            
            print(f"\n持股市值分析:")
            print(f"  总持股市值: {total_market_cap:,.0f} 万元")
            print(f"  平均持股市值: {avg_market_cap:,.0f} 万元")
            
            # 持股规模分布
            large_holdings = df[df['holding_market_cap'] >= 10000]  # >=1亿元
            medium_holdings = df[(df['holding_market_cap'] >= 1000) & (df['holding_market_cap'] < 10000)]  # 1千万-1亿
            small_holdings = df[df['holding_market_cap'] < 1000]  # <1千万
            
            print(f"\n持股规模分布:")
            print(f"  大额持股(>=1亿): {len(large_holdings)} 条")
            print(f"  中额持股(1千万-1亿): {len(medium_holdings)} 条")
            print(f"  小额持股(<1千万): {len(small_holdings)} 条")
        
        # 按股票分析
        if 'symbol' in df.columns:
            symbol_analysis = df.groupby('symbol').agg({
                'participant_code': 'nunique',
                'holding_shares': 'sum',
                'holding_market_cap': 'sum'
            }).reset_index()
            
            print(f"\n按股票分析:")
            for _, row in symbol_analysis.iterrows():
                symbol = row['symbol']
                participants = row['participant_code']
                shares = row['holding_shares']
                market_cap = row['holding_market_cap']
                
                print(f"  {symbol}: {participants}个机构, {shares:,.0f}股, {market_cap:,.0f}万元")
        
    except Exception as e:
        print(f"✗ 机构持股明细分析错误: {e}")

def test_comprehensive_hk_connect_analysis():
    """
    综合沪深港通分析
    """
    print("\n=== 综合沪深港通分析 ===")
    
    test_results = []
    
    try:
        # 获取最近的数据进行综合分析
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        analysis_summary = {
            'analysis_date': end_date_str,
            'quota_data_available': False,
            'holding_data_available': False,
            'detail_data_available': False
        }
        
        # 检查额度数据可用性
        try:
            quota_data = stk_quota_shszhk_infos(
                start_date=start_date_str,
                end_date=end_date_str
            )
            if quota_data:
                analysis_summary['quota_data_available'] = True
                analysis_summary['quota_records'] = len(quota_data)
                print(f"✓ 额度数据可用: {len(quota_data)} 条记录")
        except Exception as e:
            print(f"✗ 额度数据检查失败: {e}")
        
        # 检查持股数据可用性
        try:
            test_symbol = 'SHSE.600519'
            holding_data = stk_hk_inst_holding_info(
                symbols=[test_symbol]
            )
            if holding_data:
                analysis_summary['holding_data_available'] = True
                analysis_summary['holding_records'] = len(holding_data)
                print(f"✓ 持股数据可用: {len(holding_data)} 条记录")
        except Exception as e:
            print(f"✗ 持股数据检查失败: {e}")
        
        # 检查明细数据可用性
        try:
            detail_data = stk_hk_inst_holding_detail_info(
                symbols=[test_symbol]
            )
            if detail_data:
                analysis_summary['detail_data_available'] = True
                analysis_summary['detail_records'] = len(detail_data)
                print(f"✓ 明细数据可用: {len(detail_data)} 条记录")
        except Exception as e:
            print(f"✗ 明细数据检查失败: {e}")
        
        # 生成综合报告
        generate_hk_connect_report(analysis_summary)
        
        test_result = {
            'test_name': '综合沪深港通分析',
            'function': 'comprehensive_hk_connect_analysis',
            'status': 'success',
            'analysis_summary': analysis_summary
        }
        
    except Exception as e:
        print(f"✗ 综合沪深港通分析错误: {e}")
        test_result = {
            'test_name': '综合沪深港通分析',
            'function': 'comprehensive_hk_connect_analysis',
            'status': 'error',
            'error': str(e)
        }
    
    test_results.append(test_result)
    return test_results

def generate_hk_connect_report(analysis_summary):
    """
    生成沪深港通综合报告
    """
    print("\n=== 沪深港通数据可用性报告 ===")
    
    try:
        print(f"分析日期: {analysis_summary['analysis_date']}")
        
        # 数据可用性统计
        available_count = sum([
            analysis_summary.get('quota_data_available', False),
            analysis_summary.get('holding_data_available', False),
            analysis_summary.get('detail_data_available', False)
        ])
        
        print(f"\n数据可用性: {available_count}/3 类数据可用")
        print(f"额度数据: {'✓' if analysis_summary.get('quota_data_available') else '✗'}")
        print(f"持股数据: {'✓' if analysis_summary.get('holding_data_available') else '✗'}")
        print(f"明细数据: {'✓' if analysis_summary.get('detail_data_available') else '✗'}")
        
        # 数据量统计
        if analysis_summary.get('quota_records'):
            print(f"\n额度记录数: {analysis_summary['quota_records']}")
        if analysis_summary.get('holding_records'):
            print(f"持股记录数: {analysis_summary['holding_records']}")
        if analysis_summary.get('detail_records'):
            print(f"明细记录数: {analysis_summary['detail_records']}")
        
        # 保存报告
        report_df = pd.DataFrame([analysis_summary])
        report_df.to_csv('hk_connect_analysis_report.csv', index=False, encoding='utf-8-sig')
        print("\n✓ 沪深港通分析报告已保存到 hk_connect_analysis_report.csv")
        
        # 使用建议
        print("\n=== 使用建议 ===")
        if available_count >= 2:
            print("✓ 数据完整性良好，可进行深度分析")
        elif available_count == 1:
            print("⚠ 数据部分可用，建议检查数据源配置")
        else:
            print("✗ 数据不可用，请检查权限和网络连接")
        
    except Exception as e:
        print(f"✗ 生成沪深港通报告错误: {e}")

def main():
    """
    主函数
    """
    print("开始测试GM SDK 沪深港通数据查询功能...")
    print("=" * 60)
    
    # 配置token
    if not configure_token():
        print("Token配置失败，退出测试")
        return
    
    # 存储所有测试结果
    all_results = {
        'test_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'tests': {}
    }
    
    try:
        # 测试沪深港通额度信息
        quota_results = test_hk_connect_quota()
        all_results['tests']['hk_connect_quota'] = quota_results
        
        # 测试港股通机构持股信息
        holding_results = test_hk_inst_holding()
        all_results['tests']['hk_inst_holding'] = holding_results
        
        # 测试港股通机构持股明细
        detail_results = test_hk_inst_holding_detail()
        all_results['tests']['hk_inst_holding_detail'] = detail_results
        
        # 综合沪深港通分析
        comprehensive_results = test_comprehensive_hk_connect_analysis()
        all_results['tests']['comprehensive_hk_connect'] = comprehensive_results
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        all_results['error'] = str(e)
    
    # 保存测试结果
    with open('hk_connect_test_results.json', 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2, default=str)
    
    print("\n=== 测试总结 ===")
    print(f"测试时间: {all_results['test_time']}")
    
    if 'tests' in all_results:
        for test_type, results in all_results['tests'].items():
            if isinstance(results, list):
                total_tests = len(results)
                successful_tests = sum(1 for result in results if result.get('status') == 'success')
                print(f"{test_type}测试: {successful_tests}/{total_tests} 成功")
    
    print("\n✓ 测试结果已保存到 hk_connect_test_results.json")
    print("✓ CSV数据文件已保存到当前目录")
    print("\n沪深港通数据说明:")
    print("- 额度数据: 反映每日资金流入流出限额和使用情况")
    print("- 持股数据: 显示境外机构通过港股通持有A股的情况")
    print("- 明细数据: 提供具体机构的持股明细信息")
    print("- 数据更新: 通常在交易日结束后更新")
    print("- 分析价值: 反映外资对A股的配置偏好和流向趋势")

if __name__ == '__main__':
    main()