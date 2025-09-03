#!/usr/bin/env python3
"""
股票数据同步系统启动脚本
提供统一的入口点来运行各种功能
"""
import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from main import StockDataApp


def print_usage():
    """打印使用说明"""
    print("""
股票数据同步系统启动脚本

使用方法:
  uv run python start.py [模式] [选项]

可用模式:
  scheduler      调度模式 - 启动数据同步调度器 (默认)
  interactive    交互模式 - 手动操作界面
  test          测试模式 - 运行系统测试
  sync          同步模式 - 手动同步数据
  query         查询模式 - 查询数据统计
  symbols       标的信息模式 - 查询标的基本信息
  symbol-sync   标的信息同步模式 - 手动同步标的基本信息
  auto          自动模式 - 自动执行核心功能

测试脚本:
  uv run python start.py test-api         运行API测试
  uv run python start.py test-scheduler   运行调度器测试
  uv run python start.py test-multi       运行多频率测试
  uv run python start.py test-advanced    运行高级测试

工具脚本:
  uv run python start.py query-tool       运行数据查询工具
  uv run python start.py scheduler-tool   运行调度器工具
  uv run python start.py symbol-tool      运行标的信息查询工具

示例:
  uv run python start.py                   # 默认启动调度器
  uv run python start.py interactive       # 交互模式
  uv run python start.py scheduler         # 启动调度器
  uv run python start.py test              # 运行测试
  uv run python start.py test-api          # 运行API测试
""")


async def run_test_script(script_name: str):
    """运行测试脚本"""
    script_path = project_root / "scripts" / "tests" / f"{script_name}.py"
    
    if not script_path.exists():
        print(f"❌ 测试脚本不存在: {script_path}")
        return
    
    print(f"🚀 运行测试脚本: {script_name}")
    print("=" * 60)
    
    # 动态导入并运行脚本
    import importlib.util
    spec = importlib.util.spec_from_file_location(script_name, script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    # 如果脚本有main函数，则调用它
    if hasattr(module, 'main'):
        if asyncio.iscoroutinefunction(module.main):
            await module.main()
        else:
            module.main()


async def run_tool_script(script_name: str):
    """运行工具脚本"""
    script_path = project_root / "scripts" / "tools" / f"{script_name}.py"
    
    if not script_path.exists():
        print(f"❌ 工具脚本不存在: {script_path}")
        return
    
    print(f"🔧 运行工具脚本: {script_name}")
    print("=" * 60)
    
    # 动态导入并运行脚本
    import importlib.util
    spec = importlib.util.spec_from_file_location(script_name, script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    # 如果脚本有main函数，则调用它
    if hasattr(module, 'main'):
        if asyncio.iscoroutinefunction(module.main):
            await module.main()
        else:
            module.main()


async def main():
    """主函数"""
    if len(sys.argv) < 2:
        # 默认运行调度模式
        app = StockDataApp()
        try:
            app.setup_logging()
            if await app.initialize():
                print("🚀 启动股票数据同步调度系统...")
                await app.run_scheduler_mode()
            else:
                print("❌ 应用初始化失败!")
        finally:
            await app.cleanup()
        return
    
    command = sys.argv[1].lower()
    
    if command in ['-h', '--help', 'help']:
        print_usage()
        return
    
    # 创建应用实例
    app = StockDataApp()
    
    try:
        # 设置日志
        app.setup_logging()
        
        # 初始化应用
        if not await app.initialize():
            print("❌ 应用初始化失败!")
            return
        
        print("✅ 应用初始化成功!")
        
        if command == 'interactive':
            await app.run_interactive_mode()
        elif command == 'scheduler':
            await app.run_scheduler_mode()
        elif command == 'test':
            await app.test_api_connection()
            await app.test_database_connection()
            await app.get_system_status()
        elif command == 'sync':
            await app.manual_sync_data()
        elif command == 'query':
            await app.query_data()
        elif command == 'symbols':
            await app.query_symbol_infos()
        elif command == 'symbol-sync':
            await app.manual_sync_symbol_infos()
        elif command == 'auto':
            await app.run_auto_mode()
        elif command == 'test-api':
            await run_test_script('test_gm_api')
        elif command == 'test-scheduler':
            await run_test_script('test_scheduler')
        elif command == 'test-multi':
            await run_test_script('test_multi_frequency')
        elif command == 'test-advanced':
            await run_test_script('advanced_test')
        elif command == 'query-tool':
            await run_tool_script('query_data')
        elif command == 'scheduler-tool':
            await run_tool_script('start_scheduler')
        elif command == 'symbol-tool':
            await run_tool_script('get_symbol_infos')
        else:
            print(f"❌ 未知命令: {command}")
            print_usage()
    
    except Exception as e:
        print(f"❌ 程序异常: {e}")
        app.logger.error(f"程序异常: {e}")
    
    finally:
        # 清理资源
        await app.cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n用户中断，程序退出")
    except Exception as e:
        print(f"程序异常退出: {e}")