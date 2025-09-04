#!/usr/bin/env python3
"""
测试serv_addr参数功能
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.config.settings import Settings
from src.services.gm_service import GMService
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_serv_addr_config():
    """测试serv_addr配置解析"""
    print("=== 测试serv_addr配置解析 ===")
    
    # 测试空值
    os.environ['GM_SERV_ADDR'] = ''
    settings = Settings()
    print(f"空值测试: serv_addr = '{settings.gm_serv_addr}'")
    
    # 测试有效格式
    os.environ['GM_SERV_ADDR'] = '127.0.0.1:7001'
    settings = Settings()
    print(f"有效格式测试: serv_addr = '{settings.gm_serv_addr}'")
    
    # 测试无效格式
    try:
        os.environ['GM_SERV_ADDR'] = 'invalid_format'
        settings = Settings()
        print(f"无效格式测试: serv_addr = '{settings.gm_serv_addr}'")
    except ValueError as e:
        print(f"无效格式测试: 正确捕获错误 - {e}")
    
    # 测试域名格式
    os.environ['GM_SERV_ADDR'] = 'example.com:8080'
    settings = Settings()
    print(f"域名格式测试: serv_addr = '{settings.gm_serv_addr}'")

def test_gm_service_with_serv_addr():
    """测试GM服务使用serv_addr参数"""
    print("\n=== 测试GM服务使用serv_addr参数 ===")
    
    try:
        # 设置serv_addr
        os.environ['GM_SERV_ADDR'] = '127.0.0.1:7001'
        
        # 创建GM服务实例
        gm_service = GMService()
        print("GM服务初始化成功")
        
        # 测试连接
        if gm_service.test_connection():
            print("GM服务连接测试成功")
        else:
            print("GM服务连接测试失败")
            
    except Exception as e:
        print(f"GM服务测试失败: {e}")

def test_gm_service_without_serv_addr():
    """测试GM服务不使用serv_addr参数（默认连接）"""
    print("\n=== 测试GM服务默认连接 ===")
    
    try:
        # 清空serv_addr
        os.environ['GM_SERV_ADDR'] = ''
        
        # 创建GM服务实例
        gm_service = GMService()
        print("GM服务初始化成功（默认连接）")
        
        # 测试连接
        if gm_service.test_connection():
            print("GM服务连接测试成功（默认连接）")
        else:
            print("GM服务连接测试失败（默认连接）")
            
    except Exception as e:
        print(f"GM服务测试失败: {e}")

if __name__ == "__main__":
    print("开始测试serv_addr参数功能...")
    
    # 测试配置解析
    test_serv_addr_config()
    
    # 测试GM服务
    test_gm_service_with_serv_addr()
    test_gm_service_without_serv_addr()
    
    print("\n测试完成！")
