#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
掘金量化连接管理器

负责管理与掘金量化服务器的连接，包括:
- 连接建立和维护
- 连接状态监控
- 自动重连机制
- 连接池管理
"""

import asyncio
import time
from typing import Dict, Any, Optional, Callable
from loguru import logger
from retrying import retry

try:
    import gm
except ImportError:
    logger.warning("掘金量化SDK未安装，请安装gm3包")
    gm = None


class GMConnectionManager:
    """掘金量化连接管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.username = config.get('username', '')
        self.password = config.get('password', '')
        self.token = config.get('token', '')
        self.auth_type = config.get('auth_type', 'username_password')  # 'username_password' 或 'token'
        self.server_url = config.get('server_url', 'api.myquant.cn:9000')
        self.timeout = config.get('timeout', 30)
        self.retry_times = config.get('retry_times', 3)
        
        self.is_connected = False
        self.connection_time = None
        self.last_heartbeat = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10
        
        # 连接状态回调
        self.on_connected: Optional[Callable] = None
        self.on_disconnected: Optional[Callable] = None
        self.on_error: Optional[Callable] = None
        
        # 心跳检测
        self.heartbeat_interval = 30  # 秒
        self.heartbeat_task = None
        
        logger.info("掘金量化连接管理器初始化完成")
    
    async def connect(self) -> bool:
        """连接到掘金量化服务器"""
        if gm is None:
            logger.error("掘金量化SDK未安装")
            return False
        
        try:
            logger.info(f"正在连接掘金量化服务器: {self.server_url}")
            
            # 设置连接参数
            gm.set_serv_addr(self.server_url)
            
            # 根据认证类型设置认证信息
            if self.auth_type == 'token':
                if not self.token:
                    raise ValueError("Token认证模式下必须提供token")
                gm.set_token(self.token)
                logger.info("使用Token认证模式")
            else:
                if not self.username or not self.password:
                    raise ValueError("用户名密码认证模式下必须提供用户名和密码")
                gm.set_token(self.username, self.password)
                logger.info("使用用户名密码认证模式")
            
            # 建立连接
            result = await self._connect_with_retry()
            
            if result:
                self.is_connected = True
                self.connection_time = time.time()
                self.last_heartbeat = time.time()
                self.reconnect_attempts = 0
                
                # 启动心跳检测
                await self._start_heartbeat()
                
                logger.info("掘金量化连接建立成功")
                
                if self.on_connected:
                    await self._safe_callback(self.on_connected)
                
                return True
            else:
                logger.error("掘金量化连接建立失败")
                return False
                
        except Exception as e:
            logger.error(f"连接掘金量化服务器异常: {e}")
            if self.on_error:
                await self._safe_callback(self.on_error, e)
            return False
    
    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    async def _connect_with_retry(self) -> bool:
        """带重试的连接"""
        try:
            # 根据认证类型进行登录
            if self.auth_type == 'token':
                ret = gm.login(token=self.token)
            else:
                ret = gm.login(self.username, self.password)
            if ret != 0:
                raise Exception(f"登录失败，错误码: {ret}")
            
            # 验证连接
            account_info = gm.get_account()
            if not account_info:
                raise Exception("获取账户信息失败")
            
            logger.info(f"登录成功，账户: {account_info.get('account_id', 'Unknown')}")
            return True
            
        except Exception as e:
            logger.warning(f"连接尝试失败: {e}")
            raise
    
    async def disconnect(self):
        """断开连接"""
        try:
            logger.info("正在断开掘金量化连接")
            
            # 停止心跳检测
            await self._stop_heartbeat()
            
            # 断开连接
            if gm and self.is_connected:
                gm.logout()
            
            self.is_connected = False
            self.connection_time = None
            self.last_heartbeat = None
            
            logger.info("掘金量化连接已断开")
            
            if self.on_disconnected:
                await self._safe_callback(self.on_disconnected)
                
        except Exception as e:
            logger.error(f"断开连接异常: {e}")
    
    async def reconnect(self) -> bool:
        """重新连接"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.error(f"重连次数已达上限 {self.max_reconnect_attempts}")
            return False
        
        self.reconnect_attempts += 1
        logger.info(f"尝试重新连接 (第 {self.reconnect_attempts} 次)")
        
        # 先断开现有连接
        await self.disconnect()
        
        # 等待一段时间后重连
        await asyncio.sleep(min(self.reconnect_attempts * 2, 30))
        
        return await self.connect()
    
    async def _start_heartbeat(self):
        """启动心跳检测"""
        if self.heartbeat_task:
            return
        
        self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        logger.debug("心跳检测已启动")
    
    async def _stop_heartbeat(self):
        """停止心跳检测"""
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass
            self.heartbeat_task = None
            logger.debug("心跳检测已停止")
    
    async def _heartbeat_loop(self):
        """心跳检测循环"""
        while self.is_connected:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                
                if not await self._check_connection():
                    logger.warning("心跳检测失败，尝试重连")
                    await self.reconnect()
                    break
                else:
                    self.last_heartbeat = time.time()
                    logger.debug("心跳检测正常")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"心跳检测异常: {e}")
                await asyncio.sleep(5)
    
    async def _check_connection(self) -> bool:
        """检查连接状态"""
        try:
            if not gm or not self.is_connected:
                return False
            
            # 尝试获取账户信息来验证连接
            account_info = gm.get_account()
            return account_info is not None
            
        except Exception as e:
            logger.debug(f"连接检查失败: {e}")
            return False
    
    async def _safe_callback(self, callback: Callable, *args):
        """安全执行回调函数"""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(*args)
            else:
                callback(*args)
        except Exception as e:
            logger.error(f"回调函数执行异常: {e}")
    
    def get_connection_info(self) -> Dict[str, Any]:
        """获取连接信息"""
        return {
            'is_connected': self.is_connected,
            'connection_time': self.connection_time,
            'last_heartbeat': self.last_heartbeat,
            'reconnect_attempts': self.reconnect_attempts,
            'server_url': self.server_url,
            'username': self.username
        }
    
    def set_callbacks(self, 
                     on_connected: Optional[Callable] = None,
                     on_disconnected: Optional[Callable] = None,
                     on_error: Optional[Callable] = None):
        """设置连接状态回调函数"""
        self.on_connected = on_connected
        self.on_disconnected = on_disconnected
        self.on_error = on_error
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.disconnect()