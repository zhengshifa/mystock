"""
调度系统启动脚本
启动数据同步调度器
"""
import asyncio
import logging
import signal
import sys
import os
from src.scheduler import SchedulerService
from src.database import mongodb_client
from src.config import settings


def setup_logging():
    """设置日志"""
    # 获取项目根目录
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    log_file = os.path.join(project_root, 'logs', 'scheduler.log')
    
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file, encoding='utf-8')
        ]
    )


class SchedulerApp:
    """调度应用"""
    
    def __init__(self):
        """初始化应用"""
        self.logger = logging.getLogger(__name__)
        self.scheduler_service = SchedulerService()
        self.running = False
    
    async def start(self):
        """启动应用"""
        try:
            self.logger.info("启动调度系统...")
            
            # 连接数据库
            connected = await mongodb_client.connect()
            if not connected:
                self.logger.error("数据库连接失败，退出")
                return
            
            # 启动调度器
            await self.scheduler_service.start_scheduler()
            
            self.running = True
            self.logger.info("调度系统启动成功")
            
            # 打印状态信息
            self._print_status()
            
            # 保持运行
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            self.logger.error(f"启动调度系统失败: {e}")
        finally:
            await self.stop()
    
    async def stop(self):
        """停止应用"""
        if self.running:
            self.logger.info("停止调度系统...")
            
            # 停止调度器
            self.scheduler_service.stop_scheduler()
            
            # 断开数据库连接
            await mongodb_client.disconnect()
            
            self.running = False
            self.logger.info("调度系统已停止")
    
    def _print_status(self):
        """打印状态信息"""
        print("\n" + "="*60)
        print("调度系统状态")
        print("="*60)
        print(f"配置的股票: {settings.test_symbols}")
        print(f"同步间隔: {settings.sync_interval_minutes} 分钟")
        print(f"实时同步间隔: {settings.realtime_interval_seconds} 秒")
        print(f"历史同步时间: {settings.history_sync_time}")
        print(f"交易时间: 上午 {settings.trading_morning_start}-{settings.trading_morning_end}, 下午 {settings.trading_afternoon_start}-{settings.trading_afternoon_end}")
        print(f"MongoDB: {settings.mongodb_database}")
        print("="*60)
        print("调度系统正在运行，按 Ctrl+C 停止")
        print("="*60)


def signal_handler(signum, frame):
    """信号处理器"""
    print("\n收到停止信号，正在关闭...")
    sys.exit(0)


async def main():
    """主函数"""
    # 设置信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 设置日志
    setup_logging()
    
    # 验证配置
    if not settings.validate():
        print("❌ 配置验证失败!")
        return
    
    # 创建并启动应用
    app = SchedulerApp()
    await app.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n用户中断，程序退出")
    except Exception as e:
        print(f"程序异常退出: {e}")
        logging.error(f"程序异常退出: {e}")
