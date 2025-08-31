#!/usr/bin/env python3
"""NewsNow Python 版本主入口文件"""

import asyncio
import signal
import sys
from pathlib import Path
from typing import Optional

# 项目根目录路径
project_root = Path(__file__).parent

from utils.config import get_config
from utils.logger import setup_logger, get_logger
from database.mongodb import init_mongodb, close_mongodb
from core.scheduler import NewsScheduler
from sources import get_available_sources, get_all_sources_info

# 设置日志
setup_logger()
logger = get_logger(__name__)

# 全局调度器实例
scheduler: Optional[NewsScheduler] = None


def signal_handler(signum, frame):
    """信号处理器"""
    logger.info(f"接收到信号 {signum}，正在关闭应用...")
    if scheduler:
        asyncio.create_task(shutdown())
    else:
        sys.exit(0)


async def shutdown():
    """优雅关闭应用"""
    global scheduler
    
    logger.info("正在关闭应用...")
    
    # 停止调度器
    if scheduler:
        try:
            await scheduler.stop()
            logger.info("调度器已停止")
        except Exception as e:
            logger.error(f"停止调度器失败: {e}")
    
    # 关闭数据库连接
    try:
        await close_mongodb()
        logger.info("数据库连接已关闭")
    except Exception as e:
        logger.error(f"关闭数据库连接失败: {e}")
    
    logger.info("应用已关闭")
    sys.exit(0)


async def init_app():
    """初始化应用"""
    global scheduler
    
    config = get_config()
    
    logger.info("正在初始化 NewsNow Python 版本...")
    logger.info(f"运行模式: {'开发' if config.is_debug() else '生产'}")
    
    # 初始化数据库
    try:
        await init_mongodb()
        logger.info("数据库连接已建立")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise
    
    # 显示可用的新闻源
    sources = get_available_sources()
    logger.info(f"已加载 {len(sources)} 个新闻源: {', '.join(sources)}")
    
    # 创建调度器
    try:
        scheduler = NewsScheduler()
        logger.info("调度器已创建")
    except Exception as e:
        logger.error(f"创建调度器失败: {e}")
        raise
    
    logger.info("应用初始化完成")


async def start_app():
    """启动应用"""
    global scheduler
    
    # 初始化应用
    await init_app()
    
    # 启动调度器
    try:
        await scheduler.start()
        logger.info("调度器已启动")
        
        # 显示调度器状态
        status = scheduler.get_status()
        logger.info(f"调度器状态: {status}")
        
        # 启动后立即运行一次新闻获取
        logger.info("启动后立即运行一次新闻获取...")
        try:
            result = await scheduler.fetch_all_sources()
            logger.info(f"启动后首次新闻获取完成: {result['success_count']}/{result['success_count'] + result['error_count']} 个源成功，共获取 {result['total_items']} 条新闻，耗时 {result['duration']:.2f}秒")
        except Exception as e:
            logger.error(f"启动后首次新闻获取失败: {e}")
        
        # 保持运行
        logger.info("应用正在运行，按 Ctrl+C 退出...")
        
        # 等待信号
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("接收到键盘中断信号")
        await shutdown()
    except Exception as e:
        logger.error(f"应用运行失败: {e}")
        await shutdown()
        raise


async def run_once():
    """运行一次新闻获取"""
    global scheduler
    
    logger.info("运行一次新闻获取...")
    
    # 初始化应用
    await init_app()
    
    try:
        # 手动触发一次新闻获取
        result = await scheduler.fetch_all_sources()
        
        logger.info(f"新闻获取完成: {result['success_count']}/{result['success_count'] + result['error_count']} 个源成功，共获取 {result['total_items']} 条新闻，耗时 {result['duration']:.2f}秒")
        
    except Exception as e:
        logger.error(f"新闻获取失败: {e}")
        raise
    finally:
        # 关闭数据库连接
        await close_mongodb()


async def list_sources():
    """列出所有可用的新闻源"""
    logger.info("可用的新闻源:")
    
    sources_info = get_all_sources_info()
    
    for info in sources_info:
        logger.info(f"  {info['id']}: {info['name']} ({info['url']})")
    
    logger.info(f"总计: {len(sources_info)} 个新闻源")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="NewsNow Python 版本")
    parser.add_argument(
        "--once", 
        action="store_true", 
        help="运行一次新闻获取后退出"
    )
    parser.add_argument(
        "--list-sources", 
        action="store_true", 
        help="列出所有可用的新闻源"
    )
    parser.add_argument(
        "--config", 
        type=str, 
        help="指定配置文件路径"
    )
    
    args = parser.parse_args()
    
    # 设置信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        if args.list_sources:
            # 列出新闻源
            asyncio.run(list_sources())
        elif args.once:
            # 运行一次
            asyncio.run(run_once())
        else:
            # 正常启动
            asyncio.run(start_app())
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
        sys.exit(0)
    except Exception as e:
        logger.error(f"程序运行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()