#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
掘金量化 GM SDK 技术指标计算测试demo

本demo基于历史行情数据计算常见技术指标：
1. 移动平均线 (SMA, EMA)
2. MACD (指数平滑异同移动平均线)
3. RSI (相对强弱指标)
4. 布林带 (Bollinger Bands)
5. KDJ 随机指标
6. 成交量指标 (OBV, VWAP)

注意：运行前需要配置有效的token
"""

import gm
from gm.api import *
import json
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

# ============================================================
# Token配置 - 请在运行前配置有效的token
# ============================================================

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

# ============================================================
# 技术指标计算函数
# ============================================================

def calculate_sma(data, window):
    """计算简单移动平均线"""
    return data.rolling(window=window).mean()

def calculate_ema(data, window):
    """计算指数移动平均线"""
    return data.ewm(span=window).mean()

def calculate_macd(data, fast=12, slow=26, signal=9):
    """计算MACD指标"""
    ema_fast = calculate_ema(data, fast)
    ema_slow = calculate_ema(data, slow)
    macd_line = ema_fast - ema_slow
    signal_line = calculate_ema(macd_line, signal)
    histogram = macd_line - signal_line
    
    return {
        'macd': macd_line,
        'signal': signal_line,
        'histogram': histogram
    }

def calculate_rsi(data, window=14):
    """计算RSI相对强弱指标"""
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_bollinger_bands(data, window=20, num_std=2):
    """计算布林带"""
    sma = calculate_sma(data, window)
    std = data.rolling(window=window).std()
    upper_band = sma + (std * num_std)
    lower_band = sma - (std * num_std)
    
    return {
        'upper': upper_band,
        'middle': sma,
        'lower': lower_band
    }

def calculate_kdj(high, low, close, window=9, k_period=3, d_period=3):
    """计算KDJ随机指标"""
    lowest_low = low.rolling(window=window).min()
    highest_high = high.rolling(window=window).max()
    
    rsv = (close - lowest_low) / (highest_high - lowest_low) * 100
    k = rsv.ewm(span=k_period).mean()
    d = k.ewm(span=d_period).mean()
    j = 3 * k - 2 * d
    
    return {
        'k': k,
        'd': d,
        'j': j
    }

def calculate_obv(close, volume):
    """计算OBV能量潮指标"""
    obv = [0]
    for i in range(1, len(close)):
        if close.iloc[i] > close.iloc[i-1]:
            obv.append(obv[-1] + volume.iloc[i])
        elif close.iloc[i] < close.iloc[i-1]:
            obv.append(obv[-1] - volume.iloc[i])
        else:
            obv.append(obv[-1])
    return pd.Series(obv, index=close.index)

def calculate_vwap(high, low, close, volume):
    """计算VWAP成交量加权平均价格"""
    typical_price = (high + low + close) / 3
    vwap = (typical_price * volume).cumsum() / volume.cumsum()
    return vwap

def test_technical_indicators():
    """
    测试技术指标计算
    """
    results = {
        'test_info': {
            'test_name': '技术指标计算测试',
            'test_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'description': '基于历史行情数据计算常见技术指标'
        },
        'tests': []
    }
    
    # 测试股票列表
    test_symbols = [
        'SHSE.000001',  # 上证指数
        'SZSE.399001',  # 深证成指
        'SHSE.600000',  # 浦发银行
        'SZSE.000001',  # 平安银行
        'SHSE.600036'   # 招商银行
    ]
    
    # 获取历史数据时间范围
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    
    print(f"数据时间范围: {start_date} 到 {end_date}")
    
    for symbol in test_symbols:
        print(f"\n=== 处理股票: {symbol} ===")
        
        try:
            # 获取历史数据
            print(f"获取 {symbol} 的历史数据...")
            hist_data = history(
                symbol=symbol,
                frequency='1d',
                start_time=start_date,
                end_time=end_date,
                fields='symbol,eob,open,high,low,close,volume,amount',
                skip_suspended=True,
                fill_missing='Previous',
                adjust=1,  # 前复权
                df=True
            )
            
            if hist_data is None or hist_data.empty:
                print(f"  ⚠ {symbol} 无历史数据")
                continue
                
            print(f"  ✓ 获取到 {len(hist_data)} 条历史数据")
            
            # 确保数据按时间排序
            hist_data = hist_data.sort_values('eob')
            hist_data.reset_index(drop=True, inplace=True)
            
            # 提取价格和成交量数据
            close = hist_data['close']
            high = hist_data['high']
            low = hist_data['low']
            volume = hist_data['volume']
            
            # 计算各种技术指标
            indicators = {}
            
            # 1. 移动平均线
            print("  计算移动平均线...")
            indicators['sma_5'] = calculate_sma(close, 5)
            indicators['sma_10'] = calculate_sma(close, 10)
            indicators['sma_20'] = calculate_sma(close, 20)
            indicators['sma_60'] = calculate_sma(close, 60)
            indicators['ema_12'] = calculate_ema(close, 12)
            indicators['ema_26'] = calculate_ema(close, 26)
            
            # 2. MACD
            print("  计算MACD...")
            macd_data = calculate_macd(close)
            indicators['macd'] = macd_data['macd']
            indicators['macd_signal'] = macd_data['signal']
            indicators['macd_histogram'] = macd_data['histogram']
            
            # 3. RSI
            print("  计算RSI...")
            indicators['rsi_14'] = calculate_rsi(close, 14)
            indicators['rsi_6'] = calculate_rsi(close, 6)
            
            # 4. 布林带
            print("  计算布林带...")
            bollinger_data = calculate_bollinger_bands(close)
            indicators['bb_upper'] = bollinger_data['upper']
            indicators['bb_middle'] = bollinger_data['middle']
            indicators['bb_lower'] = bollinger_data['lower']
            
            # 5. KDJ
            print("  计算KDJ...")
            kdj_data = calculate_kdj(high, low, close)
            indicators['kdj_k'] = kdj_data['k']
            indicators['kdj_d'] = kdj_data['d']
            indicators['kdj_j'] = kdj_data['j']
            
            # 6. 成交量指标
            print("  计算成交量指标...")
            indicators['obv'] = calculate_obv(close, volume)
            indicators['vwap'] = calculate_vwap(high, low, close, volume)
            
            # 合并所有数据
            result_df = hist_data.copy()
            for name, values in indicators.items():
                result_df[name] = values
            
            # 计算最新指标值
            latest_indicators = {}
            for name in indicators.keys():
                if not result_df[name].empty:
                    latest_value = result_df[name].iloc[-1]
                    if pd.notna(latest_value):
                        latest_indicators[name] = float(latest_value)
            
            # 保存结果
            test_result = {
                'symbol': symbol,
                'data_count': len(hist_data),
                'date_range': {
                    'start': hist_data['eob'].min().strftime('%Y-%m-%d'),
                    'end': hist_data['eob'].max().strftime('%Y-%m-%d')
                },
                'latest_price': float(close.iloc[-1]),
                'latest_indicators': latest_indicators,
                'status': 'success'
            }
            
            results['tests'].append(test_result)
            
            # 保存详细数据到CSV
            csv_filename = f"technical_indicators_{symbol.replace('.', '_')}.csv"
            result_df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
            print(f"  ✓ 技术指标数据已保存到: {csv_filename}")
            
            # 显示最新指标值
            print(f"  最新收盘价: {close.iloc[-1]:.2f}")
            print(f"  SMA20: {latest_indicators.get('sma_20', 'N/A'):.2f}" if 'sma_20' in latest_indicators else "  SMA20: N/A")
            print(f"  RSI14: {latest_indicators.get('rsi_14', 'N/A'):.2f}" if 'rsi_14' in latest_indicators else "  RSI14: N/A")
            print(f"  MACD: {latest_indicators.get('macd', 'N/A'):.4f}" if 'macd' in latest_indicators else "  MACD: N/A")
            
        except Exception as e:
            print(f"  ✗ 处理 {symbol} 失败: {e}")
            test_result = {
                'symbol': symbol,
                'status': 'error',
                'error': str(e)
            }
            results['tests'].append(test_result)
    
    return results

def main():
    """
    主函数
    """
    print("掘金量化 GM SDK 技术指标计算测试")
    print("=" * 50)
    
    # 配置token
    if not configure_token():
        print("\n请先配置有效的token后再运行测试")
        return
    
    # 测试token有效性
    try:
        test_dates = get_trading_dates('SHSE', '2024-01-01', '2024-01-05')
        if not test_dates:
            print("Token验证失败，请检查token是否有效")
            return
        print("Token验证成功")
    except Exception as e:
        print(f"Token验证失败: {e}")
        return
    
    # 运行测试
    try:
        results = test_technical_indicators()
        
        # 保存结果到JSON文件
        output_file = 'demo_8_technical_indicators_results.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n\n测试完成！结果已保存到: {output_file}")
        
        # 统计测试结果
        total_tests = len(results['tests'])
        success_tests = len([t for t in results['tests'] if t['status'] == 'success'])
        error_tests = len([t for t in results['tests'] if t['status'] == 'error'])
        
        print(f"\n测试统计:")
        print(f"  总测试数: {total_tests}")
        print(f"  成功: {success_tests}")
        print(f"  失败: {error_tests}")
        print(f"  成功率: {success_tests/total_tests*100:.1f}%")
        
        # 显示技术指标说明
        print(f"\n技术指标说明:")
        print(f"  SMA: 简单移动平均线 (5, 10, 20, 60日)")
        print(f"  EMA: 指数移动平均线 (12, 26日)")
        print(f"  MACD: 指数平滑异同移动平均线")
        print(f"  RSI: 相对强弱指标 (6, 14日)")
        print(f"  布林带: 上轨、中轨、下轨")
        print(f"  KDJ: 随机指标 K、D、J值")
        print(f"  OBV: 能量潮指标")
        print(f"  VWAP: 成交量加权平均价格")
        
    except Exception as e:
        print(f"测试运行失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()