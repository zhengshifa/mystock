#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
市场深度数据查询演示

本脚本演示如何使用GM SDK获取市场深度数据，包括：
1. get_history_l2orders - 查询历史L2订单簿数据
2. get_history_l2transactions - 查询历史L2成交明细数据
3. get_history_l2ticks - 查询历史L2 Tick数据
4. 市场深度数据分析和可视化

市场深度数据提供了更详细的市场微观结构信息，用于高频交易和精细化分析
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

def test_l2_orders():
    """
    测试L2订单簿数据
    """
    print("\n=== 测试 get_history_l2orders 函数 - 获取L2订单簿数据 ===")
    
    test_results = []
    
    # 活跃股票列表
    active_stocks = [
        'SHSE.600519',  # 贵州茅台
        'SHSE.600036',  # 招商银行
        'SZSE.000858',  # 五粮液
        'SZSE.300750',  # 宁德时代
        'SHSE.600000'   # 浦发银行
    ]
    
    try:
        # 获取最近的交易日
        end_time = datetime.now()
        start_time = end_time - timedelta(days=1)
        
        # 格式化时间
        start_time_str = start_time.strftime('%Y-%m-%d 09:30:00')
        end_time_str = start_time.strftime('%Y-%m-%d 10:00:00')  # 获取30分钟的数据
        
        for symbol in active_stocks[:3]:  # 测试前3只股票
            print(f"\n查询 {symbol} 的L2订单簿数据...")
            
            try:
                result = get_history_l2orders(
                    symbols=symbol,
                    start_time=start_time_str,
                    end_time=end_time_str
                )
                
                if result:
                    print(f"  ✓ {symbol}: 成功获取 {len(result)} 条L2订单数据")
                    
                    # 转换为DataFrame
                    df = pd.DataFrame(result)
                    
                    # 显示数据概览
                    print(f"  数据时间范围: {df['created_at'].min()} 到 {df['created_at'].max()}")
                    
                    # 分析订单类型
                    if 'side' in df.columns:
                        side_counts = df['side'].value_counts()
                        print(f"  买单数量: {side_counts.get(1, 0)}")
                        print(f"  卖单数量: {side_counts.get(2, 0)}")
                    
                    # 分析价格分布
                    if 'price' in df.columns:
                        print(f"  价格范围: {df['price'].min():.2f} - {df['price'].max():.2f}")
                        print(f"  平均价格: {df['price'].mean():.2f}")
                    
                    # 分析订单量
                    if 'volume' in df.columns:
                        print(f"  订单量范围: {df['volume'].min()} - {df['volume'].max()}")
                        print(f"  总订单量: {df['volume'].sum():,}")
                    
                    # 保存数据
                    csv_filename = f"l2_orders_{symbol.replace('.', '_')}_{start_time.strftime('%Y%m%d')}.csv"
                    df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
                    print(f"  ✓ 数据已保存到 {csv_filename}")
                    
                    # 分析订单簿深度
                    analyze_order_book_depth(df, symbol)
                    
                    test_result = {
                        'symbol': symbol,
                        'function': 'get_history_l2orders',
                        'status': 'success',
                        'data_count': len(result),
                        'time_range': f"{start_time_str} - {end_time_str}",
                        'sample_data': result[:3]
                    }
                else:
                    print(f"  ✗ {symbol}: 无L2订单数据")
                    test_result = {
                        'symbol': symbol,
                        'function': 'get_history_l2orders',
                        'status': 'no_data',
                        'time_range': f"{start_time_str} - {end_time_str}"
                    }
                    
            except Exception as e:
                print(f"  ✗ {symbol}: 错误 - {e}")
                test_result = {
                    'symbol': symbol,
                    'function': 'get_history_l2orders',
                    'status': 'error',
                    'error': str(e)
                }
            
            test_results.append(test_result)
            
    except Exception as e:
        print(f"✗ L2订单簿数据查询错误: {e}")
        test_results.append({
            'function': 'get_history_l2orders',
            'status': 'error',
            'error': str(e)
        })
    
    return test_results

def analyze_order_book_depth(df, symbol):
    """
    分析订单簿深度
    """
    print(f"\n  === {symbol} 订单簿深度分析 ===")
    
    try:
        if df.empty:
            print("  无数据可分析")
            return
        
        # 按价格和方向分组统计
        if 'price' in df.columns and 'side' in df.columns and 'volume' in df.columns:
            # 买单（side=1）和卖单（side=2）分别统计
            buy_orders = df[df['side'] == 1]
            sell_orders = df[df['side'] == 2]
            
            if not buy_orders.empty:
                buy_depth = buy_orders.groupby('price')['volume'].sum().sort_index(ascending=False)
                print(f"  买单深度 (前5档):")
                for price, volume in buy_depth.head(5).items():
                    print(f"    {price:.2f}: {volume:,} 股")
            
            if not sell_orders.empty:
                sell_depth = sell_orders.groupby('price')['volume'].sum().sort_index()
                print(f"  卖单深度 (前5档):")
                for price, volume in sell_depth.head(5).items():
                    print(f"    {price:.2f}: {volume:,} 股")
        
        # 计算买卖压力
        if 'side' in df.columns and 'volume' in df.columns:
            total_buy_volume = df[df['side'] == 1]['volume'].sum()
            total_sell_volume = df[df['side'] == 2]['volume'].sum()
            
            print(f"  总买单量: {total_buy_volume:,} 股")
            print(f"  总卖单量: {total_sell_volume:,} 股")
            
            if total_sell_volume > 0:
                buy_sell_ratio = total_buy_volume / total_sell_volume
                print(f"  买卖比: {buy_sell_ratio:.2f}")
        
    except Exception as e:
        print(f"  ✗ 订单簿深度分析错误: {e}")

def test_l2_transactions():
    """
    测试L2成交明细数据
    """
    print("\n=== 测试 get_history_l2transactions 函数 - 获取L2成交明细数据 ===")
    
    test_results = []
    
    # 活跃股票列表
    active_stocks = [
        'SHSE.600519',  # 贵州茅台
        'SHSE.600036',  # 招商银行
        'SZSE.000858'   # 五粮液
    ]
    
    try:
        # 获取最近的交易日
        end_time = datetime.now()
        start_time = end_time - timedelta(days=1)
        
        # 格式化时间
        start_time_str = start_time.strftime('%Y-%m-%d 09:30:00')
        end_time_str = start_time.strftime('%Y-%m-%d 10:00:00')  # 获取30分钟的数据
        
        for symbol in active_stocks:
            print(f"\n查询 {symbol} 的L2成交明细数据...")
            
            try:
                result = get_history_l2transactions(
                    symbols=symbol,
                    start_time=start_time_str,
                    end_time=end_time_str
                )
                
                if result:
                    print(f"  ✓ {symbol}: 成功获取 {len(result)} 条L2成交数据")
                    
                    # 转换为DataFrame
                    df = pd.DataFrame(result)
                    
                    # 显示数据概览
                    print(f"  数据时间范围: {df['created_at'].min()} 到 {df['created_at'].max()}")
                    
                    # 分析成交数据
                    if 'price' in df.columns:
                        print(f"  成交价格范围: {df['price'].min():.2f} - {df['price'].max():.2f}")
                        print(f"  平均成交价: {df['price'].mean():.2f}")
                    
                    if 'volume' in df.columns:
                        print(f"  成交量范围: {df['volume'].min()} - {df['volume'].max()}")
                        print(f"  总成交量: {df['volume'].sum():,}")
                    
                    if 'amount' in df.columns:
                        print(f"  总成交额: {df['amount'].sum():,.2f}")
                    
                    # 分析成交方向
                    if 'side' in df.columns:
                        side_counts = df['side'].value_counts()
                        print(f"  主动买入成交: {side_counts.get(1, 0)} 笔")
                        print(f"  主动卖出成交: {side_counts.get(2, 0)} 笔")
                    
                    # 保存数据
                    csv_filename = f"l2_transactions_{symbol.replace('.', '_')}_{start_time.strftime('%Y%m%d')}.csv"
                    df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
                    print(f"  ✓ 数据已保存到 {csv_filename}")
                    
                    # 分析成交分布
                    analyze_transaction_distribution(df, symbol)
                    
                    test_result = {
                        'symbol': symbol,
                        'function': 'get_history_l2transactions',
                        'status': 'success',
                        'data_count': len(result),
                        'time_range': f"{start_time_str} - {end_time_str}",
                        'sample_data': result[:3]
                    }
                else:
                    print(f"  ✗ {symbol}: 无L2成交数据")
                    test_result = {
                        'symbol': symbol,
                        'function': 'get_history_l2transactions',
                        'status': 'no_data',
                        'time_range': f"{start_time_str} - {end_time_str}"
                    }
                    
            except Exception as e:
                print(f"  ✗ {symbol}: 错误 - {e}")
                test_result = {
                    'symbol': symbol,
                    'function': 'get_history_l2transactions',
                    'status': 'error',
                    'error': str(e)
                }
            
            test_results.append(test_result)
            
    except Exception as e:
        print(f"✗ L2成交明细数据查询错误: {e}")
        test_results.append({
            'function': 'get_history_l2transactions',
            'status': 'error',
            'error': str(e)
        })
    
    return test_results

def analyze_transaction_distribution(df, symbol):
    """
    分析成交分布
    """
    print(f"\n  === {symbol} 成交分布分析 ===")
    
    try:
        if df.empty:
            print("  无数据可分析")
            return
        
        # 按时间分析成交分布
        if 'created_at' in df.columns:
            df['minute'] = pd.to_datetime(df['created_at']).dt.strftime('%H:%M')
            minute_volume = df.groupby('minute')['volume'].sum()
            
            print(f"  成交最活跃的5分钟:")
            top_minutes = minute_volume.nlargest(5)
            for minute, volume in top_minutes.items():
                print(f"    {minute}: {volume:,} 股")
        
        # 按成交量大小分析
        if 'volume' in df.columns:
            # 大单、中单、小单分类（这里用简单的阈值分类）
            large_trades = df[df['volume'] >= 10000]  # 大于等于1万股
            medium_trades = df[(df['volume'] >= 1000) & (df['volume'] < 10000)]  # 1千到1万股
            small_trades = df[df['volume'] < 1000]  # 小于1千股
            
            print(f"  大单成交: {len(large_trades)} 笔, 总量: {large_trades['volume'].sum():,} 股")
            print(f"  中单成交: {len(medium_trades)} 笔, 总量: {medium_trades['volume'].sum():,} 股")
            print(f"  小单成交: {len(small_trades)} 笔, 总量: {small_trades['volume'].sum():,} 股")
        
        # 价格波动分析
        if 'price' in df.columns:
            price_std = df['price'].std()
            price_range = df['price'].max() - df['price'].min()
            print(f"  价格波动标准差: {price_std:.4f}")
            print(f"  价格波动幅度: {price_range:.4f}")
        
    except Exception as e:
        print(f"  ✗ 成交分布分析错误: {e}")

def test_l2_ticks_detailed():
    """
    测试详细的L2 Tick数据
    """
    print("\n=== 测试 get_history_l2ticks 函数 - 获取详细L2 Tick数据 ===")
    
    test_results = []
    
    # 选择代表性股票
    test_symbols = ['SHSE.600519', 'SHSE.600036']
    
    try:
        # 获取最近的交易日
        end_time = datetime.now()
        start_time = end_time - timedelta(days=1)
        
        # 格式化时间
        start_time_str = start_time.strftime('%Y-%m-%d 09:30:00')
        end_time_str = start_time.strftime('%Y-%m-%d 09:45:00')  # 获取15分钟的数据
        
        for symbol in test_symbols:
            print(f"\n查询 {symbol} 的详细L2 Tick数据...")
            
            try:
                result = get_history_l2ticks(
                    symbols=symbol,
                    start_time=start_time_str,
                    end_time=end_time_str
                )
                
                if result:
                    print(f"  ✓ {symbol}: 成功获取 {len(result)} 条L2 Tick数据")
                    
                    # 转换为DataFrame
                    df = pd.DataFrame(result)
                    
                    # 显示数据概览
                    print(f"  数据时间范围: {df['created_at'].min()} 到 {df['created_at'].max()}")
                    
                    # 分析Tick数据
                    analyze_l2_tick_data(df, symbol)
                    
                    # 保存数据
                    csv_filename = f"l2_ticks_{symbol.replace('.', '_')}_{start_time.strftime('%Y%m%d')}.csv"
                    df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
                    print(f"  ✓ 数据已保存到 {csv_filename}")
                    
                    test_result = {
                        'symbol': symbol,
                        'function': 'get_history_l2ticks',
                        'status': 'success',
                        'data_count': len(result),
                        'time_range': f"{start_time_str} - {end_time_str}",
                        'sample_data': result[:3]
                    }
                else:
                    print(f"  ✗ {symbol}: 无L2 Tick数据")
                    test_result = {
                        'symbol': symbol,
                        'function': 'get_history_l2ticks',
                        'status': 'no_data',
                        'time_range': f"{start_time_str} - {end_time_str}"
                    }
                    
            except Exception as e:
                print(f"  ✗ {symbol}: 错误 - {e}")
                test_result = {
                    'symbol': symbol,
                    'function': 'get_history_l2ticks',
                    'status': 'error',
                    'error': str(e)
                }
            
            test_results.append(test_result)
            
    except Exception as e:
        print(f"✗ L2 Tick数据查询错误: {e}")
        test_results.append({
            'function': 'get_history_l2ticks',
            'status': 'error',
            'error': str(e)
        })
    
    return test_results

def analyze_l2_tick_data(df, symbol):
    """
    分析L2 Tick数据
    """
    print(f"\n  === {symbol} L2 Tick数据分析 ===")
    
    try:
        if df.empty:
            print("  无数据可分析")
            return
        
        # 分析买卖档位
        bid_columns = [col for col in df.columns if col.startswith('bid_p') or col.startswith('bid_v')]
        ask_columns = [col for col in df.columns if col.startswith('ask_p') or col.startswith('ask_v')]
        
        print(f"  买盘档位数: {len([col for col in bid_columns if 'bid_p' in col])}")
        print(f"  卖盘档位数: {len([col for col in ask_columns if 'ask_p' in col])}")
        
        # 分析最新价格
        if 'price' in df.columns:
            print(f"  价格范围: {df['price'].min():.2f} - {df['price'].max():.2f}")
            print(f"  价格变化次数: {(df['price'].diff() != 0).sum()}")
        
        # 分析成交量
        if 'volume' in df.columns:
            print(f"  累计成交量: {df['volume'].iloc[-1]:,} 股" if not df.empty else "无成交量数据")
        
        # 分析买卖价差
        if 'bid_p1' in df.columns and 'ask_p1' in df.columns:
            df['spread'] = df['ask_p1'] - df['bid_p1']
            avg_spread = df['spread'].mean()
            print(f"  平均买卖价差: {avg_spread:.4f}")
        
        # 分析流动性
        if 'bid_v1' in df.columns and 'ask_v1' in df.columns:
            avg_bid_volume = df['bid_v1'].mean()
            avg_ask_volume = df['ask_v1'].mean()
            print(f"  一档买盘平均量: {avg_bid_volume:,.0f} 股")
            print(f"  一档卖盘平均量: {avg_ask_volume:,.0f} 股")
        
    except Exception as e:
        print(f"  ✗ L2 Tick数据分析错误: {e}")

def test_market_depth_summary():
    """
    市场深度数据综合分析
    """
    print("\n=== 市场深度数据综合分析 ===")
    
    test_results = []
    
    try:
        # 选择几只代表性股票进行综合分析
        analysis_symbols = ['SHSE.600519', 'SHSE.600036']
        
        summary_data = []
        
        for symbol in analysis_symbols:
            print(f"\n综合分析 {symbol} 的市场深度...")
            
            symbol_summary = {
                'symbol': symbol,
                'l2_orders_available': False,
                'l2_transactions_available': False,
                'l2_ticks_available': False,
                'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 检查各类数据的可用性
            try:
                end_time = datetime.now()
                start_time = end_time - timedelta(days=1)
                start_time_str = start_time.strftime('%Y-%m-%d 09:30:00')
                end_time_str = start_time.strftime('%Y-%m-%d 09:35:00')
                
                # 检查L2订单数据
                try:
                    orders = get_history_l2orders(symbol=symbol, start_time=start_time_str, end_time=end_time_str)
                    if orders:
                        symbol_summary['l2_orders_available'] = True
                        symbol_summary['l2_orders_count'] = len(orders)
                except:
                    pass
                
                # 检查L2成交数据
                try:
                    transactions = get_history_l2transactions(symbol=symbol, start_time=start_time_str, end_time=end_time_str)
                    if transactions:
                        symbol_summary['l2_transactions_available'] = True
                        symbol_summary['l2_transactions_count'] = len(transactions)
                except:
                    pass
                
                # 检查L2 Tick数据
                try:
                    ticks = get_history_l2ticks(symbol=symbol, start_time=start_time_str, end_time=end_time_str)
                    if ticks:
                        symbol_summary['l2_ticks_available'] = True
                        symbol_summary['l2_ticks_count'] = len(ticks)
                except:
                    pass
                
            except Exception as e:
                symbol_summary['error'] = str(e)
            
            summary_data.append(symbol_summary)
            
            # 显示可用性报告
            print(f"  L2订单数据: {'✓' if symbol_summary['l2_orders_available'] else '✗'}")
            print(f"  L2成交数据: {'✓' if symbol_summary['l2_transactions_available'] else '✗'}")
            print(f"  L2 Tick数据: {'✓' if symbol_summary['l2_ticks_available'] else '✗'}")
        
        # 生成综合报告
        if summary_data:
            generate_market_depth_report(summary_data)
            
            test_result = {
                'test_name': '市场深度数据综合分析',
                'function': 'market_depth_summary',
                'status': 'success',
                'symbols_analyzed': len(summary_data),
                'summary_data': summary_data
            }
        else:
            test_result = {
                'test_name': '市场深度数据综合分析',
                'function': 'market_depth_summary',
                'status': 'no_data'
            }
            
    except Exception as e:
        print(f"✗ 市场深度综合分析错误: {e}")
        test_result = {
            'test_name': '市场深度数据综合分析',
            'function': 'market_depth_summary',
            'status': 'error',
            'error': str(e)
        }
    
    test_results.append(test_result)
    return test_results

def generate_market_depth_report(summary_data):
    """
    生成市场深度报告
    """
    print("\n=== 市场深度数据可用性报告 ===")
    
    try:
        total_symbols = len(summary_data)
        l2_orders_available = sum(1 for data in summary_data if data.get('l2_orders_available', False))
        l2_transactions_available = sum(1 for data in summary_data if data.get('l2_transactions_available', False))
        l2_ticks_available = sum(1 for data in summary_data if data.get('l2_ticks_available', False))
        
        print(f"分析股票数量: {total_symbols}")
        print(f"L2订单数据可用: {l2_orders_available}/{total_symbols} ({l2_orders_available/total_symbols*100:.1f}%)")
        print(f"L2成交数据可用: {l2_transactions_available}/{total_symbols} ({l2_transactions_available/total_symbols*100:.1f}%)")
        print(f"L2 Tick数据可用: {l2_ticks_available}/{total_symbols} ({l2_ticks_available/total_symbols*100:.1f}%)")
        
        # 详细报告
        print("\n详细可用性:")
        for data in summary_data:
            symbol = data['symbol']
            orders = '✓' if data.get('l2_orders_available', False) else '✗'
            transactions = '✓' if data.get('l2_transactions_available', False) else '✗'
            ticks = '✓' if data.get('l2_ticks_available', False) else '✗'
            print(f"  {symbol}: 订单{orders} 成交{transactions} Tick{ticks}")
        
        # 保存报告
        report_df = pd.DataFrame(summary_data)
        report_df.to_csv('market_depth_availability_report.csv', index=False, encoding='utf-8-sig')
        print("\n✓ 市场深度可用性报告已保存到 market_depth_availability_report.csv")
        
    except Exception as e:
        print(f"✗ 生成市场深度报告错误: {e}")

def main():
    """
    主函数
    """
    print("开始测试GM SDK 市场深度数据查询功能...")
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
        # 测试L2订单簿数据
        l2_orders_results = test_l2_orders()
        all_results['tests']['l2_orders'] = l2_orders_results
        
        # 测试L2成交明细数据
        l2_transactions_results = test_l2_transactions()
        all_results['tests']['l2_transactions'] = l2_transactions_results
        
        # 测试详细L2 Tick数据
        l2_ticks_results = test_l2_ticks_detailed()
        all_results['tests']['l2_ticks'] = l2_ticks_results
        
        # 市场深度综合分析
        market_depth_summary_results = test_market_depth_summary()
        all_results['tests']['market_depth_summary'] = market_depth_summary_results
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        all_results['error'] = str(e)
    
    # 保存测试结果
    with open('market_depth_test_results.json', 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2, default=str)
    
    print("\n=== 测试总结 ===")
    print(f"测试时间: {all_results['test_time']}")
    
    if 'tests' in all_results:
        for test_type, results in all_results['tests'].items():
            if isinstance(results, list):
                total_tests = len(results)
                successful_tests = sum(1 for result in results if result.get('status') == 'success')
                print(f"{test_type}测试: {successful_tests}/{total_tests} 成功")
    
    print("\n✓ 测试结果已保存到 market_depth_test_results.json")
    print("✓ CSV数据文件已保存到当前目录")
    print("\n市场深度数据说明:")
    print("- L2订单数据: 提供完整的买卖订单簿信息")
    print("- L2成交数据: 提供详细的逐笔成交信息")
    print("- L2 Tick数据: 提供实时的五档行情快照")
    print("- 数据频率: 通常为毫秒级或秒级更新")
    print("- 适用场景: 高频交易、算法交易、市场微观结构分析")

if __name__ == '__main__':
    main()