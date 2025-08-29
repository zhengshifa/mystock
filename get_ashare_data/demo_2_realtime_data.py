#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
掘金量化 GM SDK - 1分钟前历史数据测试Demo
测试获取1分钟前的历史数据，非交易时间自动跳过
"""

import json
import pandas as pd
import os
from datetime import datetime, timedelta
from gm.api import *

def is_trading_time():
    """检查当前是否为交易时间"""
    now = datetime.now()
    current_time = now.time()
    weekday = now.weekday()  # 0=Monday, 6=Sunday
    
    # 检查是否为工作日（周一到周五）
    if weekday >= 5:  # 周六、周日
        return False
    
    # 检查是否在交易时间内
    # 上午：9:30-11:30
    # 下午：13:00-15:00
    morning_start = datetime.strptime('09:30', '%H:%M').time()
    morning_end = datetime.strptime('11:30', '%H:%M').time()
    afternoon_start = datetime.strptime('13:00', '%H:%M').time()
    afternoon_end = datetime.strptime('15:00', '%H:%M').time()
    
    is_morning = morning_start <= current_time <= morning_end
    is_afternoon = afternoon_start <= current_time <= afternoon_end
    
    return is_morning or is_afternoon

def test_current_kline_data():
    """测试获取当前时间的K线数据"""
    print("=" * 60)
    print("当前时间K线数据测试Demo")
    print("=" * 60)
    
    # 检查交易时间
    if not is_trading_time():
        print("当前非交易时间，跳过数据获取")
        print(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("交易时间: 周一至周五 09:30-11:30, 13:00-15:00")
        return {'status': 'skipped', 'reason': '非交易时间'}
    
    results = {}
    
    # 计算1分钟前的时间
    now = datetime.now()
    one_min_ago = now - timedelta(minutes=1)
    
    # 测试股票代码
    test_symbols = [
        'SHSE.000001',  # 上证指数
        'SHSE.600111',
    ]
    
    print(f"当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"目标时间: {one_min_ago.strftime('%Y-%m-%d %H:%M:%S')} (1分钟前)")
    print(f"测试标的: {test_symbols}")
    
    # 1. 测试获取1分钟前的K线数据
    print("\n" + "=" * 40)
    print("1. 测试获取当前时间的K线数据")
    print("=" * 40)
    
    history_results = {}
    
    # 测试单个标的
    print("\n1.1 测试单个标的当前K线数据")
    for symbol in test_symbols:
        try:
            print(f"\n获取 {symbol} 当前时间的K线数据...")
            
            # 获取最近的1分钟K线数据（当前时间的数据）
            kline_data = history_n(symbol=symbol, 
                                 frequency='1m', 
                                 count=3,
                                 fields='open,high,low,close,volume,amount',
                                 df=True)
            
            if kline_data is not None and not kline_data.empty:
                # 获取最新一条K线数据（当前时间的数据）
                last_bar = kline_data.iloc[-1]
                time_index = kline_data.index[-1] if len(kline_data.index) > 0 else 'N/A'
                
                history_results[symbol] = {
                    'symbol': symbol,
                    'time': str(time_index),
                    'open': float(last_bar['open']) if 'open' in last_bar else 'N/A',
                    'high': float(last_bar['high']) if 'high' in last_bar else 'N/A',
                    'low': float(last_bar['low']) if 'low' in last_bar else 'N/A',
                    'close': float(last_bar['close']) if 'close' in last_bar else 'N/A',
                    'volume': float(last_bar['volume']) if 'volume' in last_bar else 'N/A',
                    'amount': float(last_bar['amount']) if 'amount' in last_bar else 'N/A',
                    'total_bars': len(kline_data),
                    'data_quality': 'complete' if len(kline_data) > 0 else 'incomplete'
                }
                
                print(f"    ✓ 时间: {time_index}")
                print(f"    ✓ 开盘价: {last_bar['open'] if 'open' in last_bar else 'N/A'}")
                print(f"    ✓ 收盘价: {last_bar['close'] if 'close' in last_bar else 'N/A'}")
                print(f"    ✓ 成交量: {last_bar['volume'] if 'volume' in last_bar else 'N/A'}")
                print(f"    ✓ 成交额: {last_bar['amount'] if 'amount' in last_bar else 'N/A'}")
                print(f"    ✓ 获取到 {len(kline_data)} 根K线数据")
            else:
                history_results[symbol] = {'error': '无K线数据返回'}
                print(f"    ✗ 无K线数据返回")
                
        except Exception as e:
            history_results[symbol] = {'error': str(e)}
            print(f"    ✗ 错误: {e}")
    
    results['history_1min_test'] = history_results
    
    # 测试批量获取最近的K线数据
    print("\n1.2 测试批量获取最近K线数据")
    try:
        print(f"\n批量获取多个标的最近K线数据...")
        batch_symbols = test_symbols[:4]  # 取前4个
        batch_results = {}
        
        for symbol in batch_symbols:
            try:
                # 获取最近的1分钟K线数据（最近10根）
                recent_data = history_n(symbol=symbol, 
                                       frequency='1m', 
                                       count=10,
                                       fields='open,high,low,close,volume,amount',
                                       df=True)
                
                if recent_data is not None and not recent_data.empty:
                    latest_bar = recent_data.iloc[-1]
                    latest_time = recent_data.index[-1] if len(recent_data.index) > 0 else 'N/A'
                    
                    batch_results[symbol] = {
                        'time': str(latest_time),
                        'close': float(latest_bar['close']) if 'close' in latest_bar else 'N/A',
                        'volume': float(latest_bar['volume']) if 'volume' in latest_bar else 'N/A',
                        'amount': float(latest_bar['amount']) if 'amount' in latest_bar else 'N/A',
                        'bars_count': len(recent_data)
                    }
                    print(f"    ✓ {symbol}: 收盘价={latest_bar['close'] if 'close' in latest_bar else 'N/A'}, 成交量={latest_bar['volume'] if 'volume' in latest_bar else 'N/A'}")
                else:
                    batch_results[symbol] = {'error': '无数据'}
                    print(f"    ✗ {symbol}: 无数据")
            except Exception as e:
                batch_results[symbol] = {'error': str(e)}
                print(f"    ✗ {symbol}: 错误 - {e}")
        
        results['history_batch_test'] = {
            'requested_symbols': batch_symbols,
            'successful_count': len([r for r in batch_results.values() if 'error' not in r]),
            'data': batch_results
        }
            
    except Exception as e:
        results['history_batch_test'] = {'error': str(e)}
        print(f"    ✗ 批量获取错误: {e}")
    
    # 2. 测试获取5分钟K线数据对比
    print("\n" + "=" * 40)
    print("2. 测试获取5分钟K线数据对比")
    print("=" * 40)
    
    kline_5m_results = {}
    
    # 测试5分钟K线数据
    print("\n2.1 测试5分钟K线数据")
    for symbol in test_symbols[:3]:  # 测试前3个
        try:
            print(f"\n获取 {symbol} 的5分钟K线数据...")
            
            # 获取最近的5分钟K线数据
            kline_5m_data = history_n(symbol=symbol, 
                                     frequency='5m', 
                                     count=5,
                                     fields='open,high,low,close,volume,amount',
                                     df=True)
            
            if kline_5m_data is not None and not kline_5m_data.empty:
                latest_bar = kline_5m_data.iloc[-1]
                latest_time = kline_5m_data.index[-1] if len(kline_5m_data.index) > 0 else 'N/A'
                
                kline_5m_results[symbol] = {
                    'symbol': symbol,
                    'time': str(latest_time),
                    'open': float(latest_bar['open']) if 'open' in latest_bar else 'N/A',
                    'high': float(latest_bar['high']) if 'high' in latest_bar else 'N/A',
                    'low': float(latest_bar['low']) if 'low' in latest_bar else 'N/A',
                    'close': float(latest_bar['close']) if 'close' in latest_bar else 'N/A',
                    'volume': float(latest_bar['volume']) if 'volume' in latest_bar else 'N/A',
                    'amount': float(latest_bar['amount']) if 'amount' in latest_bar else 'N/A',
                    'total_bars': len(kline_5m_data)
                }
                
                print(f"    ✓ 时间: {latest_time}")
                print(f"    ✓ 开盘价: {latest_bar['open'] if 'open' in latest_bar else 'N/A'}")
                print(f"    ✓ 收盘价: {latest_bar['close'] if 'close' in latest_bar else 'N/A'}")
                print(f"    ✓ 最高价: {latest_bar['high'] if 'high' in latest_bar else 'N/A'}")
                print(f"    ✓ 最低价: {latest_bar['low'] if 'low' in latest_bar else 'N/A'}")
                
            else:
                kline_5m_results[symbol] = {'error': '无5分钟K线数据返回'}
                print(f"    ✗ 无5分钟K线数据返回")
                
        except Exception as e:
            kline_5m_results[symbol] = {'error': str(e)}
            print(f"    ✗ 错误: {e}")
    
    results['kline_5m_test'] = kline_5m_results
    
    # 3. 测试不同频率的K线数据
    print("\n" + "=" * 40)
    print("3. 测试不同频率的K线数据")
    print("=" * 40)
    
    frequency_test_results = {}
    test_symbol = 'SHSE.600036'  # 招商银行
    
    frequencies = ['1m', '5m', '15m', '30m']
    
    for freq in frequencies:
        try:
            print(f"\n测试 {freq} 频率K线数据...")
            
            freq_data = history_n(symbol=test_symbol, 
                                 frequency=freq, 
                                 count=3,
                                 fields='open,high,low,close,volume,amount',
                                 df=True)
            
            if freq_data is not None and not freq_data.empty:
                latest_bar = freq_data.iloc[-1]
                latest_time = freq_data.index[-1] if len(freq_data.index) > 0 else 'N/A'
                
                frequency_test_results[freq] = {
                    'frequency': freq,
                    'time': str(latest_time),
                    'open': float(latest_bar['open']) if 'open' in latest_bar else 'N/A',
                    'close': float(latest_bar['close']) if 'close' in latest_bar else 'N/A',
                    'volume': float(latest_bar['volume']) if 'volume' in latest_bar else 'N/A',
                    'bars_count': len(freq_data)
                }
                print(f"    ✓ {freq} 数据: 时间={latest_time}, 收盘价={latest_bar['close'] if 'close' in latest_bar else 'N/A'}")
            else:
                frequency_test_results[freq] = {'error': f'无{freq}数据返回'}
                print(f"    ✗ 无{freq}数据返回")
                
        except Exception as e:
            frequency_test_results[freq] = {'error': str(e)}
            print(f"    ✗ {freq}数据错误: {e}")
    
    results['frequency_test'] = frequency_test_results
    
    # 保存测试结果
    with open('demo_2_1min_ago_data_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    
    # 保存历史数据快照到CSV
    if 'history_1min_test' in results:
        df_data = []
        for symbol, data in results['history_1min_test'].items():
            if 'error' not in data:
                row = {'symbol': symbol}
                row.update(data)
                df_data.append(row)
        
        if df_data:
            df = pd.DataFrame(df_data)
            df.to_csv('1min_ago_snapshot.csv', index=False, encoding='utf-8-sig')
            print(f"\n1分钟前数据快照已保存到: 1min_ago_snapshot.csv")
    
    print("\n" + "=" * 60)
    print("当前时间K线数据测试完成！")
    print("详细结果已保存到: demo_2_1min_ago_data_results.json")
    print("=" * 60)
    
    return results

def configure_token():
    """
    配置GM SDK的token
    支持多种配置方式：
    1. 直接设置token
    2. 从配置文件读取
    3. 从环境变量读取
    """
    
    # 方法1: 直接设置token（不推荐，仅用于测试）
    # set_token('your_token_here')
    
    # 方法2: 从配置文件读取（推荐）
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
    
    # 方法3: 从环境变量读取
    token = os.getenv('GM_TOKEN')
    if token:
        set_token(token)
        print("已从环境变量 GM_TOKEN 读取token")
        return True
    
    print("警告: 未找到有效的token配置")
    print("请通过以下方式之一配置token:")
    print("1. 创建 gm_config.json 文件并设置token")
    print("2. 设置环境变量 GM_TOKEN")
    print("3. 在代码中直接调用 set_token('your_token')")
    return False

if __name__ == "__main__":
    try:
        # 配置token
        if not configure_token():
            print("\n请先配置有效的token后再运行测试")
            exit(1)
        
        # 测试token有效性
        try:
            test_dates = get_trading_dates('SHSE', '2024-01-01', '2024-01-05')
            if not test_dates:
                print("Token验证失败，请检查token是否有效")
                exit(1)
            print("Token验证成功")
        except Exception as e:
            print(f"Token验证失败: {e}")
            exit(1)
        
        # 运行测试
        test_results = test_current_kline_data()
        
        # 打印总结
        if test_results.get('status') == 'skipped':
            print(f"\n测试跳过: {test_results.get('reason', '未知原因')}")
        else:
            print("\n测试总结:")
            
            if 'history_1min_test' in test_results:
                total_1min = len(test_results['history_1min_test'])
                successful_1min = sum(1 for data in test_results['history_1min_test'].values() if 'error' not in data)
                print(f"1分钟K线数据测试: {successful_1min}/{total_1min} 成功")
            
            if 'kline_5m_test' in test_results:
                total_5m = len(test_results['kline_5m_test'])
                successful_5m = sum(1 for data in test_results['kline_5m_test'].values() if 'error' not in data)
                print(f"5分钟K线数据测试: {successful_5m}/{total_5m} 成功")
            
            if 'history_batch_test' in test_results:
                batch_success = test_results['history_batch_test'].get('successful_count', 0)
                batch_total = len(test_results['history_batch_test'].get('requested_symbols', []))
                print(f"批量K线数据测试: {batch_success}/{batch_total} 成功")
            
            if 'frequency_test' in test_results:
                freq_total = len(test_results['frequency_test'])
                freq_success = sum(1 for data in test_results['frequency_test'].values() if 'error' not in data)
                print(f"不同频率K线测试: {freq_success}/{freq_total} 成功")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()