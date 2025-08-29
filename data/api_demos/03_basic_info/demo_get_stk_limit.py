#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GM API Demo: get_stk_limit() 获取股票涨跌停价格
功能：测试 gm.get_stk_limit() API的各种用法
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import gmtrade as gm
import pandas as pd
import json
from datetime import datetime, timedelta
import time

def load_config():
    """加载配置文件"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'gm_config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载配置文件失败: {e}")
        return None

def init_gm_api(config):
    """初始化GM API"""
    try:
        # 设置token
        gm.set_token(config['token'])
        
        # 设置服务地址
        gm.set_serv_addr(config['md_addr'])
        
        print("GM API初始化成功")
        return True
    except Exception as e:
        print(f"GM API初始化失败: {e}")
        return False

def stk_limit_to_dict(stk_limit):
    """将stk_limit对象转换为字典格式"""
    if stk_limit is None:
        return None
    
    try:
        limit_dict = {}
        
        # 常见的stk_limit属性
        attributes = [
            'symbol', 'sec_id', 'exchange', 'sec_type', 'sec_name',
            'trade_date', 'pre_close', 'limit_up', 'limit_down',
            'limit_up_ratio', 'limit_down_ratio', 'price_tick',
            'min_order_qty', 'max_order_qty', 'lot_size',
            'trading_status', 'suspension_reason', 'is_suspended',
            'open_auction_start', 'open_auction_end', 'close_auction_start',
            'close_auction_end', 'trading_start', 'trading_end',
            'created_at', 'updated_at', 'data_source'
        ]
        
        for attr in attributes:
            if hasattr(stk_limit, attr):
                value = getattr(stk_limit, attr)
                # 处理日期时间类型
                if attr in ['trade_date', 'created_at', 'updated_at'] and value:
                    try:
                        if hasattr(value, 'strftime'):
                            limit_dict[attr] = value.strftime('%Y-%m-%d')
                        else:
                            limit_dict[attr] = str(value)
                    except:
                        limit_dict[attr] = str(value)
                # 处理时间类型
                elif attr in ['open_auction_start', 'open_auction_end', 'close_auction_start', 'close_auction_end', 'trading_start', 'trading_end'] and value:
                    try:
                        if hasattr(value, 'strftime'):
                            limit_dict[attr] = value.strftime('%H:%M:%S')
                        else:
                            limit_dict[attr] = str(value)
                    except:
                        limit_dict[attr] = str(value)
                else:
                    limit_dict[attr] = value
        
        # 如果没有提取到任何属性，尝试直接转换
        if not limit_dict:
            limit_dict = {'raw_data': str(stk_limit)}
        
        return limit_dict
        
    except Exception as e:
        return {'error': f'Failed to convert stk_limit: {e}', 'raw_data': str(stk_limit)}

def test_get_stk_limit_major_stocks():
    """测试主要股票的涨跌停价格查询"""
    print("\n=== 测试主要股票的涨跌停价格查询 ===")
    
    # 测试主要股票
    major_stocks = [
        {'symbol': 'SHSE.600000', 'name': '浦发银行'},
        {'symbol': 'SHSE.600036', 'name': '招商银行'},
        {'symbol': 'SHSE.600519', 'name': '贵州茅台'},
        {'symbol': 'SHSE.600887', 'name': '伊利股份'},
        {'symbol': 'SZSE.000001', 'name': '平安银行'},
        {'symbol': 'SZSE.000002', 'name': '万科A'},
        {'symbol': 'SZSE.000858', 'name': '五粮液'},
        {'symbol': 'SZSE.002415', 'name': '海康威视'},
        {'symbol': 'SZSE.300059', 'name': '东方财富'},
        {'symbol': 'SZSE.300750', 'name': '宁德时代'}
    ]
    
    results = []
    
    # 查询最近交易日的涨跌停价格
    trade_date = datetime.now().strftime('%Y-%m-%d')
    
    for stock_info in major_stocks:
        try:
            print(f"\n查询 {stock_info['name']} ({stock_info['symbol']}) 的涨跌停价格...")
            
            # 获取涨跌停价格信息
            stk_limit = gm.get_stk_limit(
                symbol=stock_info['symbol'],
                trade_date=trade_date
            )
            
            if stk_limit is not None:
                # 转换为字典列表
                limit_list = []
                if hasattr(stk_limit, '__iter__') and not isinstance(stk_limit, str):
                    for limit in stk_limit:
                        limit_dict = stk_limit_to_dict(limit)
                        if limit_dict:
                            limit_list.append(limit_dict)
                else:
                    limit_dict = stk_limit_to_dict(stk_limit)
                    if limit_dict:
                        limit_list.append(limit_dict)
                
                result = {
                    'symbol': stock_info['symbol'],
                    'name': stock_info['name'],
                    'trade_date': trade_date,
                    'limits': limit_list,
                    'count': len(limit_list),
                    'timestamp': datetime.now().isoformat(),
                    'success': True,
                    'error': None
                }
                
                print(f"  获取到 {len(limit_list)} 条涨跌停记录")
                
                # 分析涨跌停信息
                if limit_list:
                    latest_limit = limit_list[0] if limit_list else {}
                    
                    # 显示基本价格信息
                    pre_close = latest_limit.get('pre_close')
                    limit_up = latest_limit.get('limit_up')
                    limit_down = latest_limit.get('limit_down')
                    limit_up_ratio = latest_limit.get('limit_up_ratio')
                    limit_down_ratio = latest_limit.get('limit_down_ratio')
                    
                    print(f"  价格信息:")
                    if pre_close is not None:
                        print(f"    昨收价: {pre_close:.2f}" if isinstance(pre_close, (int, float)) else f"    昨收价: {pre_close}")
                    if limit_up is not None:
                        print(f"    涨停价: {limit_up:.2f}" if isinstance(limit_up, (int, float)) else f"    涨停价: {limit_up}")
                    if limit_down is not None:
                        print(f"    跌停价: {limit_down:.2f}" if isinstance(limit_down, (int, float)) else f"    跌停价: {limit_down}")
                    
                    # 显示涨跌停比例
                    if limit_up_ratio is not None or limit_down_ratio is not None:
                        print(f"  涨跌停比例:")
                        if limit_up_ratio is not None:
                            print(f"    涨停比例: {limit_up_ratio:.2f}%" if isinstance(limit_up_ratio, (int, float)) else f"    涨停比例: {limit_up_ratio}")
                        if limit_down_ratio is not None:
                            print(f"    跌停比例: {limit_down_ratio:.2f}%" if isinstance(limit_down_ratio, (int, float)) else f"    跌停比例: {limit_down_ratio}")
                    
                    # 计算价格区间
                    if isinstance(limit_up, (int, float)) and isinstance(limit_down, (int, float)):
                        price_range = limit_up - limit_down
                        print(f"    价格区间: {price_range:.2f} ({limit_down:.2f} - {limit_up:.2f})")
                        
                        if isinstance(pre_close, (int, float)) and pre_close > 0:
                            range_ratio = price_range / pre_close * 100
                            print(f"    区间幅度: {range_ratio:.2f}%")
                    
                    # 显示交易参数
                    price_tick = latest_limit.get('price_tick')
                    min_order_qty = latest_limit.get('min_order_qty')
                    max_order_qty = latest_limit.get('max_order_qty')
                    lot_size = latest_limit.get('lot_size')
                    
                    if any([price_tick, min_order_qty, max_order_qty, lot_size]):
                        print(f"  交易参数:")
                        if price_tick is not None:
                            print(f"    最小价格变动: {price_tick}")
                        if min_order_qty is not None:
                            print(f"    最小委托量: {min_order_qty}")
                        if max_order_qty is not None:
                            print(f"    最大委托量: {max_order_qty}")
                        if lot_size is not None:
                            print(f"    交易单位: {lot_size}")
                    
                    # 显示交易状态
                    trading_status = latest_limit.get('trading_status')
                    is_suspended = latest_limit.get('is_suspended')
                    suspension_reason = latest_limit.get('suspension_reason')
                    
                    if trading_status or is_suspended or suspension_reason:
                        print(f"  交易状态:")
                        if trading_status:
                            print(f"    交易状态: {trading_status}")
                        if is_suspended is not None:
                            print(f"    是否停牌: {'是' if is_suspended else '否'}")
                        if suspension_reason:
                            print(f"    停牌原因: {suspension_reason}")
                    
                    # 显示交易时间
                    trading_start = latest_limit.get('trading_start')
                    trading_end = latest_limit.get('trading_end')
                    open_auction_start = latest_limit.get('open_auction_start')
                    open_auction_end = latest_limit.get('open_auction_end')
                    
                    if any([trading_start, trading_end, open_auction_start, open_auction_end]):
                        print(f"  交易时间:")
                        if open_auction_start and open_auction_end:
                            print(f"    开盘集合竞价: {open_auction_start} - {open_auction_end}")
                        if trading_start and trading_end:
                            print(f"    连续交易: {trading_start} - {trading_end}")
                
            else:
                result = {
                    'symbol': stock_info['symbol'],
                    'name': stock_info['name'],
                    'trade_date': trade_date,
                    'limits': [],
                    'count': 0,
                    'timestamp': datetime.now().isoformat(),
                    'success': False,
                    'error': 'No data returned'
                }
                print(f"  无涨跌停数据")
            
            results.append(result)
            
        except Exception as e:
            print(f"  查询失败: {e}")
            results.append({
                'symbol': stock_info['symbol'],
                'name': stock_info['name'],
                'trade_date': trade_date,
                'limits': [],
                'count': 0,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            })
    
    return results

def test_get_stk_limit_different_dates():
    """测试不同日期的涨跌停价格查询"""
    print("\n=== 测试不同日期的涨跌停价格查询 ===")
    
    # 测试不同的交易日期
    test_dates = [
        {
            'name': '今日',
            'trade_date': datetime.now().strftime('%Y-%m-%d')
        },
        {
            'name': '昨日',
            'trade_date': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        },
        {
            'name': '1周前',
            'trade_date': (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        },
        {
            'name': '1个月前',
            'trade_date': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        },
        {
            'name': '2024年1月2日',
            'trade_date': '2024-01-02'
        },
        {
            'name': '2023年12月29日',
            'trade_date': '2023-12-29'
        },
        {
            'name': '2023年6月15日',
            'trade_date': '2023-06-15'
        }
    ]
    
    results = []
    
    # 选择贵州茅台作为测试对象
    test_symbol = 'SHSE.600519'
    test_name = '贵州茅台'
    
    for date_info in test_dates:
        try:
            print(f"\n查询 {test_name} 在 {date_info['name']} ({date_info['trade_date']}) 的涨跌停价格...")
            
            # 获取涨跌停价格信息
            stk_limit = gm.get_stk_limit(
                symbol=test_symbol,
                trade_date=date_info['trade_date']
            )
            
            if stk_limit is not None:
                # 转换为字典列表
                limit_list = []
                if hasattr(stk_limit, '__iter__') and not isinstance(stk_limit, str):
                    for limit in stk_limit:
                        limit_dict = stk_limit_to_dict(limit)
                        if limit_dict:
                            limit_list.append(limit_dict)
                else:
                    limit_dict = stk_limit_to_dict(stk_limit)
                    if limit_dict:
                        limit_list.append(limit_dict)
                
                result = {
                    'date_name': date_info['name'],
                    'symbol': test_symbol,
                    'name': test_name,
                    'trade_date': date_info['trade_date'],
                    'limits': limit_list,
                    'count': len(limit_list),
                    'timestamp': datetime.now().isoformat(),
                    'success': True,
                    'error': None
                }
                
                print(f"  获取到 {len(limit_list)} 条涨跌停记录")
                
                # 分析价格变化
                if limit_list:
                    latest_limit = limit_list[0] if limit_list else {}
                    
                    pre_close = latest_limit.get('pre_close')
                    limit_up = latest_limit.get('limit_up')
                    limit_down = latest_limit.get('limit_down')
                    
                    if all(isinstance(x, (int, float)) for x in [pre_close, limit_up, limit_down] if x is not None):
                        print(f"  价格信息: 昨收 {pre_close:.2f}, 涨停 {limit_up:.2f}, 跌停 {limit_down:.2f}")
                        
                        # 计算涨跌停幅度
                        if pre_close and pre_close > 0:
                            up_ratio = (limit_up - pre_close) / pre_close * 100
                            down_ratio = (limit_down - pre_close) / pre_close * 100
                            print(f"  涨跌停幅度: +{up_ratio:.2f}% / {down_ratio:.2f}%")
                    
                    # 显示交易状态
                    trading_status = latest_limit.get('trading_status')
                    is_suspended = latest_limit.get('is_suspended')
                    
                    if trading_status or is_suspended is not None:
                        status_info = []
                        if trading_status:
                            status_info.append(f"状态: {trading_status}")
                        if is_suspended is not None:
                            status_info.append(f"停牌: {'是' if is_suspended else '否'}")
                        print(f"  交易状态: {', '.join(status_info)}")
                
            else:
                result = {
                    'date_name': date_info['name'],
                    'symbol': test_symbol,
                    'name': test_name,
                    'trade_date': date_info['trade_date'],
                    'limits': [],
                    'count': 0,
                    'timestamp': datetime.now().isoformat(),
                    'success': False,
                    'error': 'No data returned'
                }
                print(f"  无涨跌停数据")
            
            results.append(result)
            
        except Exception as e:
            print(f"  查询失败: {e}")
            results.append({
                'date_name': date_info['name'],
                'symbol': test_symbol,
                'name': test_name,
                'trade_date': date_info['trade_date'],
                'limits': [],
                'count': 0,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            })
    
    return results

def test_get_stk_limit_different_markets():
    """测试不同市场的涨跌停价格查询"""
    print("\n=== 测试不同市场的涨跌停价格查询 ===")
    
    # 测试不同市场的股票
    market_stocks = [
        # 上海主板
        {'symbol': 'SHSE.600000', 'name': '浦发银行', 'market': '上海主板'},
        {'symbol': 'SHSE.600519', 'name': '贵州茅台', 'market': '上海主板'},
        
        # 科创板
        {'symbol': 'SHSE.688981', 'name': '中芯国际', 'market': '科创板'},
        {'symbol': 'SHSE.688036', 'name': '传音控股', 'market': '科创板'},
        
        # 深圳主板
        {'symbol': 'SZSE.000001', 'name': '平安银行', 'market': '深圳主板'},
        {'symbol': 'SZSE.000002', 'name': '万科A', 'market': '深圳主板'},
        
        # 中小板
        {'symbol': 'SZSE.002415', 'name': '海康威视', 'market': '中小板'},
        {'symbol': 'SZSE.002594', 'name': '比亚迪', 'market': '中小板'},
        
        # 创业板
        {'symbol': 'SZSE.300059', 'name': '东方财富', 'market': '创业板'},
        {'symbol': 'SZSE.300750', 'name': '宁德时代', 'market': '创业板'}
    ]
    
    results = []
    trade_date = datetime.now().strftime('%Y-%m-%d')
    
    # 统计信息
    market_stats = {}
    
    for stock_info in market_stocks:
        try:
            print(f"\n查询 {stock_info['name']} ({stock_info['symbol']}) [{stock_info['market']}] 的涨跌停价格...")
            
            # 获取涨跌停价格信息
            stk_limit = gm.get_stk_limit(
                symbol=stock_info['symbol'],
                trade_date=trade_date
            )
            
            if stk_limit is not None:
                # 转换为字典列表
                limit_list = []
                if hasattr(stk_limit, '__iter__') and not isinstance(stk_limit, str):
                    for limit in stk_limit:
                        limit_dict = stk_limit_to_dict(limit)
                        if limit_dict:
                            limit_list.append(limit_dict)
                else:
                    limit_dict = stk_limit_to_dict(stk_limit)
                    if limit_dict:
                        limit_list.append(limit_dict)
                
                result = {
                    'symbol': stock_info['symbol'],
                    'name': stock_info['name'],
                    'market': stock_info['market'],
                    'trade_date': trade_date,
                    'limits': limit_list,
                    'count': len(limit_list),
                    'timestamp': datetime.now().isoformat(),
                    'success': True,
                    'error': None
                }
                
                print(f"  获取到 {len(limit_list)} 条涨跌停记录")
                
                # 统计市场信息
                market = stock_info['market']
                if market not in market_stats:
                    market_stats[market] = {
                        'count': 0,
                        'successful': 0,
                        'avg_limit_ratio': [],
                        'stocks': []
                    }
                
                market_stats[market]['count'] += 1
                market_stats[market]['successful'] += 1
                market_stats[market]['stocks'].append(stock_info['name'])
                
                # 分析涨跌停信息
                if limit_list:
                    latest_limit = limit_list[0] if limit_list else {}
                    
                    pre_close = latest_limit.get('pre_close')
                    limit_up = latest_limit.get('limit_up')
                    limit_down = latest_limit.get('limit_down')
                    limit_up_ratio = latest_limit.get('limit_up_ratio')
                    limit_down_ratio = latest_limit.get('limit_down_ratio')
                    
                    # 显示价格信息
                    if all(isinstance(x, (int, float)) for x in [pre_close, limit_up, limit_down] if x is not None):
                        print(f"  价格: 昨收 {pre_close:.2f}, 涨停 {limit_up:.2f}, 跌停 {limit_down:.2f}")
                    
                    # 显示涨跌停比例
                    if limit_up_ratio is not None and limit_down_ratio is not None:
                        if isinstance(limit_up_ratio, (int, float)) and isinstance(limit_down_ratio, (int, float)):
                            print(f"  涨跌停比例: +{limit_up_ratio:.2f}% / {limit_down_ratio:.2f}%")
                            market_stats[market]['avg_limit_ratio'].append(abs(limit_up_ratio))
                    
                    # 显示交易参数
                    price_tick = latest_limit.get('price_tick')
                    lot_size = latest_limit.get('lot_size')
                    
                    if price_tick is not None or lot_size is not None:
                        params = []
                        if price_tick is not None:
                            params.append(f"最小变动: {price_tick}")
                        if lot_size is not None:
                            params.append(f"交易单位: {lot_size}")
                        print(f"  交易参数: {', '.join(params)}")
                
            else:
                result = {
                    'symbol': stock_info['symbol'],
                    'name': stock_info['name'],
                    'market': stock_info['market'],
                    'trade_date': trade_date,
                    'limits': [],
                    'count': 0,
                    'timestamp': datetime.now().isoformat(),
                    'success': False,
                    'error': 'No data returned'
                }
                print(f"  无涨跌停数据")
                
                # 统计失败的查询
                market = stock_info['market']
                if market not in market_stats:
                    market_stats[market] = {
                        'count': 0,
                        'successful': 0,
                        'avg_limit_ratio': [],
                        'stocks': []
                    }
                market_stats[market]['count'] += 1
                market_stats[market]['stocks'].append(stock_info['name'])
            
            results.append(result)
            
        except Exception as e:
            print(f"  查询失败: {e}")
            results.append({
                'symbol': stock_info['symbol'],
                'name': stock_info['name'],
                'market': stock_info['market'],
                'trade_date': trade_date,
                'limits': [],
                'count': 0,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            })
            
            # 统计失败的查询
            market = stock_info['market']
            if market not in market_stats:
                market_stats[market] = {
                    'count': 0,
                    'successful': 0,
                    'avg_limit_ratio': [],
                    'stocks': []
                }
            market_stats[market]['count'] += 1
            market_stats[market]['stocks'].append(stock_info['name'])
    
    # 显示市场统计
    if market_stats:
        print(f"\n=== 市场统计 ===")
        for market, stats in market_stats.items():
            print(f"\n{market}:")
            print(f"  测试股票数: {stats['count']} 个")
            print(f"  成功查询数: {stats['successful']} 个")
            print(f"  成功率: {stats['successful']/stats['count']*100:.1f}%")
            print(f"  股票列表: {', '.join(stats['stocks'])}")
            
            if stats['avg_limit_ratio']:
                avg_ratio = sum(stats['avg_limit_ratio']) / len(stats['avg_limit_ratio'])
                print(f"  平均涨跌停比例: ±{avg_ratio:.2f}%")
    
    # 添加统计信息到结果
    summary_result = {
        'summary_type': 'market_statistics',
        'total_stocks': len(market_stocks),
        'market_stats': market_stats,
        'timestamp': datetime.now().isoformat()
    }
    
    results.append(summary_result)
    
    return results

def test_get_stk_limit_edge_cases():
    """测试边界情况"""
    print("\n=== 测试边界情况 ===")
    
    test_cases = [
        {
            'name': '不存在的股票代码',
            'symbol': 'INVALID.123456',
            'trade_date': datetime.now().strftime('%Y-%m-%d')
        },
        {
            'name': '未来日期',
            'symbol': 'SHSE.600000',
            'trade_date': '2025-12-31'
        },
        {
            'name': '很久以前的日期',
            'symbol': 'SHSE.600000',
            'trade_date': '1990-01-01'
        },
        {
            'name': '非交易日（元旦）',
            'symbol': 'SHSE.600000',
            'trade_date': '2023-01-01'
        },
        {
            'name': '周末日期',
            'symbol': 'SHSE.600000',
            'trade_date': '2023-07-01'  # 周六
        },
        {
            'name': '空字符串股票代码',
            'symbol': '',
            'trade_date': datetime.now().strftime('%Y-%m-%d')
        },
        {
            'name': '格式错误的股票代码',
            'symbol': '600000',  # 缺少交易所前缀
            'trade_date': datetime.now().strftime('%Y-%m-%d')
        },
        {
            'name': '格式错误的日期',
            'symbol': 'SHSE.600000',
            'trade_date': '2023-13-01'  # 不存在的月份
        },
        {
            'name': '已退市股票',
            'symbol': 'SHSE.600001',  # 假设的退市股票
            'trade_date': '2020-01-01'
        },
        {
            'name': '停牌股票',
            'symbol': 'SHSE.600519',  # 贵州茅台，假设某日停牌
            'trade_date': '2023-05-15'
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        try:
            print(f"\n测试 {test_case['name']}...")
            print(f"  股票代码: {test_case['symbol']}")
            print(f"  交易日期: {test_case['trade_date']}")
            
            # 获取涨跌停价格信息
            stk_limit = gm.get_stk_limit(
                symbol=test_case['symbol'],
                trade_date=test_case['trade_date']
            )
            
            if stk_limit is not None:
                # 转换为字典列表
                limit_list = []
                if hasattr(stk_limit, '__iter__') and not isinstance(stk_limit, str):
                    for limit in stk_limit:
                        limit_dict = stk_limit_to_dict(limit)
                        if limit_dict:
                            limit_list.append(limit_dict)
                else:
                    limit_dict = stk_limit_to_dict(stk_limit)
                    if limit_dict:
                        limit_list.append(limit_dict)
                
                result = {
                    'test_name': test_case['name'],
                    'symbol': test_case['symbol'],
                    'trade_date': test_case['trade_date'],
                    'limits': limit_list,
                    'count': len(limit_list),
                    'timestamp': datetime.now().isoformat(),
                    'success': True,
                    'error': None
                }
                
                print(f"  获取到 {len(limit_list)} 条涨跌停记录")
                
                if limit_list:
                    print(f"  涨跌停信息:")
                    for i, limit in enumerate(limit_list[:3]):
                        pre_close = limit.get('pre_close')
                        limit_up = limit.get('limit_up')
                        limit_down = limit.get('limit_down')
                        trading_status = limit.get('trading_status')
                        is_suspended = limit.get('is_suspended')
                        
                        print(f"    记录 {i+1}:")
                        if pre_close is not None:
                            print(f"      昨收价: {pre_close}")
                        if limit_up is not None:
                            print(f"      涨停价: {limit_up}")
                        if limit_down is not None:
                            print(f"      跌停价: {limit_down}")
                        if trading_status:
                            print(f"      交易状态: {trading_status}")
                        if is_suspended is not None:
                            print(f"      是否停牌: {'是' if is_suspended else '否'}")
                
            else:
                result = {
                    'test_name': test_case['name'],
                    'symbol': test_case['symbol'],
                    'trade_date': test_case['trade_date'],
                    'limits': [],
                    'count': 0,
                    'timestamp': datetime.now().isoformat(),
                    'success': False,
                    'error': 'No data returned'
                }
                print(f"  无涨跌停数据")
            
            results.append(result)
            
        except Exception as e:
            print(f"  查询失败: {e}")
            results.append({
                'test_name': test_case['name'],
                'symbol': test_case['symbol'],
                'trade_date': test_case['trade_date'],
                'limits': [],
                'count': 0,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            })
    
    return results

def analyze_stk_limit_data(results):
    """分析涨跌停数据结构"""
    print("\n=== 涨跌停数据结构分析 ===")
    
    all_fields = set()
    field_counts = {}
    total_limit_records = 0
    
    # 收集所有字段
    def collect_fields_from_results(data):
        nonlocal total_limit_records
        
        if isinstance(data, dict):
            if 'limits' in data:
                limits = data['limits']
                if isinstance(limits, list):
                    total_limit_records += len(limits)
                    for limit in limits:
                        if isinstance(limit, dict):
                            for field in limit.keys():
                                all_fields.add(field)
                                field_counts[field] = field_counts.get(field, 0) + 1
            else:
                # 递归处理嵌套字典
                for value in data.values():
                    if isinstance(value, (dict, list)):
                        collect_fields_from_results(value)
        elif isinstance(data, list):
            for item in data:
                collect_fields_from_results(item)
    
    # 分析所有结果
    for result_set in results:
        collect_fields_from_results(result_set)
    
    if all_fields:
        print(f"发现的涨跌停字段 ({len(all_fields)}个):")
        for field in sorted(all_fields):
            count = field_counts[field]
            print(f"  {field}: 出现 {count} 次")
    else:
        print("未发现有效的涨跌停字段")
    
    print(f"\n总涨跌停记录数: {total_limit_records}")
    
    return {
        'total_fields': len(all_fields),
        'fields': list(all_fields),
        'field_counts': field_counts,
        'total_limit_records': total_limit_records
    }

def save_results(results, filename_prefix):
    """保存结果到文件"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 保存为JSON
    json_filename = f"{filename_prefix}_results_{timestamp}.json"
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump({
            'test_info': {
                'api_function': 'gm.get_stk_limit()',
                'test_time': datetime.now().isoformat(),
                'description': 'GM API get_stk_limit function test results'
            },
            'results': results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"结果已保存到: {json_filename}")
    
    # 尝试保存为CSV（展平涨跌停数据）
    try:
        flattened_results = []
        
        def flatten_results(data, prefix=""):
            if isinstance(data, dict):
                if 'limits' in data:
                    # 这是一个包含limits的结果
                    base_info = {k: v for k, v in data.items() if k != 'limits'}
                    limits = data['limits']
                    
                    if isinstance(limits, list):
                        for i, limit in enumerate(limits):
                            flat_result = base_info.copy()
                            flat_result['limit_index'] = i
                            if isinstance(limit, dict):
                                for key, value in limit.items():
                                    flat_result[f'limit_{key}'] = value
                            flattened_results.append(flat_result)
                    elif limits:
                        flat_result = base_info.copy()
                        if isinstance(limits, dict):
                            for key, value in limits.items():
                                flat_result[f'limit_{key}'] = value
                        flattened_results.append(flat_result)
                    else:
                        flattened_results.append(base_info)
                else:
                    # 递归处理嵌套字典
                    for key, value in data.items():
                        if isinstance(value, (dict, list)):
                            flatten_results(value, f"{prefix}{key}_")
            elif isinstance(data, list):
                for item in data:
                    flatten_results(item, prefix)
        
        # 展平所有结果
        for result_set in results:
            flatten_results(result_set)
        
        if flattened_results:
            csv_filename = f"{filename_prefix}_results_{timestamp}.csv"
            df = pd.DataFrame(flattened_results)
            df.to_csv(csv_filename, encoding='utf-8-sig', index=False)
            print(f"结果已保存到: {csv_filename}")
            
    except Exception as e:
        print(f"保存CSV文件失败: {e}")

def main():
    """主函数"""
    print("GM API get_stk_limit() 功能测试")
    print("=" * 60)
    
    # 加载配置
    config = load_config()
    if not config:
        print("无法加载配置文件，退出测试")
        return
    
    # 初始化API
    if not init_gm_api(config):
        print("API初始化失败，退出测试")
        return
    
    try:
        all_results = []
        
        # 测试1: 主要股票的涨跌停价格查询
        major_results = test_get_stk_limit_major_stocks()
        save_results(major_results, 'get_stk_limit_major')
        all_results.append(major_results)
        
        # 测试2: 不同日期的涨跌停价格查询
        date_results = test_get_stk_limit_different_dates()
        save_results(date_results, 'get_stk_limit_dates')
        all_results.append(date_results)
        
        # 测试3: 不同市场的涨跌停价格查询
        market_results = test_get_stk_limit_different_markets()
        save_results(market_results, 'get_stk_limit_markets')
        all_results.append(market_results)
        
        # 测试4: 边界情况测试
        edge_results = test_get_stk_limit_edge_cases()
        save_results(edge_results, 'get_stk_limit_edge_cases')
        all_results.append(edge_results)
        
        # 分析数据结构
        structure_analysis = analyze_stk_limit_data(all_results)
        
        # 汇总统计
        print("\n=== 测试汇总 ===")
        
        # 统计各测试结果
        def count_success_and_data(results):
            success_count = 0
            total_count = 0
            data_count = 0
            
            def count_recursive(data):
                nonlocal success_count, total_count, data_count
                
                if isinstance(data, dict):
                    if 'success' in data and 'count' in data:
                        total_count += 1
                        if data['success']:
                            success_count += 1
                        data_count += data.get('count', 0)
                    else:
                        for value in data.values():
                            if isinstance(value, (dict, list)):
                                count_recursive(value)
                elif isinstance(data, list):
                    for item in data:
                        count_recursive(item)
            
            count_recursive(results)
            return success_count, total_count, data_count
        
        major_success, major_total, major_data = count_success_and_data(major_results)
        print(f"主要股票测试: {major_success}/{major_total} 成功, {major_data} 条涨跌停记录")
        
        date_success, date_total, date_data = count_success_and_data(date_results)
        print(f"不同日期测试: {date_success}/{date_total} 成功, {date_data} 条涨跌停记录")
        
        market_success, market_total, market_data = count_success_and_data(market_results)
        print(f"不同市场测试: {market_success}/{market_total} 成功, {market_data} 条涨跌停记录")
        
        edge_success, edge_total, edge_data = count_success_and_data(edge_results)
        print(f"边界情况测试: {edge_success}/{edge_total} 成功, {edge_data} 条涨跌停记录")
        
        # 总体统计
        total_tests = major_total + date_total + market_total + edge_total
        total_success = major_success + date_success + market_success + edge_success
        total_data_count = major_data + date_data + market_data + edge_data
        
        print(f"\n总体成功率: {total_success}/{total_tests} ({total_success/total_tests*100:.1f}%)")
        print(f"总涨跌停记录数: {total_data_count}")
        
        # 数据结构统计
        print(f"\n涨跌停数据结构:")
        print(f"  发现字段数: {structure_analysis['total_fields']}")
        if structure_analysis['total_fields'] > 0:
            print(f"  主要字段: {', '.join(list(structure_analysis['fields'])[:10])}")
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
    
    print("\nget_stk_limit() API测试完成！")

if __name__ == "__main__":
    main()