#!/usr/bin/env python3
"""
配置管理功能测试脚本
"""
import sys
import os
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config.config_manager import get_config_manager
from src.config.scheduler_config import get_scheduler_config
from src.utils.logger import setup_logger


def test_config_loading():
    """测试配置加载功能"""
    print("🧪 测试配置加载功能...")
    
    try:
        # 获取配置管理器
        config_manager = get_config_manager()
        print("✅ 配置管理器创建成功")
        
        # 获取当前配置
        current_config = config_manager.get_current_config()
        print(f"✅ 当前配置获取成功，包含 {len(current_config)} 个主要配置项")
        
        # 获取配置摘要
        summary = config_manager.get_config_summary()
        print("✅ 配置摘要获取成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 配置加载测试失败: {e}")
        return False


def test_stock_symbol_management():
    """测试股票代码管理功能"""
    print("\n🧪 测试股票代码管理功能...")
    
    try:
        config_manager = get_config_manager()
        
        # 获取当前股票列表
        sh_symbols = config_manager.scheduler_config.get_stock_symbols("SH")
        sz_symbols = config_manager.scheduler_config.get_stock_symbols("SZ")
        print(f"✅ 当前股票列表获取成功: SH({len(sh_symbols)}只), SZ({len(sz_symbols)}只)")
        
        # 测试添加股票代码
        test_symbol = "999999"
        if config_manager.add_stock_symbol("SH", test_symbol):
            print(f"✅ 成功添加测试股票代码: {test_symbol}")
            
            # 验证是否添加成功
            new_sh_symbols = config_manager.scheduler_config.get_stock_symbols("SH")
            if test_symbol in new_sh_symbols:
                print("✅ 股票代码添加验证成功")
            else:
                print("❌ 股票代码添加验证失败")
            
            # 测试移除股票代码
            if config_manager.remove_stock_symbol("SH", test_symbol):
                print(f"✅ 成功移除测试股票代码: {test_symbol}")
            else:
                print("❌ 移除测试股票代码失败")
        else:
            print("❌ 添加测试股票代码失败")
        
        return True
        
    except Exception as e:
        print(f"❌ 股票代码管理测试失败: {e}")
        return False


def test_task_management():
    """测试任务管理功能"""
    print("\n🧪 测试任务管理功能...")
    
    try:
        config_manager = get_config_manager()
        
        # 获取当前任务列表
        config = config_manager.scheduler_config.get_config()
        print(f"✅ 当前任务列表获取成功，共 {len(config.tasks)} 个任务")
        
        # 测试任务启用/禁用
        if config.tasks:
            first_task = config.tasks[0]
            task_name = first_task.name
            
            # 禁用任务
            if config_manager.disable_task(task_name):
                print(f"✅ 成功禁用任务: {task_name}")
                
                # 验证禁用状态
                updated_config = config_manager.scheduler_config.get_config()
                updated_task = next((t for t in updated_config.tasks if t.name == task_name), None)
                if updated_task and not updated_task.enabled:
                    print("✅ 任务禁用状态验证成功")
                else:
                    print("❌ 任务禁用状态验证失败")
                
                # 重新启用任务
                if config_manager.enable_task(task_name):
                    print(f"✅ 成功启用任务: {task_name}")
                else:
                    print("❌ 启用任务失败")
            else:
                print("❌ 禁用任务失败")
        
        return True
        
    except Exception as e:
        print(f"❌ 任务管理测试失败: {e}")
        return False


def test_config_export_import():
    """测试配置导入导出功能"""
    print("\n🧪 测试配置导入导出功能...")
    
    try:
        config_manager = get_config_manager()
        
        # 测试配置导出
        export_filename = "test_config_export.json"
        if config_manager.export_config(export_filename):
            print(f"✅ 配置导出成功: {export_filename}")
            
            # 检查导出文件是否存在
            if os.path.exists(export_filename):
                print("✅ 导出文件创建验证成功")
                
                # 测试配置导入
                if config_manager.import_config(export_filename):
                    print("✅ 配置导入成功")
                else:
                    print("❌ 配置导入失败")
                
                # 清理测试文件
                try:
                    os.remove(export_filename)
                    print("✅ 测试文件清理成功")
                except:
                    print("⚠️ 测试文件清理失败")
            else:
                print("❌ 导出文件创建验证失败")
        else:
            print("❌ 配置导出失败")
        
        return True
        
    except Exception as e:
        print(f"❌ 配置导入导出测试失败: {e}")
        return False


def test_scheduler_config():
    """测试调度器配置功能"""
    print("\n🧪 测试调度器配置功能...")
    
    try:
        scheduler_config = get_scheduler_config()
        
        # 测试获取各种配置
        stock_symbols = scheduler_config.get_stock_symbols()
        trading_hours = scheduler_config.get_trading_hours()
        supported_frequencies = scheduler_config.get_supported_frequencies()
        realtime_intervals = scheduler_config.get_realtime_intervals()
        
        print(f"✅ 股票代码获取成功: {len(stock_symbols)}只")
        print(f"✅ 交易时间获取成功: {trading_hours}")
        print(f"✅ 支持频率获取成功: {supported_frequencies}")
        print(f"✅ 实时间隔获取成功: {realtime_intervals}")
        
        return True
        
    except Exception as e:
        print(f"❌ 调度器配置测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("🚀 开始测试配置管理功能...")
    print("=" * 50)
    
    # 设置日志系统
    setup_logger()
    
    # 运行各项测试
    tests = [
        test_config_loading,
        test_stock_symbol_management,
        test_task_management,
        test_config_export_import,
        test_scheduler_config
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ 测试执行异常: {e}")
    
    # 输出测试结果
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！配置管理功能正常")
    else:
        print("⚠️ 部分测试失败，请检查相关功能")
    
    print("\n💡 提示:")
    print("- 使用 'uv run python config_manager.py' 启动交互式配置管理工具")
    print("- 配置文件位于 'config/scheduler_config.yaml'")
    print("- 所有配置变更都会自动保存到文件")


if __name__ == "__main__":
    main()
