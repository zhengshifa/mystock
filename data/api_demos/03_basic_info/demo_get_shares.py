#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GM API Demo: get_shares() 获取股本信息
功能：测试 gm.get_shares() API的各种用法
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

def shares_to_dict(shares):
    """将shares对象转换为字典格式"""
    if shares is None:
        return None
    
    try:
        shares_dict = {}
        
        # 常见的shares属性
        attributes = [
            'symbol', 'sec_id', 'exchange', 'sec_type', 'sec_name',
            'pub_date', 'end_date', 'total_shares', 'float_shares',
            'restricted_shares', 'free_float_shares', 'a_shares',
            'b_shares', 'h_shares', 'state_owned_shares', 'legal_person_shares',
            'management_shares', 'strategic_investor_shares', 'fund_shares',
            'general_legal_person_shares', 'other_shares', 'treasury_shares',
            'preferred_shares', 'convertible_shares', 'warrant_shares',
            'share_split_ratio', 'bonus_ratio', 'rights_ratio',
            'created_at', 'updated_at', 'data_source', 'currency'
        ]
        
        for attr in attributes:
            if hasattr(shares, attr):
                value = getattr(shares, attr)
                # 处理日期时间类型
                if attr in ['pub_date', 'end_date', 'created_at', 'updated_at'] and value:
                    try:
                        if hasattr(value, 'strftime'):
                            shares_dict[attr] = value.strftime('%Y-%m-%d')
                        else:
                            shares_dict[attr] = str(value)
                    except:
                        shares_dict[attr] = str(value)
                else:
                    shares_dict[attr] = value
        
        # 如果没有提取到任何属性，尝试直接转换
        if not shares_dict:
            shares_dict = {'raw_data': str(shares)}
        
        return shares_dict
        
    except Exception as e:
        return {'error': f'Failed to convert shares: {e}', 'raw_data': str(shares)}

def test_get_shares_major_stocks():
    """测试主要股票的股本信息查询"""
    print("\n=== 测试主要股票的股本信息查询 ===")
    
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
    
    # 查询最近的股本信息
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    for stock_info in major_stocks:
        try:
            print(f"\n查询 {stock_info['name']} ({stock_info['symbol']}) 的股本信息...")
            
            # 获取股本信息
            shares = gm.get_shares(
                symbol=stock_info['symbol'],
                end_date=end_date
            )
            
            if shares is not None:
                # 转换为字典列表
                shares_list = []
                if hasattr(shares, '__iter__') and not isinstance(shares, str):
                    for share in shares:
                        share_dict = shares_to_dict(share)
                        if share_dict:
                            shares_list.append(share_dict)
                else:
                    share_dict = shares_to_dict(shares)
                    if share_dict:
                        shares_list.append(share_dict)
                
                result = {
                    'symbol': stock_info['symbol'],
                    'name': stock_info['name'],
                    'end_date': end_date,
                    'shares': shares_list,
                    'count': len(shares_list),
                    'timestamp': datetime.now().isoformat(),
                    'success': True,
                    'error': None
                }
                
                print(f"  获取到 {len(shares_list)} 条股本记录")
                
                # 分析股本结构
                if shares_list:
                    latest_share = shares_list[0] if shares_list else {}
                    
                    # 显示基本股本信息
                    total_shares = latest_share.get('total_shares')
                    float_shares = latest_share.get('float_shares')
                    restricted_shares = latest_share.get('restricted_shares')
                    free_float_shares = latest_share.get('free_float_shares')
                    
                    print(f"  最新股本信息:")
                    if total_shares is not None:
                        print(f"    总股本: {total_shares:,.0f} 股" if isinstance(total_shares, (int, float)) else f"    总股本: {total_shares}")
                    if float_shares is not None:
                        print(f"    流通股本: {float_shares:,.0f} 股" if isinstance(float_shares, (int, float)) else f"    流通股本: {float_shares}")
                    if restricted_shares is not None:
                        print(f"    限售股本: {restricted_shares:,.0f} 股" if isinstance(restricted_shares, (int, float)) else f"    限售股本: {restricted_shares}")
                    if free_float_shares is not None:
                        print(f"    自由流通股本: {free_float_shares:,.0f} 股" if isinstance(free_float_shares, (int, float)) else f"    自由流通股本: {free_float_shares}")
                    
                    # 计算流通比例
                    if total_shares and float_shares and isinstance(total_shares, (int, float)) and isinstance(float_shares, (int, float)):
                        float_ratio = float_shares / total_shares * 100
                        print(f"    流通比例: {float_ratio:.2f}%")
                    
                    # 显示股本结构详情
                    a_shares = latest_share.get('a_shares')
                    b_shares = latest_share.get('b_shares')
                    h_shares = latest_share.get('h_shares')
                    
                    if any([a_shares, b_shares, h_shares]):
                        print(f"  股本结构:")
                        if a_shares is not None:
                            print(f"    A股: {a_shares:,.0f} 股" if isinstance(a_shares, (int, float)) else f"    A股: {a_shares}")
                        if b_shares is not None:
                            print(f"    B股: {b_shares:,.0f} 股" if isinstance(b_shares, (int, float)) else f"    B股: {b_shares}")
                        if h_shares is not None:
                            print(f"    H股: {h_shares:,.0f} 股" if isinstance(h_shares, (int, float)) else f"    H股: {h_shares}")
                    
                    # 显示股东结构
                    state_owned = latest_share.get('state_owned_shares')
                    legal_person = latest_share.get('legal_person_shares')
                    management = latest_share.get('management_shares')
                    
                    if any([state_owned, legal_person, management]):
                        print(f"  股东结构:")
                        if state_owned is not None:
                            print(f"    国有股: {state_owned:,.0f} 股" if isinstance(state_owned, (int, float)) else f"    国有股: {state_owned}")
                        if legal_person is not None:
                            print(f"    法人股: {legal_person:,.0f} 股" if isinstance(legal_person, (int, float)) else f"    法人股: {legal_person}")
                        if management is not None:
                            print(f"    管理层持股: {management:,.0f} 股" if isinstance(management, (int, float)) else f"    管理层持股: {management}")
                    
                    # 显示发布日期
                    pub_date = latest_share.get('pub_date')
                    end_date_info = latest_share.get('end_date')
                    if pub_date or end_date_info:
                        print(f"  日期信息:")
                        if pub_date:
                            print(f"    发布日期: {pub_date}")
                        if end_date_info:
                            print(f"    截止日期: {end_date_info}")
                
            else:
                result = {
                    'symbol': stock_info['symbol'],
                    'name': stock_info['name'],
                    'end_date': end_date,
                    'shares': [],
                    'count': 0,
                    'timestamp': datetime.now().isoformat(),
                    'success': False,
                    'error': 'No data returned'
                }
                print(f"  无股本数据")
            
            results.append(result)
            
        except Exception as e:
            print(f"  查询失败: {e}")
            results.append({
                'symbol': stock_info['symbol'],
                'name': stock_info['name'],
                'end_date': end_date,
                'shares': [],
                'count': 0,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            })
    
    return results

def test_get_shares_historical():
    """测试历史股本信息查询"""
    print("\n=== 测试历史股本信息查询 ===")
    
    # 测试不同的历史日期
    test_dates = [
        {
            'name': '最近日期',
            'end_date': datetime.now().strftime('%Y-%m-%d')
        },
        {
            'name': '1个月前',
            'end_date': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        },
        {
            'name': '3个月前',
            'end_date': (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        },
        {
            'name': '6个月前',
            'end_date': (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
        },
        {
            'name': '1年前',
            'end_date': (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        },
        {
            'name': '2023年底',
            'end_date': '2023-12-31'
        },
        {
            'name': '2022年底',
            'end_date': '2022-12-31'
        }
    ]
    
    results = []
    
    # 选择贵州茅台作为测试对象
    test_symbol = 'SHSE.600519'
    test_name = '贵州茅台'
    
    for date_info in test_dates:
        try:
            print(f"\n查询 {test_name} 在 {date_info['name']} ({date_info['end_date']}) 的股本信息...")
            
            # 获取股本信息
            shares = gm.get_shares(
                symbol=test_symbol,
                end_date=date_info['end_date']
            )
            
            if shares is not None:
                # 转换为字典列表
                shares_list = []
                if hasattr(shares, '__iter__') and not isinstance(shares, str):
                    for share in shares:
                        share_dict = shares_to_dict(share)
                        if share_dict:
                            shares_list.append(share_dict)
                else:
                    share_dict = shares_to_dict(shares)
                    if share_dict:
                        shares_list.append(share_dict)
                
                result = {
                    'date_name': date_info['name'],
                    'symbol': test_symbol,
                    'name': test_name,
                    'end_date': date_info['end_date'],
                    'shares': shares_list,
                    'count': len(shares_list),
                    'timestamp': datetime.now().isoformat(),
                    'success': True,
                    'error': None
                }
                
                print(f"  获取到 {len(shares_list)} 条股本记录")
                
                # 分析股本变化
                if shares_list:
                    latest_share = shares_list[0] if shares_list else {}
                    
                    total_shares = latest_share.get('total_shares')
                    float_shares = latest_share.get('float_shares')
                    
                    if total_shares is not None and isinstance(total_shares, (int, float)):
                        print(f"  总股本: {total_shares:,.0f} 股")
                    if float_shares is not None and isinstance(float_shares, (int, float)):
                        print(f"  流通股本: {float_shares:,.0f} 股")
                    
                    # 显示股本变化事件
                    share_split_ratio = latest_share.get('share_split_ratio')
                    bonus_ratio = latest_share.get('bonus_ratio')
                    rights_ratio = latest_share.get('rights_ratio')
                    
                    if any([share_split_ratio, bonus_ratio, rights_ratio]):
                        print(f"  股本变化事件:")
                        if share_split_ratio is not None:
                            print(f"    股票分割比例: {share_split_ratio}")
                        if bonus_ratio is not None:
                            print(f"    送股比例: {bonus_ratio}")
                        if rights_ratio is not None:
                            print(f"    配股比例: {rights_ratio}")
                
            else:
                result = {
                    'date_name': date_info['name'],
                    'symbol': test_symbol,
                    'name': test_name,
                    'end_date': date_info['end_date'],
                    'shares': [],
                    'count': 0,
                    'timestamp': datetime.now().isoformat(),
                    'success': False,
                    'error': 'No data returned'
                }
                print(f"  无股本数据")
            
            results.append(result)
            
        except Exception as e:
            print(f"  查询失败: {e}")
            results.append({
                'date_name': date_info['name'],
                'symbol': test_symbol,
                'name': test_name,
                'end_date': date_info['end_date'],
                'shares': [],
                'count': 0,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            })
    
    return results

def test_get_shares_multiple_symbols():
    """测试多个股票的股本信息批量查询"""
    print("\n=== 测试多个股票的股本信息批量查询 ===")
    
    # 测试不同类型的股票
    test_stocks = [
        {'symbol': 'SHSE.600000', 'name': '浦发银行', 'type': '银行'},
        {'symbol': 'SHSE.600519', 'name': '贵州茅台', 'type': '白酒'},
        {'symbol': 'SZSE.000858', 'name': '五粮液', 'type': '白酒'},
        {'symbol': 'SZSE.002415', 'name': '海康威视', 'type': '安防'},
        {'symbol': 'SZSE.300750', 'name': '宁德时代', 'type': '新能源'},
        {'symbol': 'SHSE.688981', 'name': '中芯国际', 'type': '芯片'},
        {'symbol': 'SZSE.300059', 'name': '东方财富', 'type': '金融科技'},
        {'symbol': 'SHSE.600036', 'name': '招商银行', 'type': '银行'},
        {'symbol': 'SZSE.000001', 'name': '平安银行', 'type': '银行'},
        {'symbol': 'SZSE.000002', 'name': '万科A', 'type': '地产'}
    ]
    
    results = []
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    # 统计信息
    industry_stats = {}
    total_market_cap = 0
    successful_queries = 0
    
    for stock_info in test_stocks:
        try:
            print(f"\n查询 {stock_info['name']} ({stock_info['symbol']}) [{stock_info['type']}] 的股本信息...")
            
            # 获取股本信息
            shares = gm.get_shares(
                symbol=stock_info['symbol'],
                end_date=end_date
            )
            
            if shares is not None:
                # 转换为字典列表
                shares_list = []
                if hasattr(shares, '__iter__') and not isinstance(shares, str):
                    for share in shares:
                        share_dict = shares_to_dict(share)
                        if share_dict:
                            shares_list.append(share_dict)
                else:
                    share_dict = shares_to_dict(shares)
                    if share_dict:
                        shares_list.append(share_dict)
                
                result = {
                    'symbol': stock_info['symbol'],
                    'name': stock_info['name'],
                    'industry_type': stock_info['type'],
                    'end_date': end_date,
                    'shares': shares_list,
                    'count': len(shares_list),
                    'timestamp': datetime.now().isoformat(),
                    'success': True,
                    'error': None
                }
                
                print(f"  获取到 {len(shares_list)} 条股本记录")
                successful_queries += 1
                
                # 统计行业信息
                industry_type = stock_info['type']
                if industry_type not in industry_stats:
                    industry_stats[industry_type] = {
                        'count': 0,
                        'total_shares': 0,
                        'float_shares': 0,
                        'stocks': []
                    }
                
                industry_stats[industry_type]['count'] += 1
                industry_stats[industry_type]['stocks'].append(stock_info['name'])
                
                # 分析股本信息
                if shares_list:
                    latest_share = shares_list[0] if shares_list else {}
                    
                    total_shares = latest_share.get('total_shares')
                    float_shares = latest_share.get('float_shares')
                    
                    if total_shares is not None and isinstance(total_shares, (int, float)):
                        print(f"  总股本: {total_shares:,.0f} 股")
                        industry_stats[industry_type]['total_shares'] += total_shares
                    
                    if float_shares is not None and isinstance(float_shares, (int, float)):
                        print(f"  流通股本: {float_shares:,.0f} 股")
                        industry_stats[industry_type]['float_shares'] += float_shares
                        
                        # 计算流通比例
                        if total_shares and isinstance(total_shares, (int, float)):
                            float_ratio = float_shares / total_shares * 100
                            print(f"  流通比例: {float_ratio:.2f}%")
                    
                    # 显示特殊股本结构
                    preferred_shares = latest_share.get('preferred_shares')
                    convertible_shares = latest_share.get('convertible_shares')
                    
                    if preferred_shares is not None or convertible_shares is not None:
                        print(f"  特殊股本:")
                        if preferred_shares is not None:
                            print(f"    优先股: {preferred_shares:,.0f} 股" if isinstance(preferred_shares, (int, float)) else f"    优先股: {preferred_shares}")
                        if convertible_shares is not None:
                            print(f"    可转换股: {convertible_shares:,.0f} 股" if isinstance(convertible_shares, (int, float)) else f"    可转换股: {convertible_shares}")
                
            else:
                result = {
                    'symbol': stock_info['symbol'],
                    'name': stock_info['name'],
                    'industry_type': stock_info['type'],
                    'end_date': end_date,
                    'shares': [],
                    'count': 0,
                    'timestamp': datetime.now().isoformat(),
                    'success': False,
                    'error': 'No data returned'
                }
                print(f"  无股本数据")
            
            results.append(result)
            
        except Exception as e:
            print(f"  查询失败: {e}")
            results.append({
                'symbol': stock_info['symbol'],
                'name': stock_info['name'],
                'industry_type': stock_info['type'],
                'end_date': end_date,
                'shares': [],
                'count': 0,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            })
    
    # 显示行业统计
    if industry_stats:
        print(f"\n=== 行业股本统计 ===")
        for industry, stats in industry_stats.items():
            print(f"\n{industry} 行业:")
            print(f"  股票数量: {stats['count']} 个")
            print(f"  股票列表: {', '.join(stats['stocks'])}")
            
            if stats['total_shares'] > 0:
                print(f"  总股本合计: {stats['total_shares']:,.0f} 股")
                print(f"  平均总股本: {stats['total_shares']/stats['count']:,.0f} 股")
            
            if stats['float_shares'] > 0:
                print(f"  流通股本合计: {stats['float_shares']:,.0f} 股")
                print(f"  平均流通股本: {stats['float_shares']/stats['count']:,.0f} 股")
                
                if stats['total_shares'] > 0:
                    avg_float_ratio = stats['float_shares'] / stats['total_shares'] * 100
                    print(f"  平均流通比例: {avg_float_ratio:.2f}%")
    
    # 添加统计信息到结果
    summary_result = {
        'summary_type': 'industry_statistics',
        'total_stocks': len(test_stocks),
        'successful_queries': successful_queries,
        'success_rate': successful_queries / len(test_stocks) * 100,
        'industry_stats': industry_stats,
        'timestamp': datetime.now().isoformat()
    }
    
    results.append(summary_result)
    
    return results

def test_get_shares_edge_cases():
    """测试边界情况"""
    print("\n=== 测试边界情况 ===")
    
    test_cases = [
        {
            'name': '不存在的股票代码',
            'symbol': 'INVALID.123456',
            'end_date': datetime.now().strftime('%Y-%m-%d')
        },
        {
            'name': '未来日期',
            'symbol': 'SHSE.600000',
            'end_date': '2025-12-31'
        },
        {
            'name': '很久以前的日期',
            'symbol': 'SHSE.600000',
            'end_date': '1990-01-01'
        },
        {
            'name': '非交易日（元旦）',
            'symbol': 'SHSE.600000',
            'end_date': '2023-01-01'
        },
        {
            'name': '周末日期',
            'symbol': 'SHSE.600000',
            'end_date': '2023-07-01'  # 周六
        },
        {
            'name': '空字符串股票代码',
            'symbol': '',
            'end_date': datetime.now().strftime('%Y-%m-%d')
        },
        {
            'name': '格式错误的股票代码',
            'symbol': '600000',  # 缺少交易所前缀
            'end_date': datetime.now().strftime('%Y-%m-%d')
        },
        {
            'name': '格式错误的日期',
            'symbol': 'SHSE.600000',
            'end_date': '2023-13-01'  # 不存在的月份
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        try:
            print(f"\n测试 {test_case['name']}...")
            print(f"  股票代码: {test_case['symbol']}")
            print(f"  截止日期: {test_case['end_date']}")
            
            # 获取股本信息
            shares = gm.get_shares(
                symbol=test_case['symbol'],
                end_date=test_case['end_date']
            )
            
            if shares is not None:
                # 转换为字典列表
                shares_list = []
                if hasattr(shares, '__iter__') and not isinstance(shares, str):
                    for share in shares:
                        share_dict = shares_to_dict(share)
                        if share_dict:
                            shares_list.append(share_dict)
                else:
                    share_dict = shares_to_dict(shares)
                    if share_dict:
                        shares_list.append(share_dict)
                
                result = {
                    'test_name': test_case['name'],
                    'symbol': test_case['symbol'],
                    'end_date': test_case['end_date'],
                    'shares': shares_list,
                    'count': len(shares_list),
                    'timestamp': datetime.now().isoformat(),
                    'success': True,
                    'error': None
                }
                
                print(f"  获取到 {len(shares_list)} 条股本记录")
                
                if shares_list:
                    print(f"  股本信息:")
                    for i, share in enumerate(shares_list[:3]):
                        total_shares = share.get('total_shares')
                        float_shares = share.get('float_shares')
                        pub_date = share.get('pub_date')
                        
                        print(f"    记录 {i+1}:")
                        if total_shares is not None:
                            print(f"      总股本: {total_shares}")
                        if float_shares is not None:
                            print(f"      流通股本: {float_shares}")
                        if pub_date:
                            print(f"      发布日期: {pub_date}")
                
            else:
                result = {
                    'test_name': test_case['name'],
                    'symbol': test_case['symbol'],
                    'end_date': test_case['end_date'],
                    'shares': [],
                    'count': 0,
                    'timestamp': datetime.now().isoformat(),
                    'success': False,
                    'error': 'No data returned'
                }
                print(f"  无股本数据")
            
            results.append(result)
            
        except Exception as e:
            print(f"  查询失败: {e}")
            results.append({
                'test_name': test_case['name'],
                'symbol': test_case['symbol'],
                'end_date': test_case['end_date'],
                'shares': [],
                'count': 0,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            })
    
    return results

def analyze_shares_data(results):
    """分析股本数据结构"""
    print("\n=== 股本数据结构分析 ===")
    
    all_fields = set()
    field_counts = {}
    total_shares_records = 0
    
    # 收集所有字段
    def collect_fields_from_results(data):
        nonlocal total_shares_records
        
        if isinstance(data, dict):
            if 'shares' in data:
                shares = data['shares']
                if isinstance(shares, list):
                    total_shares_records += len(shares)
                    for share in shares:
                        if isinstance(share, dict):
                            for field in share.keys():
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
        print(f"发现的股本字段 ({len(all_fields)}个):")
        for field in sorted(all_fields):
            count = field_counts[field]
            print(f"  {field}: 出现 {count} 次")
    else:
        print("未发现有效的股本字段")
    
    print(f"\n总股本记录数: {total_shares_records}")
    
    return {
        'total_fields': len(all_fields),
        'fields': list(all_fields),
        'field_counts': field_counts,
        'total_shares_records': total_shares_records
    }

def save_results(results, filename_prefix):
    """保存结果到文件"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 保存为JSON
    json_filename = f"{filename_prefix}_results_{timestamp}.json"
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump({
            'test_info': {
                'api_function': 'gm.get_shares()',
                'test_time': datetime.now().isoformat(),
                'description': 'GM API get_shares function test results'
            },
            'results': results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"结果已保存到: {json_filename}")
    
    # 尝试保存为CSV（展平股本数据）
    try:
        flattened_results = []
        
        def flatten_results(data, prefix=""):
            if isinstance(data, dict):
                if 'shares' in data:
                    # 这是一个包含shares的结果
                    base_info = {k: v for k, v in data.items() if k != 'shares'}
                    shares = data['shares']
                    
                    if isinstance(shares, list):
                        for i, share in enumerate(shares):
                            flat_result = base_info.copy()
                            flat_result['share_index'] = i
                            if isinstance(share, dict):
                                for key, value in share.items():
                                    flat_result[f'share_{key}'] = value
                            flattened_results.append(flat_result)
                    elif shares:
                        flat_result = base_info.copy()
                        if isinstance(shares, dict):
                            for key, value in shares.items():
                                flat_result[f'share_{key}'] = value
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
    print("GM API get_shares() 功能测试")
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
        
        # 测试1: 主要股票的股本信息查询
        major_results = test_get_shares_major_stocks()
        save_results(major_results, 'get_shares_major')
        all_results.append(major_results)
        
        # 测试2: 历史股本信息查询
        historical_results = test_get_shares_historical()
        save_results(historical_results, 'get_shares_historical')
        all_results.append(historical_results)
        
        # 测试3: 多个股票的股本信息批量查询
        multiple_results = test_get_shares_multiple_symbols()
        save_results(multiple_results, 'get_shares_multiple')
        all_results.append(multiple_results)
        
        # 测试4: 边界情况测试
        edge_results = test_get_shares_edge_cases()
        save_results(edge_results, 'get_shares_edge_cases')
        all_results.append(edge_results)
        
        # 分析数据结构
        structure_analysis = analyze_shares_data(all_results)
        
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
        print(f"主要股票测试: {major_success}/{major_total} 成功, {major_data} 条股本记录")
        
        historical_success, historical_total, historical_data = count_success_and_data(historical_results)
        print(f"历史股本测试: {historical_success}/{historical_total} 成功, {historical_data} 条股本记录")
        
        multiple_success, multiple_total, multiple_data = count_success_and_data(multiple_results)
        print(f"批量查询测试: {multiple_success}/{multiple_total} 成功, {multiple_data} 条股本记录")
        
        edge_success, edge_total, edge_data = count_success_and_data(edge_results)
        print(f"边界情况测试: {edge_success}/{edge_total} 成功, {edge_data} 条股本记录")
        
        # 总体统计
        total_tests = major_total + historical_total + multiple_total + edge_total
        total_success = major_success + historical_success + multiple_success + edge_success
        total_data_count = major_data + historical_data + multiple_data + edge_data
        
        print(f"\n总体成功率: {total_success}/{total_tests} ({total_success/total_tests*100:.1f}%)")
        print(f"总股本记录数: {total_data_count}")
        
        # 数据结构统计
        print(f"\n股本数据结构:")
        print(f"  发现字段数: {structure_analysis['total_fields']}")
        if structure_analysis['total_fields'] > 0:
            print(f"  主要字段: {', '.join(list(structure_analysis['fields'])[:10])}")
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
    
    print("\nget_shares() API测试完成！")

if __name__ == "__main__":
    main()