"""网络请求工具模块"""

import asyncio
import random
from typing import Optional, Dict, Any, List, Union
from urllib.parse import urlparse
import httpx
from loguru import logger

from .config import get_config


class ProxyManager:
    """代理管理器"""
    
    def __init__(self):
        self.config = get_config()
        self.proxies: List[str] = []
        self.current_proxy_index = 0
        self.failed_proxies: set = set()
        self.load_proxies()
        
        # 启动时测试代理 - 只在异步环境中执行
        if self.config.get("PROXY_TEST_ON_START", True) and self.proxies:
            try:
                loop = asyncio.get_running_loop()
                asyncio.create_task(self.test_all_proxies())
            except RuntimeError:
                # 不在异步环境中，跳过启动时测试
                pass
    
    def load_proxies(self) -> None:
        """加载代理列表"""
        proxy_list = self.config.get("PROXY_LIST")
        if proxy_list:
            if isinstance(proxy_list, str):
                # 支持逗号分隔的代理列表
                self.proxies = [p.strip() for p in proxy_list.split(",") if p.strip()]
            elif isinstance(proxy_list, list):
                self.proxies = proxy_list
        
        if self.proxies:
            logger.info(f"已加载 {len(self.proxies)} 个代理")
    
    def get_proxy(self) -> Optional[str]:
        """获取可用代理"""
        if not self.proxies or not self.config.get("PROXY_ENABLED", False):
            return None
        
        available_proxies = [p for p in self.proxies if p not in self.failed_proxies]
        
        if not available_proxies:
            # 重置失败代理列表
            self.failed_proxies.clear()
            available_proxies = self.proxies
        
        if self.config.get("PROXY_ROTATION", False):
            # 轮询模式
            proxy = available_proxies[self.current_proxy_index % len(available_proxies)]
            self.current_proxy_index += 1
        else:
            # 随机模式
            proxy = random.choice(available_proxies)
        
        return proxy
    
    def mark_proxy_failed(self, proxy: str) -> None:
        """标记代理失败"""
        self.failed_proxies.add(proxy)
        logger.warning(f"代理 {proxy} 标记为失败")
    
    async def test_proxy(self, proxy: str, test_url: str = "https://httpbin.org/ip") -> bool:
        """测试代理可用性"""
        try:
            async with httpx.AsyncClient(
                proxy=proxy,
                timeout=10.0
            ) as client:
                response = await client.get(test_url)
                return response.status_code == 200
        except Exception:
            return False
    
    async def test_all_proxies(self) -> None:
        """测试所有代理的可用性"""
        if not self.proxies:
            return
        
        test_url = self.config.get("PROXY_TEST_URL", "https://httpbin.org/ip")
        logger.info(f"开始测试 {len(self.proxies)} 个代理...")
        
        working_count = 0
        for proxy in self.proxies:
            is_working = await self.test_proxy(proxy, test_url)
            if is_working:
                working_count += 1
                logger.debug(f"代理 {proxy} 测试通过")
            else:
                self.failed_proxies.add(proxy)
                logger.warning(f"代理 {proxy} 测试失败")
        
        logger.info(f"代理测试完成: {working_count}/{len(self.proxies)} 个代理可用")


class NetworkFetcher:
    """网络请求器"""
    
    def __init__(self):
        self.config = get_config()
        self.proxy_manager = ProxyManager()
        self.session: Optional[httpx.AsyncClient] = None
    
    def get_headers(self, custom_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """获取请求头"""
        headers = {
            "User-Agent": self.config.get("USER_AGENT", 
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        
        if custom_headers:
            headers.update(custom_headers)
        
        return headers
    
    def get_client_config(self, proxy: Optional[str] = None) -> Dict[str, Any]:
        """获取HTTP客户端配置"""
        config = {
            "timeout": httpx.Timeout(self.config.get("REQUEST_TIMEOUT", 30)),
            "follow_redirects": True,
            "verify": False,  # 忽略SSL证书验证
        }
        
        if proxy:
            config["proxy"] = proxy
        
        return config
    
    async def fetch(
        self,
        url: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Union[Dict[str, Any], str, bytes]] = None,
        json: Optional[Dict[str, Any]] = None,
        cookies: Optional[Dict[str, str]] = None,
        allow_redirects: bool = True,
        max_retries: Optional[int] = None,
        retry_delay: Optional[float] = None,
        use_proxy: bool = True
    ) -> httpx.Response:
        """发送HTTP请求"""
        
        if max_retries is None:
            max_retries = self.config.get("MAX_RETRIES", 3)
        
        if retry_delay is None:
            retry_delay = self.config.get("RETRY_DELAY", 1)
        
        request_headers = self.get_headers(headers)
        
        last_exception = None
        
        for attempt in range(max_retries + 1):
            proxy = None
            if use_proxy and attempt >= 2:  # 失败2次后使用代理
                proxy = self.proxy_manager.get_proxy()
            
            try:
                client_config = self.get_client_config(proxy)
                
                async with httpx.AsyncClient(**client_config) as client:
                    response = await client.request(
                        method=method,
                        url=url,
                        headers=request_headers,
                        params=params,
                        data=data,
                        json=json,
                        cookies=cookies
                    )
                    
                    # 检查响应状态
                    if response.status_code >= 400:
                        if response.status_code in [429, 503, 502, 504]:  # 可重试的错误
                            raise httpx.HTTPStatusError(
                                f"HTTP {response.status_code}",
                                request=response.request,
                                response=response
                            )
                        else:
                            # 不可重试的错误，直接返回
                            return response
                    
                    logger.debug(f"成功请求 {url} (尝试 {attempt + 1}/{max_retries + 1})")
                    return response
                    
            except Exception as e:
                last_exception = e
                
                # 如果使用了代理且请求失败，标记代理为失败
                if proxy:
                    self.proxy_manager.mark_proxy_failed(proxy)
                
                if attempt < max_retries:
                    wait_time = retry_delay * (2 ** attempt)  # 指数退避
                    logger.warning(
                        f"请求 {url} 失败 (尝试 {attempt + 1}/{max_retries + 1}): {e}, "
                        f"{wait_time}秒后重试"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"请求 {url} 最终失败: {e}")
        
        # 所有重试都失败了
        if last_exception:
            raise last_exception
        else:
            raise Exception(f"请求 {url} 失败，未知错误")
    
    async def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> httpx.Response:
        """GET请求"""
        return await self.fetch(url, "GET", headers=headers, params=params, **kwargs)
    
    async def post(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Union[Dict[str, Any], str, bytes]] = None,
        json: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> httpx.Response:
        """POST请求"""
        return await self.fetch(url, "POST", headers=headers, data=data, json=json, **kwargs)
    
    async def get_text(self, url: str, encoding: str = "utf-8", **kwargs) -> str:
        """获取文本内容"""
        response = await self.get(url, **kwargs)
        response.encoding = encoding
        return response.text
    
    async def get_json(self, url: str, **kwargs) -> Dict[str, Any]:
        """获取JSON内容"""
        import json
        response = await self.get(url, **kwargs)
        
        # 检查响应内容是否为空
        if not response.content:
            logger.warning(f"响应内容为空: {url}")
            raise ValueError("响应内容为空")
        
        try:
            # 尝试直接解析JSON
            return response.json()
        except UnicodeDecodeError as e:
            # 如果遇到编码问题，尝试不同的编码
            logger.warning(f"JSON编码问题，尝试修复: {e}")
            try:
                # 尝试使用 response.content 并手动解码
                content = response.content
                # 尝试不同的编码
                for encoding in ['utf-8', 'gbk', 'gb2312', 'latin1']:
                    try:
                        text = content.decode(encoding)
                        return json.loads(text)
                    except (UnicodeDecodeError, json.JSONDecodeError):
                        continue
                # 如果都失败了，使用 latin1 编码（不会失败）
                text = content.decode('latin1')
                return json.loads(text)
            except Exception as e2:
                logger.error(f"修复JSON编码失败: {e2}")
                raise e2
        except json.JSONDecodeError as e:
            # 处理JSON解析错误
            logger.warning(f"JSON解析失败: {e}")
            # 尝试检查响应内容
            try:
                content_text = response.text[:200]  # 只取前200个字符
                logger.warning(f"响应内容预览: {content_text}")
            except Exception:
                pass
            raise e
    
    async def get_bytes(self, url: str, **kwargs) -> bytes:
        """获取二进制内容"""
        response = await self.get(url, **kwargs)
        return response.content
    
    async def check_url_availability(self, url: str, timeout: float = 10.0) -> bool:
        """检查URL可用性"""
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.head(url)
                return response.status_code < 400
        except Exception:
            return False


# 全局网络请求器实例
_fetcher_instance: Optional[NetworkFetcher] = None


def get_fetcher() -> NetworkFetcher:
    """获取网络请求器实例"""
    global _fetcher_instance
    if _fetcher_instance is None:
        _fetcher_instance = NetworkFetcher()
    return _fetcher_instance


# 便捷函数
async def fetch(
    url: str,
    method: str = "GET",
    **kwargs
) -> httpx.Response:
    """发送HTTP请求"""
    fetcher = get_fetcher()
    return await fetcher.fetch(url, method, **kwargs)


async def get(url: str, **kwargs) -> httpx.Response:
    """GET请求"""
    fetcher = get_fetcher()
    return await fetcher.get(url, **kwargs)


async def post(url: str, **kwargs) -> httpx.Response:
    """POST请求"""
    fetcher = get_fetcher()
    return await fetcher.post(url, **kwargs)


async def get_text(url: str, encoding: str = "utf-8", **kwargs) -> str:
    """获取文本内容"""
    fetcher = get_fetcher()
    return await fetcher.get_text(url, encoding=encoding, **kwargs)


async def get_json(url: str, **kwargs) -> Dict[str, Any]:
    """获取JSON内容"""
    fetcher = get_fetcher()
    return await fetcher.get_json(url, **kwargs)


async def get_bytes(url: str, **kwargs) -> bytes:
    """获取二进制内容"""
    fetcher = get_fetcher()
    return await fetcher.get_bytes(url, **kwargs)