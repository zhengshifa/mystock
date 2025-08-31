"""法布财经新闻源实现"""

import re
from datetime import datetime
from typing import List, Dict, Any
from bs4 import BeautifulSoup

from sources.base import HTMLSource
from database.models import NewsItem, SourceResponse
from utils.logger import get_logger

logger = get_logger(__name__)


class FastbullSource(HTMLSource):
    """法布财经新闻源"""
    
    def __init__(self, source_type: str = "express"):
        """初始化法布财经新闻源
        
        Args:
            source_type: 新闻类型 (express/news)
        """
        self.source_type = source_type
        source_id = f"fastbull-{source_type}"
        name = "法布财经"
        
        # 根据类型设置不同的URL
        if source_type == "express":
            url = f"https://www.fastbull.com/cn/express-news"
        elif source_type == "news":
            url = f"https://www.fastbull.com/cn/news"
        else:
            raise ValueError(f"不支持的新闻类型: {source_type}")
        
        super().__init__(source_id, name, url)
        self.base_url = "https://www.fastbull.com"
        self.interval = 120  # 2分钟
    
    async def parse_html_response(self, html: str) -> List[NewsItem]:
        """解析法布财经HTML响应"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            news_items = []
            
            if self.source_type == "express":
                # 快讯页面解析
                news_containers = soup.find_all(class_="news-list")
                
                for container in news_containers:
                    try:
                        # 查找标题链接
                        title_element = container.find(class_="title_name")
                        if not title_element:
                            continue
                        
                        url_path = title_element.get("href")
                        title_text = title_element.get_text(strip=True)
                        
                        if not url_path or not title_text:
                            continue
                        
                        # 构建完整URL
                        url = self.base_url + url_path if url_path.startswith("/") else url_path
                        
                        # 处理标题格式，提取【】内的内容
                        title_match = re.search(r'【(.+)】', title_text)
                        if title_match:
                            title = title_match.group(1)
                            # 如果提取的标题太短，使用原标题
                            if len(title) < 4:
                                title = title_text
                        else:
                            title = title_text
                        
                        # 获取时间戳
                        date_attr = container.get("data-date")
                        published_at = datetime.now()
                        
                        if date_attr:
                            try:
                                published_at = datetime.fromtimestamp(int(date_attr) / 1000)
                            except (ValueError, TypeError):
                                published_at = datetime.now()
                        
                        # 创建新闻项
                        news_item = NewsItem(
                            title=title,
                            url=url,
                            source_id=self.source_id,
                            description="",
                            published_at=published_at,
                            extra={
                                "type": "realtime",
                                "source_type": self.source_type,
                                "original_title": title_text
                            }
                        )
                        news_items.append(news_item)
                        
                    except Exception as e:
                        logger.warning(f"法布财经({self.source_type}): 解析单条新闻失败 - {e}")
                        continue
            
            elif self.source_type == "news":
                # 新闻页面解析
                news_containers = soup.find_all(class_="trending_type")
                
                for container in news_containers:
                    try:
                        # 获取链接
                        url_path = container.get("href")
                        if not url_path:
                            continue
                        
                        # 构建完整URL
                        url = self.base_url + url_path if url_path.startswith("/") else url_path
                        
                        # 获取标题
                        title_element = container.find(class_="title")
                        if not title_element:
                            continue
                        
                        title = title_element.get_text(strip=True)
                        if not title:
                            continue
                        
                        # 获取时间戳
                        date_element = container.find("[data-date]")
                        published_at = datetime.now()
                        
                        if date_element:
                            date_attr = date_element.get("data-date")
                            if date_attr:
                                try:
                                    published_at = datetime.fromtimestamp(int(date_attr) / 1000)
                                except (ValueError, TypeError):
                                    published_at = datetime.now()
                        
                        # 创建新闻项
                        news_item = NewsItem(
                            title=title,
                            url=url,
                            source_id=self.source_id,
                            description="",
                            published_at=published_at,
                            extra={
                                "type": "news",
                                "source_type": self.source_type
                            }
                        )
                        news_items.append(news_item)
                        
                    except Exception as e:
                        logger.warning(f"法布财经({self.source_type}): 解析单条新闻失败 - {e}")
                        continue
            
            logger.info(f"法布财经({self.source_type}): 解析到 {len(news_items)} 条新闻")
            return news_items
            
        except Exception as e:
            logger.error(f"法布财经({self.source_type}): 解析HTML失败 - {e}")
            return []
    
    async def fetch_news(self) -> SourceResponse:
        """获取法布财经新闻"""
        try:
            # 获取HTML内容
            html = await self.fetch_html(self.url)
            
            # 解析HTML
            items = await self.parse_html_response(str(html))
            
            if items:
                logger.success(f"成功获取 {len(items)} 条 法布财经({self.source_type}) 新闻")
                return self.create_success_response(items)
            else:
                logger.info(f"法布财经({self.source_type}) 没有新数据")
                return self.create_success_response([])
                
        except Exception as e:
            logger.error(f"获取 法布财经({self.source_type}) 新闻失败: {e}")
            return self.create_error_response(str(e))


# 创建不同类型的法布财经新闻源实例
fastbull_express_source = FastbullSource("express")
fastbull_news_source = FastbullSource("news")


# 导出获取函数
async def get_fastbull_express_news():
    """获取法布财经快讯"""
    return await fastbull_express_source.fetch_news()


async def get_fastbull_news():
    """获取法布财经新闻"""
    return await fastbull_news_source.fetch_news()


# 统一的获取函数
async def fastbull_getter():
    """法布财经新闻获取器(默认快讯)"""
    return await get_fastbull_express_news()


async def fastbull_express_getter():
    """法布财经快讯获取器"""
    return await get_fastbull_express_news()


async def fastbull_news_getter():
    """法布财经新闻获取器"""
    return await get_fastbull_news()