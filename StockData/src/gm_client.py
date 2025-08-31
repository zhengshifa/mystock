#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
掘金量化SDK测试客户端
用于测试与掘金量化平台的连接
"""

import sys
import os

# 临时移除当前目录和src目录，避免模块冲突
original_path = sys.path.copy()
current_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(current_dir)

# 移除可能冲突的路径
if current_dir in sys.path:
    sys.path.remove(current_dir)
if project_dir in sys.path:
    sys.path.remove(project_dir)

try:
    import gm.api as gm
    print("掘金量化SDK导入成功")
except Exception as e:
    print(f"掘金量化SDK导入失败: {e}")
    # 恢复原始路径
    sys.path = original_path
    sys.exit(1)

# 恢复原始路径
sys.path = original_path

import time
from typing import Optional, Callable


class GMClient:
    """掘金量化客户端类"""
    
    def __init__(self, token: str = None, account_id: str = None):
        """
        初始化掘金量化客户端
        
        Args:
            token (str, optional): 掘金量化平台的访问令牌
            account_id (str, optional): 账户ID
        """
        self.token = token or "d5791ecb0f33260e9fd719227c36f5c28b42e11c"
        self.account_id = account_id
        self.is_connected = False
        
    def connect(self) -> bool:
        """
        连接到掘金量化平台
        
        Returns:
            bool: 连接是否成功
        """
        try:
            print("正在连接到掘金量化平台...")
            gm.set_token(self.token)
            
            # 如果提供了账户ID，则设置账户ID
            if self.account_id:
                print(f"设置账户ID: {self.account_id}")
                gm.set_account_id(self.account_id)
            
            self.is_connected = True
            print("成功连接到掘金量化平台")
            return True
        except Exception as e:
            print(f"连接失败: {e}")
            self.is_connected = False
            return False
    
    def test_connection(self) -> bool:
        """
        测试连接状态（不需要ACCOUNT_ID）
        
        Returns:
            bool: 连接是否正常
        """
        if not self.is_connected:
            print("客户端未连接，请先调用connect()方法")
            return False
        
        try:
            # 获取SDK版本信息来测试连接（不需要ACCOUNT_ID）
            version = gm.get_version()
            print(f"SDK版本: {version}")
            return True
        except Exception as e:
            print(f"连接测试失败: {e}")
            return False
    
    def get_account_info(self) -> Optional[dict]:
        """
        获取账户信息（如果有ACCOUNT_ID则获取详细信息，否则获取基本信息）
        
        Returns:
            Optional[dict]: 账户信息字典，失败时返回None
        """
        if not self.is_connected:
            print("客户端未连接，请先调用connect()方法")
            return None
        
        # 如果没有ACCOUNT_ID，返回基本信息
        if not self.account_id:
            print("未设置ACCOUNT_ID，返回基本信息")
            try:
                version = gm.get_version()
                lang = gm.sdk_lang
                
                account_info = {
                    'sdk_version': version,
                    'sdk_language': lang,
                    'connection_status': 'connected',
                    'note': '账户详细信息需要设置ACCOUNT_ID'
                }
                print("成功获取基本信息")
                return account_info
            except Exception as e:
                print(f"获取基本信息失败: {e}")
                return None
        
        # 如果有ACCOUNT_ID，尝试获取详细信息
        try:
            cash_info = gm.get_cash()
            position_info = gm.get_position()
            
            account_info = {
                'cash': cash_info,
                'position': position_info,
                'account_id': self.account_id,
                'connection_status': 'connected'
            }
            print("成功获取详细账户信息")
            return account_info
        except Exception as e:
            print(f"获取详细账户信息失败: {e}")
            # 如果获取详细信息失败，返回基本信息
            print("返回基本信息作为备选")
            try:
                version = gm.get_version()
                lang = gm.sdk_lang
                
                account_info = {
                    'sdk_version': version,
                    'sdk_language': lang,
                    'connection_status': 'connected',
                    'note': '详细账户信息获取失败，返回基本信息'
                }
                return account_info
            except Exception as e2:
                print(f"获取基本信息也失败: {e2}")
                return None
    
    def get_account_details(self) -> Optional[dict]:
        """
        获取详细账户信息（需要ACCOUNT_ID）
        
        Returns:
            Optional[dict]: 详细账户信息字典，失败时返回None
        """
        if not self.is_connected:
            print("客户端未连接，请先调用connect()方法")
            return None
        
        if not self.account_id:
            print("未设置ACCOUNT_ID，无法获取详细账户信息")
            return None
        
        try:
            # 获取现金和持仓信息
            cash_info = gm.get_cash()
            position_info = gm.get_position()
            
            account_info = {
                'cash': cash_info,
                'position': position_info,
                'account_id': self.account_id
            }
            print("成功获取详细账户信息")
            return account_info
        except Exception as e:
            print(f"获取详细账户信息失败: {e}")
            return None
    
    def disconnect(self):
        """断开连接"""
        if self.is_connected:
            self.is_connected = False
            print("已断开与掘金量化平台的连接")
    
    def submit_data_task(self, task_name: str, func: Callable, *args, **kwargs) -> str:
        """
        提交数据获取任务到调度器
        
        Args:
            task_name: 任务名称
            func: 要执行的函数
            *args: 函数参数
            **kwargs: 函数关键字参数
            
        Returns:
            任务ID
        """
        # 简化版本，直接返回任务名称
        return f"{task_name}_{int(time.time() * 1000)}"
    
    def get_task_status(self, task_id: str):
        """获取任务状态"""
        return "completed"
    
    def get_task_result(self, task_id: str):
        """获取任务结果"""
        return "任务执行完成"


def main():
    """主函数 - 测试掘金量化SDK连接"""
    # 创建客户端实例（使用配置中的token）
    client = GMClient()
    
    try:
        # 测试连接
        if client.connect():
            print("连接测试成功！")
            
            # 测试获取账户信息
            if client.test_connection():
                print("连接状态正常！")
                
                # 获取账户信息
                account_info = client.get_account_info()
                if account_info:
                    print("账户信息获取成功！")
                    print(f"账户详情: {account_info}")
            else:
                print("连接测试失败！")
        else:
            print("无法连接到掘金量化平台！")
            
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
    finally:
        # 断开连接
        client.disconnect()
        print("测试完成，已断开连接")


if __name__ == "__main__":
    main()
