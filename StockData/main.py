#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
掘金量化股票数据管理系统 - 主程序入口

功能:
- 实时数据同步 (30秒间隔)
- 历史数据增量同步
- 多种股票数据类型支持
- MongoDB数据存储
- 配置解耦
- 日志系统
- 调度系统

Author: Stock Data System
Date: 2024
"""

import asyncio
import signal
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.application import StockDataApplication
from src.utils.logger import setup_logger
from src.config.config_manager import ConfigManager


class StockDataMain:
    """股票数据系统主程序"""
    
    def __init__(self):
        self.app = None
        self.logger = None
        self.config_manager = None
        self._shutdown_event = asyncio.Event()
    
    async def initialize(self):
        """初始化系统"""
        try:
            # 初始化配置管理器
            self.config_manager = ConfigManager()
            await self.config_manager.load_config()
            
            # 初始化日志系统
            self.logger = setup_logger(self.config_manager.get_config())
            self.logger.info("股票数据管理系统启动中...")
            
            # 初始化应用程序
            self.app = StockDataApplication(self.config_manager)
            await self.app.initialize()
            
            self.logger.info("系统初始化完成")
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"系统初始化失败: {e}")
            else:
                print(f"系统初始化失败: {e}")
            raise
    
    async def start(self):
        """启动系统"""
        try:
            self.logger.info("启动股票数据管理系统")
            
            # 启动应用程序
            await self.app.start()
            
            self.logger.info("系统启动成功，等待数据同步任务...")
            
            # 等待关闭信号
            await self._shutdown_event.wait()
            
        except Exception as e:
            self.logger.error(f"系统运行异常: {e}")
            raise
    
    async def shutdown(self):
        """关闭系统"""
        try:
            self.logger.info("正在关闭股票数据管理系统...")
            
            if self.app:
                await self.app.shutdown()
            
            self.logger.info("系统已安全关闭")
            
        except Exception as e:
            self.logger.error(f"系统关闭异常: {e}")
    
    def signal_handler(self, signum, frame):
        """信号处理器"""
        if self.logger:
            self.logger.info(f"接收到信号 {signum}，准备关闭系统")
        self._shutdown_event.set()


async def main():
    """主函数"""
    stock_main = StockDataMain()
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, stock_main.signal_handler)
    signal.signal(signal.SIGTERM, stock_main.signal_handler)
    
    try:
        # 初始化系统
        await stock_main.initialize()
        
        # 启动系统
        await stock_main.start()
        
    except KeyboardInterrupt:
        print("\n接收到中断信号，正在关闭系统...")
    except Exception as e:
        print(f"系统运行异常: {e}")
        sys.exit(1)
    finally:
        # 关闭系统
        await stock_main.shutdown()


if __name__ == "__main__":
    # 设置事件循环策略（Windows兼容性）
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # 运行主程序
    asyncio.run(main())