#!/usr/bin/env python3
"""
配置管理命令行工具
提供交互式的调度配置管理功能
"""
import sys
import os
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config.config_manager import get_config_manager
from src.utils.logger import setup_logger


class ConfigManagerCLI:
    """配置管理命令行界面"""
    
    def __init__(self):
        """初始化命令行界面"""
        self.config_manager = get_config_manager()
        self.running = True
    
    def run(self):
        """运行命令行界面"""
        print("🚀 股票数据收集器配置管理工具")
        print("=" * 50)
        
        while self.running:
            try:
                self._show_menu()
                choice = input("\n请选择操作 (输入数字): ").strip()
                self._handle_choice(choice)
            except KeyboardInterrupt:
                print("\n\n👋 再见！")
                break
            except Exception as e:
                print(f"❌ 操作失败: {e}")
    
    def _show_menu(self):
        """显示主菜单"""
        print("\n📋 主菜单:")
        print("1. 查看当前配置")
        print("2. 管理股票代码")
        print("3. 管理任务调度")
        print("4. 管理数据收集")
        print("5. 管理交易时间")
        print("6. 导入/导出配置")
        print("7. 重新加载配置")
        print("0. 退出")
    
    def _handle_choice(self, choice: str):
        """处理用户选择"""
        if choice == "1":
            self._show_current_config()
        elif choice == "2":
            self._manage_stock_symbols()
        elif choice == "3":
            self._manage_task_schedule()
        elif choice == "4":
            self._manage_data_collection()
        elif choice == "5":
            self._manage_trading_hours()
        elif choice == "6":
            self._manage_import_export()
        elif choice == "7":
            self._reload_config()
        elif choice == "0":
            self.running = False
        else:
            print("❌ 无效选择，请重新输入")
    
    def _show_current_config(self):
        """显示当前配置"""
        print("\n📊 当前配置信息:")
        print("-" * 30)
        
        summary = self.config_manager.get_config_summary()
        
        for category, details in summary.items():
            print(f"\n{category}:")
            if isinstance(details, dict):
                for key, value in details.items():
                    print(f"  {key}: {value}")
            else:
                print(f"  {details}")
    
    def _manage_stock_symbols(self):
        """管理股票代码"""
        while True:
            print("\n📈 股票代码管理:")
            print("1. 查看股票列表")
            print("2. 添加股票代码")
            print("3. 移除股票代码")
            print("4. 返回主菜单")
            
            choice = input("请选择操作: ").strip()
            
            if choice == "1":
                self._show_stock_symbols()
            elif choice == "2":
                self._add_stock_symbol()
            elif choice == "3":
                self._remove_stock_symbol()
            elif choice == "4":
                break
            else:
                print("❌ 无效选择")
    
    def _show_stock_symbols(self):
        """显示股票代码列表"""
        print("\n📋 股票代码列表:")
        
        sh_symbols = self.config_manager.scheduler_config.get_stock_symbols("SH")
        sz_symbols = self.config_manager.scheduler_config.get_stock_symbols("SZ")
        
        print(f"上海市场 ({len(sh_symbols)}只):")
        for symbol in sh_symbols:
            print(f"  {symbol}")
        
        print(f"\n深圳市场 ({len(sz_symbols)}只):")
        for symbol in sz_symbols:
            print(f"  {symbol}")
    
    def _add_stock_symbol(self):
        """添加股票代码"""
        print("\n➕ 添加股票代码:")
        
        market = input("选择市场 (SH/SZ): ").strip().upper()
        if market not in ["SH", "SZ"]:
            print("❌ 无效的市场选择")
            return
        
        symbol = input("输入股票代码 (6位数字): ").strip()
        if len(symbol) != 6 or not symbol.isdigit():
            print("❌ 无效的股票代码格式")
            return
        
        if self.config_manager.add_stock_symbol(market, symbol):
            print(f"✅ 成功添加股票代码: {market}{symbol}")
        else:
            print("❌ 添加股票代码失败")
    
    def _remove_stock_symbol(self):
        """移除股票代码"""
        print("\n➖ 移除股票代码:")
        
        market = input("选择市场 (SH/SZ): ").strip().upper()
        if market not in ["SH", "SZ"]:
            print("❌ 无效的市场选择")
            return
        
        symbol = input("输入股票代码: ").strip()
        
        if self.config_manager.remove_stock_symbol(market, symbol):
            print(f"✅ 成功移除股票代码: {market}{symbol}")
        else:
            print("❌ 移除股票代码失败")
    
    def _manage_task_schedule(self):
        """管理任务调度"""
        while True:
            print("\n⏰ 任务调度管理:")
            print("1. 查看任务列表")
            print("2. 启用任务")
            print("3. 禁用任务")
            print("4. 修改任务间隔")
            print("5. 返回主菜单")
            
            choice = input("请选择操作: ").strip()
            
            if choice == "1":
                self._show_task_list()
            elif choice == "2":
                self._enable_task()
            elif choice == "3":
                self._disable_task()
            elif choice == "4":
                self._modify_task_interval()
            elif choice == "5":
                break
            else:
                print("❌ 无效选择")
    
    def _show_task_list(self):
        """显示任务列表"""
        print("\n📋 任务列表:")
        
        config = self.config_manager.scheduler_config.get_config()
        for i, task in enumerate(config.tasks, 1):
            status = "✅ 启用" if task.enabled else "❌ 禁用"
            print(f"{i}. {task.name} - {status}")
            print(f"   描述: {task.description}")
            print(f"   间隔: {task.interval_value} {task.interval_type}")
            if task.at_time:
                print(f"   时间: {task.at_time}")
            print()
    
    def _enable_task(self):
        """启用任务"""
        print("\n✅ 启用任务:")
        
        task_name = input("输入任务名称: ").strip()
        if self.config_manager.enable_task(task_name):
            print(f"✅ 成功启用任务: {task_name}")
        else:
            print("❌ 启用任务失败")
    
    def _disable_task(self):
        """禁用任务"""
        print("\n❌ 禁用任务:")
        
        task_name = input("输入任务名称: ").strip()
        if self.config_manager.disable_task(task_name):
            print(f"✅ 成功禁用任务: {task_name}")
        else:
            print("❌ 禁用任务失败")
    
    def _modify_task_interval(self):
        """修改任务间隔"""
        print("\n⏱️ 修改任务间隔:")
        
        task_name = input("输入任务名称: ").strip()
        interval_value = input("输入新的间隔值: ").strip()
        
        try:
            interval_value = int(interval_value)
            if self.config_manager.update_task_schedule(task_name, interval_value=interval_value):
                print(f"✅ 成功修改任务间隔: {task_name}")
            else:
                print("❌ 修改任务间隔失败")
        except ValueError:
            print("❌ 间隔值必须是数字")
    
    def _manage_data_collection(self):
        """管理数据收集"""
        while True:
            print("\n📊 数据收集管理:")
            print("1. 查看数据收集配置")
            print("2. 修改实时数据间隔")
            print("3. 修改支持的数据频率")
            print("4. 返回主菜单")
            
            choice = input("请选择操作: ").strip()
            
            if choice == "1":
                self._show_data_collection_config()
            elif choice == "2":
                self._modify_realtime_intervals()
            elif choice == "3":
                self._modify_supported_frequencies()
            elif choice == "4":
                break
            else:
                print("❌ 无效选择")
    
    def _show_data_collection_config(self):
        """显示数据收集配置"""
        print("\n📊 数据收集配置:")
        
        config = self.config_manager.scheduler_config.get_config()
        dc = config.data_collection
        
        print(f"Tick数据间隔: {dc.realtime_tick_interval}秒")
        print(f"Bar数据间隔: {dc.realtime_bar_interval}秒")
        print(f"支持的数据频率: {dc.supported_frequencies}")
        print(f"每日同步时间: {dc.daily_sync_times}")
        print(f"市场状态检查间隔: {dc.market_status_check_interval}分钟")
    
    def _modify_realtime_intervals(self):
        """修改实时数据间隔"""
        print("\n⏱️ 修改实时数据间隔:")
        
        try:
            tick_interval = input("输入Tick数据间隔(秒，回车跳过): ").strip()
            bar_interval = input("输入Bar数据间隔(秒，回车跳过): ").strip()
            
            tick_interval = int(tick_interval) if tick_interval else None
            bar_interval = int(bar_interval) if bar_interval else None
            
            if self.config_manager.update_realtime_intervals(tick_interval, bar_interval):
                print("✅ 成功修改实时数据间隔")
            else:
                print("❌ 修改实时数据间隔失败")
        except ValueError:
            print("❌ 间隔值必须是数字")
    
    def _modify_supported_frequencies(self):
        """修改支持的数据频率"""
        print("\n📈 修改支持的数据频率:")
        print("当前支持的频率: 60s, 300s, 900s, 1d")
        
        frequencies_input = input("输入新的频率列表(用逗号分隔): ").strip()
        if frequencies_input:
            frequencies = [f.strip() for f in frequencies_input.split(",")]
            if self.config_manager.update_supported_frequencies(frequencies):
                print("✅ 成功修改支持的数据频率")
            else:
                print("❌ 修改支持的数据频率失败")
    
    def _manage_trading_hours(self):
        """管理交易时间"""
        print("\n🕐 交易时间管理:")
        
        current_hours = self.config_manager.scheduler_config.get_trading_hours()
        print(f"当前交易时间: {current_hours}")
        
        print("\n修改交易时间:")
        try:
            morning_start = input("上午开盘时间 (HH:MM): ").strip()
            morning_end = input("上午收盘时间 (HH:MM): ").strip()
            afternoon_start = input("下午开盘时间 (HH:MM): ").strip()
            afternoon_end = input("下午收盘时间 (HH:MM): ").strip()
            
            new_trading_hours = {
                "morning": [morning_start, morning_end],
                "afternoon": [afternoon_start, afternoon_end]
            }
            
            if self.config_manager.update_trading_hours(new_trading_hours):
                print("✅ 成功修改交易时间")
            else:
                print("❌ 修改交易时间失败")
        except Exception as e:
            print(f"❌ 输入格式错误: {e}")
    
    def _manage_import_export(self):
        """管理配置导入导出"""
        while True:
            print("\n📁 配置导入导出:")
            print("1. 导出配置")
            print("2. 导入配置")
            print("3. 返回主菜单")
            
            choice = input("请选择操作: ").strip()
            
            if choice == "1":
                self._export_config()
            elif choice == "2":
                self._import_config()
            elif choice == "3":
                break
            else:
                print("❌ 无效选择")
    
    def _export_config(self):
        """导出配置"""
        print("\n📤 导出配置:")
        
        filename = input("输入导出文件名 (回车使用默认名称): ").strip()
        if not filename:
            filename = None
        
        if self.config_manager.export_config(filename):
            print("✅ 配置导出成功")
        else:
            print("❌ 配置导出失败")
    
    def _import_config(self):
        """导入配置"""
        print("\n📥 导入配置:")
        
        filename = input("输入导入文件名: ").strip()
        if not filename:
            print("❌ 文件名不能为空")
            return
        
        if not os.path.exists(filename):
            print("❌ 文件不存在")
            return
        
        if self.config_manager.import_config(filename):
            print("✅ 配置导入成功")
        else:
            print("❌ 配置导入失败")
    
    def _reload_config(self):
        """重新加载配置"""
        print("\n🔄 重新加载配置:")
        
        if self.config_manager.reload_config():
            print("✅ 配置重新加载成功")
        else:
            print("❌ 配置重新加载失败")


def main():
    """主函数"""
    try:
        # 设置日志系统
        setup_logger()
        
        # 创建并运行命令行界面
        cli = ConfigManagerCLI()
        cli.run()
        
    except Exception as e:
        print(f"❌ 程序运行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
