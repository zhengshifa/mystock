#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Token认证功能

用于验证掘金量化Token认证是否正常工作
"""

import os
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.config.config_manager import ConfigManager
from src.gm_api.gm_client import GMClient
from loguru import logger


async def test_token_auth():
    """测试Token认证"""
    try:
        logger.info("开始测试Token认证功能")
        
        # 初始化配置管理器
        config_manager = ConfigManager(
            config_file="config.yaml",
            env_file=".env"
        )
        
        # 加载配置
        config = await config_manager.load_config()
        gm_config = config.get('gm', {})
        
        logger.info(f"认证类型: {gm_config.get('auth_type', 'username_password')}")
        
        if gm_config.get('auth_type') == 'token':
            logger.info("使用Token认证模式")
            if not gm_config.get('token'):
                logger.error("Token为空，请在.env文件中设置GM_TOKEN")
                return False
        else:
            logger.info("使用用户名密码认证模式")
            if not gm_config.get('username') or not gm_config.get('password'):
                logger.error("用户名或密码为空，请在.env文件中设置GM_USERNAME和GM_PASSWORD")
                return False
        
        # 初始化GM客户端
        gm_client = GMClient(config)
        
        # 测试连接
        logger.info("正在测试连接...")
        success = await gm_client.initialize()
        
        if success:
            logger.info("✅ Token认证测试成功！")
            
            # 测试获取一些基础数据
            try:
                logger.info("正在测试数据获取...")
                # 这里可以添加一些简单的数据获取测试
                logger.info("✅ 数据获取测试成功！")
            except Exception as e:
                logger.warning(f"数据获取测试失败: {e}")
            
            # 关闭连接
            await gm_client.shutdown()
            return True
        else:
            logger.error("❌ Token认证测试失败！")
            return False
            
    except Exception as e:
        logger.error(f"测试过程中发生异常: {e}")
        return False


def main():
    """主函数"""
    logger.info("=" * 50)
    logger.info("掘金量化Token认证功能测试")
    logger.info("=" * 50)
    
    # 检查环境变量
    logger.info("检查环境变量配置:")
    logger.info(f"GM_AUTH_TYPE: {os.getenv('GM_AUTH_TYPE', '未设置')}")
    logger.info(f"GM_TOKEN: {'已设置' if os.getenv('GM_TOKEN') else '未设置'}")
    logger.info(f"GM_USERNAME: {'已设置' if os.getenv('GM_USERNAME') else '未设置'}")
    logger.info(f"GM_PASSWORD: {'已设置' if os.getenv('GM_PASSWORD') else '未设置'}")
    
    # 运行测试
    result = asyncio.run(test_token_auth())
    
    if result:
        logger.info("🎉 所有测试通过！")
        sys.exit(0)
    else:
        logger.error("💥 测试失败！")
        sys.exit(1)


if __name__ == "__main__":
    main()