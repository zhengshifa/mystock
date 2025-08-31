"""新闻源基础模块"""

import asyncio
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Callable, Awaitable
from datetime import datetime
from bs4 import BeautifulSoup
from loguru import logger

from database.models import NewsItem, SourceResponse
from utils.fetch import get_fetcher
from utils.config import get_config


class BaseSource(ABC):
    """新闻源基类"""
    
    def __init__(self, source_id: str, name: str, url: str):
        self.source_id = source_id
        self.name = name
        self.url = url
        self.config = get_config()
        self.fetcher = get_fetcher()
    
    @abstractmethod
    async def fetch_news(self) -> SourceResponse:
        """获取新闻数据"""
        pass
    
    def create_news_item(
        self,
        title: str,
        url: str,
        description: Optional[str] = None,
        image: Optional[str] = None,
        author: Optional[str] = None,
        published_at: Optional[datetime] = None,
        extra: Optional[Dict[str, Any]] = None
    ) -> NewsItem:
        """创建新闻条目"""
        return NewsItem(
            title=title.strip() if title else "",
            url=url.strip() if url else "",
            source_id=self.source_id,
            description=description.strip() if description else None,
            image=image.strip() if image else None,
            author=author.strip() if author else None,
            published_at=published_at,
            extra=extra or {}
        )
    
    def create_success_response(self, items: List[NewsItem]) -> SourceResponse:
        """创建成功响应"""
        return SourceResponse(
            status="success",
            source_id=self.source_id,
            items=items
        )
    
    def create_error_response(self, error_message: str) -> SourceResponse:
        """创建错误响应"""
        return SourceResponse(
            status="error",
            source_id=self.source_id,
            items=[],
            error_message=error_message
        )
    
    def create_cache_response(self, items: List[NewsItem]) -> SourceResponse:
        """创建缓存响应"""
        return SourceResponse(
            status="cache",
            source_id=self.source_id,
            items=items
        )


class HTMLSource(BaseSource):
    """HTML网页新闻源"""
    
    async def fetch_html(self, url: str, encoding: str = "utf-8") -> BeautifulSoup:
        """获取并解析HTML"""
        try:
            html_content = await self.fetcher.get_text(url, encoding=encoding)
            return BeautifulSoup(html_content, 'html.parser')
        except Exception as e:
            logger.error(f"获取HTML失败 {url}: {e}")
            raise
    
    def extract_text(self, element, default: str = "") -> str:
        """提取元素文本"""
        if element:
            return element.get_text(strip=True)
        return default
    
    def extract_attr(self, element, attr: str, default: str = "") -> str:
        """提取元素属性"""
        if element:
            return element.get(attr, default)
        return default
    
    def resolve_url(self, base_url: str, relative_url: str) -> str:
        """解析相对URL"""
        from urllib.parse import urljoin
        return urljoin(base_url, relative_url)


class RSSSource(BaseSource):
    """RSS新闻源"""
    
    async def fetch_rss(self, url: str) -> Dict[str, Any]:
        """获取并解析RSS"""
        try:
            import feedparser
            
            # 获取RSS内容
            content = await self.fetcher.get_text(url)
            
            # 解析RSS
            feed = feedparser.parse(content)
            
            if feed.bozo:
                logger.warning(f"RSS解析警告 {url}: {feed.bozo_exception}")
            
            return feed
            
        except Exception as e:
            logger.error(f"获取RSS失败 {url}: {e}")
            raise
    
    def parse_rss_item(self, item: Dict[str, Any]) -> NewsItem:
        """解析RSS条目"""
        title = item.get('title', '')
        link = item.get('link', '')
        description = item.get('summary', '') or item.get('description', '')
        author = item.get('author', '')
        
        # 解析发布时间
        published_at = None
        if 'published_parsed' in item and item['published_parsed']:
            import time
            published_at = datetime.fromtimestamp(time.mktime(item['published_parsed']))
        elif 'updated_parsed' in item and item['updated_parsed']:
            import time
            published_at = datetime.fromtimestamp(time.mktime(item['updated_parsed']))
        
        return self.create_news_item(
            title=title,
            url=link,
            description=description,
            author=author,
            published_at=published_at
        )
    
    async def fetch_news(self) -> SourceResponse:
        """获取RSS新闻"""
        try:
            feed = await self.fetch_rss(self.url)
            
            items = []
            max_items = self.config.get("MAX_NEWS_PER_SOURCE", 50)
            
            for entry in feed.entries[:max_items]:
                try:
                    news_item = self.parse_rss_item(entry)
                    if news_item.title and news_item.url:
                        items.append(news_item)
                except Exception as e:
                    logger.warning(f"解析RSS条目失败: {e}")
                    continue
            
            logger.success(f"成功获取 {self.source_id} 的 {len(items)} 条新闻")
            return self.create_success_response(items)
            
        except Exception as e:
            error_msg = f"获取 {self.source_id} RSS数据失败: {e}"
            logger.error(error_msg)
            return self.create_error_response(error_msg)


class JSONSource(BaseSource):
    """JSON API新闻源"""
    
    async def fetch_json(self, url: str, **kwargs) -> Dict[str, Any]:
        """获取JSON数据"""
        try:
            return await self.fetcher.get_json(url, **kwargs)
        except Exception as e:
            logger.error(f"获取JSON失败 {url}: {e}")
            raise
    
    @abstractmethod
    def parse_json_response(self, data: Dict[str, Any]) -> List[NewsItem]:
        """解析JSON响应"""
        pass
    
    async def fetch_news(self) -> SourceResponse:
        """获取JSON新闻"""
        try:
            data = await self.fetch_json(self.url)
            items = self.parse_json_response(data)
            
            # 限制条目数量
            max_items = self.config.get("MAX_NEWS_PER_SOURCE", 50)
            items = items[:max_items]
            
            logger.success(f"成功获取 {self.source_id} 的 {len(items)} 条新闻")
            return self.create_success_response(items)
            
        except Exception as e:
            error_msg = f"获取 {self.source_id} JSON数据失败: {e}"
            logger.error(error_msg)
            return self.create_error_response(error_msg)


# 新闻源装饰器
def define_source(
    source_id: str,
    name: str,
    url: str,
    source_type: str = "html"
):
    """定义新闻源装饰器"""
    def decorator(func: Callable[[], Awaitable[SourceResponse]]):
        async def wrapper() -> SourceResponse:
            try:
                logger.debug(f"开始获取 {source_id} 数据")
                result = await func()
                logger.debug(f"完成获取 {source_id} 数据")
                return result
            except Exception as e:
                error_msg = f"获取 {source_id} 数据失败: {e}"
                logger.error(error_msg)
                return SourceResponse(
                    status="error",
                    source_id=source_id,
                    items=[],
                    error_message=error_msg
                )
        
        # 添加元数据
        wrapper.source_id = source_id
        wrapper.name = name
        wrapper.url = url
        wrapper.source_type = source_type
        
        return wrapper
    
    return decorator


def define_rss_source(source_id: str, name: str, url: str):
    """定义RSS新闻源"""
    @define_source(source_id, name, url, "rss")
    async def rss_getter() -> SourceResponse:
        source = RSSSource(source_id, name, url)
        return await source.fetch_news()
    
    return rss_getter


def define_rsshub_source(source_id: str, name: str, path: str, base_url: str = "https://rsshub.app"):
    """定义RSSHub新闻源"""
    url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"
    return define_rss_source(source_id, name, url)