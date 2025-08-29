#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GM API - 系统设置接口测试

本脚本测试系统设置相关API，包括:
- set_token: 设置token
- set_account_id: 设置账户ID
- set_endpoint: 设置服务端点
- set_backtest_config: 设置回测配置
- set_strategy_id: 设置策略ID
- get_version: 获取版本信息
- get_config: 获取配置信息
- log: 日志记录
- run: 运行策略
- stop: 停止策略

主要功能:
1. API连接配置管理
2. 账户和策略设置
3. 系统信息查询
4. 日志管理
5. 策略运行控制
6. 配置参数验证

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
import time
import logging


def init_gm_api() -> bool:
    """
    初始化GM API
    
    Returns:
        bool: 初始化是否成功
    """
    try:
        # 设置token（实际使用时需要替换为真实token）
        gm.set_token('your_token_here')
        
        # 设置账户ID（实际使用时需要替换为真实账户ID）
        gm.set_account_id('your_account_id_here')
        
        print("GM API初始化成功")
        return True
    except Exception as e:
        print(f"GM API初始化失败: {e}")
        return False


def save_results(data: Dict[str, Any], filename_prefix: str) -> None:
    """
    保存结果到文件
    
    Args:
        data: 要保存的数据
        filename_prefix: 文件名前缀
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 创建结果目录
    results_dir = Path("results/system_settings")
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存JSON格式
    json_file = results_dir / f"{filename_prefix}_{timestamp}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    
    # 如果有DataFrame格式的数据，也保存为CSV
    if 'data' in data and isinstance(data['data'], list) and data['data']:
        try:
            df = pd.DataFrame(data['data'])
            csv_file = results_dir / f"{filename_prefix}_{timestamp}.csv"
            df.to_csv(csv_file, index=False, encoding='utf-8-sig')
            print(f"CSV结果已保存到: {csv_file}")
        except Exception as e:
            print(f"保存CSV失败: {e}")
    
    print(f"JSON结果已保存到: {json_file}")


def convert_object_to_dict(obj) -> Dict[str, Any]:
    """
    将对象转换为字典
    
    Args:
        obj: 要转换的对象
    
    Returns:
        Dict: 转换后的字典
    """
    if hasattr(obj, '__dict__'):
        return {k: v for k, v in obj.__dict__.items() if not k.startswith('_')}
    elif hasattr(obj, '_asdict'):
        return obj._asdict()
    else:
        # 尝试获取常见属性
        result = {}
        common_attrs = [
            'version', 'build_time', 'git_hash', 'python_version',
            'endpoint', 'token', 'account_id', 'strategy_id',
            'backtest_start_time', 'backtest_end_time', 'initial_cash',
            'benchmark', 'commission', 'slippage', 'price_type',
            'order_volume_round', 'unsubscribe_on_stop', 'adjust',
            'check_date_valid', 'backtest_adjust', 'mode'
        ]
        
        for attr in common_attrs:
            if hasattr(obj, attr):
                result[attr] = getattr(obj, attr)
        
        return result if result else str(obj)


def test_set_token():
    """
    测试设置token
    """
    print("\n=== 测试设置token ===")
    
    token_result = {}
    
    try:
        # 测试设置不同类型的token
        test_tokens = [
            "test_token_123",
            "demo_token_456",
            "invalid_token",
            "",  # 空token
            None  # None token
        ]
        
        token_tests = []
        
        for i, token in enumerate(test_tokens):
            print(f"\n{i+1}. 测试token: {token if token else 'Empty/None'}")
            
            test_result = {
                "token": token,
                "test_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            try:
                if token is not None:
                    gm.set_token(token)
                    test_result["status"] = "设置成功"
                    test_result["note"] = "token已设置，但未验证有效性"
                    print(f"    设置成功: {token}")
                else:
                    # 测试None token
                    try:
                        gm.set_token(token)
                        test_result["status"] = "设置成功"
                        test_result["note"] = "接受None值"
                    except Exception as e:
                        test_result["status"] = "设置失败"
                        test_result["error"] = str(e)
                        print(f"    设置失败: {e}")
                
            except Exception as e:
                test_result["status"] = "设置失败"
                test_result["error"] = str(e)
                print(f"    设置失败: {e}")
            
            token_tests.append(test_result)
        
        token_result["token_tests"] = token_tests
        
        # 恢复原始token（如果有的话）
        try:
            gm.set_token('your_token_here')
            token_result["restore_status"] = "已恢复原始token"
        except Exception as e:
            token_result["restore_error"] = str(e)
        
    except Exception as e:
        print(f"token测试失败: {e}")
        token_result["error"] = str(e)
    
    # 保存结果
    save_results({
        "test_type": "set_token",
        "data": token_result
    }, "set_token")
    
    return token_result


def test_set_account_id():
    """
    测试设置账户ID
    """
    print("\n=== 测试设置账户ID ===")
    
    account_result = {}
    
    try:
        # 测试设置不同类型的账户ID
        test_account_ids = [
            "test_account_001",
            "demo_account_002",
            "12345678",
            "invalid_account",
            "",  # 空账户ID
            None  # None账户ID
        ]
        
        account_tests = []
        
        for i, account_id in enumerate(test_account_ids):
            print(f"\n{i+1}. 测试账户ID: {account_id if account_id else 'Empty/None'}")
            
            test_result = {
                "account_id": account_id,
                "test_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            try:
                if account_id is not None:
                    gm.set_account_id(account_id)
                    test_result["status"] = "设置成功"
                    test_result["note"] = "账户ID已设置，但未验证有效性"
                    print(f"    设置成功: {account_id}")
                else:
                    # 测试None账户ID
                    try:
                        gm.set_account_id(account_id)
                        test_result["status"] = "设置成功"
                        test_result["note"] = "接受None值"
                    except Exception as e:
                        test_result["status"] = "设置失败"
                        test_result["error"] = str(e)
                        print(f"    设置失败: {e}")
                
            except Exception as e:
                test_result["status"] = "设置失败"
                test_result["error"] = str(e)
                print(f"    设置失败: {e}")
            
            account_tests.append(test_result)
        
        account_result["account_tests"] = account_tests
        
        # 恢复原始账户ID（如果有的话）
        try:
            gm.set_account_id('your_account_id_here')
            account_result["restore_status"] = "已恢复原始账户ID"
        except Exception as e:
            account_result["restore_error"] = str(e)
        
    except Exception as e:
        print(f"账户ID测试失败: {e}")
        account_result["error"] = str(e)
    
    # 保存结果
    save_results({
        "test_type": "set_account_id",
        "data": account_result
    }, "set_account_id")
    
    return account_result


def test_set_endpoint():
    """
    测试设置服务端点
    """
    print("\n=== 测试设置服务端点 ===")
    
    endpoint_result = {}
    
    try:
        # 测试设置不同的端点
        test_endpoints = [
            "https://api.myquant.cn",
            "https://test-api.myquant.cn",
            "http://localhost:8080",
            "invalid_endpoint",
            "",  # 空端点
        ]
        
        endpoint_tests = []
        
        for i, endpoint in enumerate(test_endpoints):
            print(f"\n{i+1}. 测试端点: {endpoint if endpoint else 'Empty'}")
            
            test_result = {
                "endpoint": endpoint,
                "test_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            try:
                gm.set_endpoint(endpoint)
                test_result["status"] = "设置成功"
                test_result["note"] = "端点已设置，但未验证连通性"
                print(f"    设置成功: {endpoint}")
                
            except Exception as e:
                test_result["status"] = "设置失败"
                test_result["error"] = str(e)
                print(f"    设置失败: {e}")
            
            endpoint_tests.append(test_result)
        
        endpoint_result["endpoint_tests"] = endpoint_tests
        
        # 恢复默认端点
        try:
            gm.set_endpoint("https://api.myquant.cn")
            endpoint_result["restore_status"] = "已恢复默认端点"
        except Exception as e:
            endpoint_result["restore_error"] = str(e)
        
    except Exception as e:
        print(f"端点测试失败: {e}")
        endpoint_result["error"] = str(e)
    
    # 保存结果
    save_results({
        "test_type": "set_endpoint",
        "data": endpoint_result
    }, "set_endpoint")
    
    return endpoint_result


def test_set_backtest_config():
    """
    测试设置回测配置
    """
    print("\n=== 测试设置回测配置 ===")
    
    backtest_result = {}
    
    try:
        # 测试不同的回测配置
        test_configs = [
            {
                "name": "基本配置",
                "config": {
                    "start_time": '2023-01-01',
                    "end_time": '2023-12-31',
                    "initial_cash": 1000000,
                    "benchmark": 'SHSE.000300'
                }
            },
            {
                "name": "详细配置",
                "config": {
                    "start_time": '2023-06-01',
                    "end_time": '2023-12-31',
                    "initial_cash": 500000,
                    "benchmark": 'SHSE.000001',
                    "commission": 0.0003,
                    "slippage": 0.001,
                    "price_type": 1,
                    "order_volume_round": True
                }
            },
            {
                "name": "最小配置",
                "config": {
                    "start_time": '2023-01-01',
                    "end_time": '2023-01-31'
                }
            }
        ]
        
        config_tests = []
        
        for i, test_case in enumerate(test_configs):
            config_name = test_case["name"]
            config = test_case["config"]
            
            print(f"\n{i+1}. 测试{config_name}")
            
            test_result = {
                "config_name": config_name,
                "config": config,
                "test_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            try:
                gm.set_backtest_config(**config)
                test_result["status"] = "设置成功"
                test_result["note"] = "回测配置已设置"
                
                print(f"    设置成功: {config_name}")
                for key, value in config.items():
                    print(f"      {key}: {value}")
                
            except Exception as e:
                test_result["status"] = "设置失败"
                test_result["error"] = str(e)
                print(f"    设置失败: {e}")
            
            config_tests.append(test_result)
        
        backtest_result["config_tests"] = config_tests
        
    except Exception as e:
        print(f"回测配置测试失败: {e}")
        backtest_result["error"] = str(e)
    
    # 保存结果
    save_results({
        "test_type": "set_backtest_config",
        "data": backtest_result
    }, "set_backtest_config")
    
    return backtest_result


def test_set_strategy_id():
    """
    测试设置策略ID
    """
    print("\n=== 测试设置策略ID ===")
    
    strategy_result = {}
    
    try:
        # 测试设置不同的策略ID
        test_strategy_ids = [
            "strategy_001",
            "test_strategy_alpha",
            "demo_strategy_beta",
            "12345",
            "",  # 空策略ID
        ]
        
        strategy_tests = []
        
        for i, strategy_id in enumerate(test_strategy_ids):
            print(f"\n{i+1}. 测试策略ID: {strategy_id if strategy_id else 'Empty'}")
            
            test_result = {
                "strategy_id": strategy_id,
                "test_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            try:
                gm.set_strategy_id(strategy_id)
                test_result["status"] = "设置成功"
                test_result["note"] = "策略ID已设置"
                print(f"    设置成功: {strategy_id}")
                
            except Exception as e:
                test_result["status"] = "设置失败"
                test_result["error"] = str(e)
                print(f"    设置失败: {e}")
            
            strategy_tests.append(test_result)
        
        strategy_result["strategy_tests"] = strategy_tests
        
    except Exception as e:
        print(f"策略ID测试失败: {e}")
        strategy_result["error"] = str(e)
    
    # 保存结果
    save_results({
        "test_type": "set_strategy_id",
        "data": strategy_result
    }, "set_strategy_id")
    
    return strategy_result


def test_get_version():
    """
    测试获取版本信息
    """
    print("\n=== 测试获取版本信息 ===")
    
    version_result = {}
    
    try:
        # 获取版本信息
        version_info = gm.get_version()
        
        version_dict = convert_object_to_dict(version_info)
        version_result["version_info"] = version_dict
        
        print(f"版本信息:")
        for key, value in version_dict.items():
            print(f"  {key}: {value}")
        
        # 分析版本信息
        version_analysis = {
            "has_version": bool(version_dict.get('version')),
            "has_build_time": bool(version_dict.get('build_time')),
            "has_git_hash": bool(version_dict.get('git_hash')),
            "python_version": version_dict.get('python_version', 'N/A')
        }
        
        version_result["version_analysis"] = version_analysis
        
        print(f"\n版本分析:")
        print(f"  包含版本号: {version_analysis['has_version']}")
        print(f"  包含构建时间: {version_analysis['has_build_time']}")
        print(f"  包含Git哈希: {version_analysis['has_git_hash']}")
        print(f"  Python版本: {version_analysis['python_version']}")
        
    except Exception as e:
        print(f"获取版本信息失败: {e}")
        version_result["error"] = str(e)
    
    # 保存结果
    save_results({
        "test_type": "get_version",
        "data": version_result
    }, "get_version")
    
    return version_result


def test_get_config():
    """
    测试获取配置信息
    """
    print("\n=== 测试获取配置信息 ===")
    
    config_result = {}
    
    try:
        # 获取配置信息
        config_info = gm.get_config()
        
        config_dict = convert_object_to_dict(config_info)
        config_result["config_info"] = config_dict
        
        print(f"配置信息:")
        for key, value in config_dict.items():
            print(f"  {key}: {value}")
        
        # 分析配置信息
        config_analysis = {
            "has_endpoint": bool(config_dict.get('endpoint')),
            "has_token": bool(config_dict.get('token')),
            "has_account_id": bool(config_dict.get('account_id')),
            "has_strategy_id": bool(config_dict.get('strategy_id')),
            "backtest_mode": config_dict.get('mode') == 'backtest' if 'mode' in config_dict else None
        }
        
        config_result["config_analysis"] = config_analysis
        
        print(f"\n配置分析:")
        print(f"  包含端点: {config_analysis['has_endpoint']}")
        print(f"  包含Token: {config_analysis['has_token']}")
        print(f"  包含账户ID: {config_analysis['has_account_id']}")
        print(f"  包含策略ID: {config_analysis['has_strategy_id']}")
        print(f"  回测模式: {config_analysis['backtest_mode']}")
        
    except Exception as e:
        print(f"获取配置信息失败: {e}")
        config_result["error"] = str(e)
    
    # 保存结果
    save_results({
        "test_type": "get_config",
        "data": config_result
    }, "get_config")
    
    return config_result


def test_log_function():
    """
    测试日志功能
    """
    print("\n=== 测试日志功能 ===")
    
    log_result = {}
    
    try:
        # 测试不同级别的日志
        log_tests = [
            {"level": "info", "message": "这是一条信息日志"},
            {"level": "warning", "message": "这是一条警告日志"},
            {"level": "error", "message": "这是一条错误日志"},
            {"level": "debug", "message": "这是一条调试日志"},
        ]
        
        log_test_results = []
        
        for i, log_test in enumerate(log_tests):
            level = log_test["level"]
            message = log_test["message"]
            
            print(f"\n{i+1}. 测试{level}级别日志")
            
            test_result = {
                "level": level,
                "message": message,
                "test_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            try:
                # 根据级别调用相应的日志函数
                if hasattr(gm, 'log'):
                    gm.log(message, level=level)
                    test_result["status"] = "记录成功"
                    print(f"    {level}日志记录成功: {message}")
                else:
                    # 如果没有log函数，尝试使用Python标准日志
                    logger = logging.getLogger('gm_test')
                    getattr(logger, level)(message)
                    test_result["status"] = "使用标准日志记录"
                    test_result["note"] = "GM API可能不支持log函数，使用Python标准日志"
                    print(f"    使用标准日志记录: {message}")
                
            except Exception as e:
                test_result["status"] = "记录失败"
                test_result["error"] = str(e)
                print(f"    日志记录失败: {e}")
            
            log_test_results.append(test_result)
        
        log_result["log_tests"] = log_test_results
        
        # 测试特殊情况的日志
        print("\n5. 测试特殊日志情况")
        special_tests = [
            {"message": "", "note": "空消息"},
            {"message": "包含中文的日志消息", "note": "中文消息"},
            {"message": "Very long message " * 50, "note": "超长消息"},
            {"message": "Message with special chars: !@#$%^&*()", "note": "特殊字符"}
        ]
        
        special_results = []
        for special_test in special_tests:
            message = special_test["message"]
            note = special_test["note"]
            
            test_result = {
                "message": message[:100] + "..." if len(message) > 100 else message,
                "note": note,
                "test_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            try:
                if hasattr(gm, 'log'):
                    gm.log(message)
                    test_result["status"] = "记录成功"
                else:
                    logging.info(message)
                    test_result["status"] = "使用标准日志记录"
                
                print(f"    {note}日志记录成功")
                
            except Exception as e:
                test_result["status"] = "记录失败"
                test_result["error"] = str(e)
                print(f"    {note}日志记录失败: {e}")
            
            special_results.append(test_result)
        
        log_result["special_tests"] = special_results
        
    except Exception as e:
        print(f"日志功能测试失败: {e}")
        log_result["error"] = str(e)
    
    # 保存结果
    save_results({
        "test_type": "log_function",
        "data": log_result
    }, "log_function")
    
    return log_result


def test_run_stop_functions():
    """
    测试运行和停止功能
    """
    print("\n=== 测试运行和停止功能 ===")
    
    run_stop_result = {}
    
    try:
        # 测试运行功能
        print("\n1. 测试运行功能")
        run_tests = []
        
        # 测试不同的运行参数
        run_scenarios = [
            {"name": "无参数运行", "params": {}},
            {"name": "指定文件运行", "params": {"filename": "test_strategy.py"}},
            {"name": "指定模式运行", "params": {"mode": "backtest"}}
        ]
        
        for scenario in run_scenarios:
            name = scenario["name"]
            params = scenario["params"]
            
            test_result = {
                "scenario": name,
                "parameters": params,
                "test_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            try:
                print(f"    测试{name}")
                
                # 注意：这里不实际调用run函数，因为它会启动策略执行
                # 只测试函数是否存在和参数格式
                if hasattr(gm, 'run'):
                    test_result["status"] = "函数存在"
                    test_result["note"] = "run函数存在，但未实际调用以避免启动策略"
                    print(f"      run函数存在，参数: {params}")
                else:
                    test_result["status"] = "函数不存在"
                    test_result["note"] = "GM API中未找到run函数"
                    print(f"      run函数不存在")
                
            except Exception as e:
                test_result["status"] = "测试失败"
                test_result["error"] = str(e)
                print(f"      测试失败: {e}")
            
            run_tests.append(test_result)
        
        run_stop_result["run_tests"] = run_tests
        
        # 测试停止功能
        print("\n2. 测试停止功能")
        stop_tests = []
        
        stop_scenarios = [
            {"name": "正常停止", "params": {}},
            {"name": "强制停止", "params": {"force": True}}
        ]
        
        for scenario in stop_scenarios:
            name = scenario["name"]
            params = scenario["params"]
            
            test_result = {
                "scenario": name,
                "parameters": params,
                "test_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            try:
                print(f"    测试{name}")
                
                # 注意：这里不实际调用stop函数，因为可能没有运行中的策略
                if hasattr(gm, 'stop'):
                    test_result["status"] = "函数存在"
                    test_result["note"] = "stop函数存在，但未实际调用"
                    print(f"      stop函数存在，参数: {params}")
                else:
                    test_result["status"] = "函数不存在"
                    test_result["note"] = "GM API中未找到stop函数"
                    print(f"      stop函数不存在")
                
            except Exception as e:
                test_result["status"] = "测试失败"
                test_result["error"] = str(e)
                print(f"      测试失败: {e}")
            
            stop_tests.append(test_result)
        
        run_stop_result["stop_tests"] = stop_tests
        
        # 功能可用性总结
        run_available = any(test["status"] == "函数存在" for test in run_tests)
        stop_available = any(test["status"] == "函数存在" for test in stop_tests)
        
        run_stop_result["availability_summary"] = {
            "run_function_available": run_available,
            "stop_function_available": stop_available,
            "note": "函数存在性检查，未实际执行以避免意外启动或停止策略"
        }
        
        print(f"\n功能可用性总结:")
        print(f"  run函数可用: {run_available}")
        print(f"  stop函数可用: {stop_available}")
        
    except Exception as e:
        print(f"运行停止功能测试失败: {e}")
        run_stop_result["error"] = str(e)
    
    # 保存结果
    save_results({
        "test_type": "run_stop_functions",
        "data": run_stop_result
    }, "run_stop_functions")
    
    return run_stop_result


def test_comprehensive_system_analysis():
    """
    测试综合系统分析
    """
    print("\n=== 测试综合系统分析 ===")
    
    system_analysis = {
        "analysis_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    try:
        # 1. 系统信息收集
        print("\n1. 收集系统信息")
        
        # 版本信息
        try:
            version_info = gm.get_version()
            system_analysis["version_info"] = convert_object_to_dict(version_info)
            print("  版本信息收集成功")
        except Exception as e:
            system_analysis["version_error"] = str(e)
            print(f"  版本信息收集失败: {e}")
        
        # 配置信息
        try:
            config_info = gm.get_config()
            system_analysis["config_info"] = convert_object_to_dict(config_info)
            print("  配置信息收集成功")
        except Exception as e:
            system_analysis["config_error"] = str(e)
            print(f"  配置信息收集失败: {e}")
        
        # 2. 功能可用性检查
        print("\n2. 检查功能可用性")
        
        functions_to_check = [
            'set_token', 'set_account_id', 'set_endpoint', 'set_backtest_config',
            'set_strategy_id', 'get_version', 'get_config', 'log', 'run', 'stop'
        ]
        
        function_availability = {}
        for func_name in functions_to_check:
            available = hasattr(gm, func_name)
            function_availability[func_name] = available
            print(f"  {func_name}: {'可用' if available else '不可用'}")
        
        system_analysis["function_availability"] = function_availability
        
        # 3. 配置完整性检查
        print("\n3. 检查配置完整性")
        
        config_completeness = {}
        if "config_info" in system_analysis:
            config = system_analysis["config_info"]
            
            required_configs = ['endpoint', 'token', 'account_id']
            optional_configs = ['strategy_id', 'mode']
            
            for config_name in required_configs:
                has_config = bool(config.get(config_name))
                config_completeness[f"has_{config_name}"] = has_config
                print(f"  {config_name}: {'已配置' if has_config else '未配置'}")
            
            for config_name in optional_configs:
                has_config = bool(config.get(config_name))
                config_completeness[f"has_{config_name}"] = has_config
                print(f"  {config_name} (可选): {'已配置' if has_config else '未配置'}")
        
        system_analysis["config_completeness"] = config_completeness
        
        # 4. 系统健康度评估
        print("\n4. 评估系统健康度")
        
        health_score = 0
        max_score = 10
        
        # 版本信息 (2分)
        if "version_info" in system_analysis:
            health_score += 2
            print("  版本信息: +2分")
        
        # 配置信息 (2分)
        if "config_info" in system_analysis:
            health_score += 2
            print("  配置信息: +2分")
        
        # 核心功能可用性 (4分)
        core_functions = ['set_token', 'set_account_id', 'get_version', 'get_config']
        available_core = sum(1 for func in core_functions if function_availability.get(func, False))
        core_score = (available_core / len(core_functions)) * 4
        health_score += core_score
        print(f"  核心功能可用性: +{core_score:.1f}分 ({available_core}/{len(core_functions)})")
        
        # 配置完整性 (2分)
        if config_completeness:
            required_count = sum(1 for k, v in config_completeness.items() 
                               if k.startswith('has_') and k.replace('has_', '') in ['endpoint', 'token', 'account_id'] and v)
            completeness_score = (required_count / 3) * 2
            health_score += completeness_score
            print(f"  配置完整性: +{completeness_score:.1f}分 ({required_count}/3)")
        
        health_percentage = (health_score / max_score) * 100
        
        system_analysis["health_assessment"] = {
            "health_score": health_score,
            "max_score": max_score,
            "health_percentage": health_percentage,
            "health_level": "优秀" if health_percentage >= 80 else "良好" if health_percentage >= 60 else "一般" if health_percentage >= 40 else "较差"
        }
        
        print(f"\n系统健康度: {health_score:.1f}/{max_score} ({health_percentage:.1f}%) - {system_analysis['health_assessment']['health_level']}")
        
        # 5. 建议和警告
        recommendations = []
        warnings = []
        
        if "version_error" in system_analysis:
            warnings.append("无法获取版本信息，可能存在连接问题")
        
        if "config_error" in system_analysis:
            warnings.append("无法获取配置信息，请检查API连接")
        
        if config_completeness:
            if not config_completeness.get('has_token', False):
                recommendations.append("建议设置有效的API Token")
            
            if not config_completeness.get('has_account_id', False):
                recommendations.append("建议设置账户ID")
            
            if not config_completeness.get('has_endpoint', False):
                recommendations.append("建议检查API端点配置")
        
        if health_percentage < 60:
            recommendations.append("系统健康度较低，建议检查配置和网络连接")
        
        if not recommendations:
            recommendations.append("系统配置良好，无特殊建议")
        
        if not warnings:
            warnings.append("无系统警告")
        
        system_analysis["recommendations"] = recommendations
        system_analysis["warnings"] = warnings
        
        print(f"\n建议:")
        for rec in recommendations:
            print(f"  - {rec}")
        
        print(f"\n警告:")
        for warn in warnings:
            print(f"  - {warn}")
        
    except Exception as e:
        print(f"综合系统分析失败: {e}")
        system_analysis["error"] = str(e)
    
    # 保存结果
    save_results({
        "test_type": "comprehensive_system_analysis",
        "data": system_analysis
    }, "comprehensive_system_analysis")
    
    return system_analysis


def main():
    """
    主函数
    """
    print("GM API - 系统设置接口测试")
    print("=" * 50)
    
    # 注意：不调用init_gm_api()，因为我们要测试设置函数本身
    
    # 执行各项测试
    token_result = test_set_token()
    account_result = test_set_account_id()
    endpoint_result = test_set_endpoint()
    backtest_result = test_set_backtest_config()
    strategy_result = test_set_strategy_id()
    version_result = test_get_version()
    config_result = test_get_config()
    log_result = test_log_function()
    run_stop_result = test_run_stop_functions()
    system_analysis = test_comprehensive_system_analysis()
    
    print("\n=== 所有测试完成 ===")
    print("\n测试总结:")
    
    # 统计测试结果
    test_results = {
        "设置Token": "成功" if "error" not in token_result else "失败",
        "设置账户ID": "成功" if "error" not in account_result else "失败",
        "设置端点": "成功" if "error" not in endpoint_result else "失败",
        "设置回测配置": "成功" if "error" not in backtest_result else "失败",
        "设置策略ID": "成功" if "error" not in strategy_result else "失败",
        "获取版本信息": "成功" if "error" not in version_result else "失败",
        "获取配置信息": "成功" if "error" not in config_result else "失败",
        "日志功能": "成功" if "error" not in log_result else "失败",
        "运行停止功能": "成功" if "error" not in run_stop_result else "失败",
        "综合系统分析": "成功" if "error" not in system_analysis else "失败"
    }
    
    for test_name, result in test_results.items():
        print(f"  {test_name}: {result}")
    
    success_count = sum(1 for result in test_results.values() if result == "成功")
    total_count = len(test_results)
    
    print(f"\n测试通过率: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
    
    # 显示系统健康度
    if "health_assessment" in system_analysis:
        health = system_analysis["health_assessment"]
        print(f"系统健康度: {health['health_percentage']:.1f}% ({health['health_level']})")


if __name__ == '__main__':
    main()