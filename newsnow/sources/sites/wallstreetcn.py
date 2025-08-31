"""华尔街见闻新闻源实现"""

from datetime import datetime
from typing import List, Dict, Any, Optional

from sources.base import JSONSource
from database.models import NewsItem, SourceResponse
from utils.logger import get_logger

logger = get_logger(__name__)


class WallstreetcnSource(JSONSource):
    """华尔街见闻新闻源"""
    
    def __init__(self, source_type: str = "quick"):
        """初始化华尔街见闻新闻源
        
        Args:
            source_type: 新闻类型 (quick/news/hot)
        """
        self.source_type = source_type
        source_id = f"wallstreetcn-{source_type}"
        name = "华尔街见闻"
        url = "https://api-one.wallstcn.com/apiv1/content/lives?channel=global-channel&limit=30"  # 默认URL
        super().__init__(source_id, name, url)
        self.base_url = "https://wallstreetcn.com/"
        self.interval = 300  # 5分钟
        
        # 根据类型设置不同的API URL
        if source_type == "quick":
            self.url = "https://api-one.wallstcn.com/apiv1/content/lives?channel=global-channel&limit=30"
        elif source_type == "news":
            self.url = "https://api-one.wallstcn.com/apiv1/content/information-flow?channel=global-channel&accept=article&limit=30"
        elif source_type == "hot":
            self.url = "https://api-one.wallstcn.com/apiv1/content/articles/hot?period=all"
        else:
            raise ValueError(f"不支持的新闻类型: {source_type}")
    
    async def parse_json_response(self, data: Dict[str, Any]) -> List[NewsItem]:
        """解析华尔街见闻JSON响应"""
        try:
            news_items = []
            
            if self.source_type == "quick":
                # 快讯数据
                items = data.get("data", {}).get("items", [])
                for item in items:
                    news_item = NewsItem(
                        source_id=self.source_id,
                        title=item.get("title") or item.get("content_text", ""),
                        url=item.get("uri", ""),
                        description=item.get("content_short", ""),
                        published_at=datetime.fromtimestamp(item.get("display_time", 0)),
                        extra={
                            "type": "realtime",
                            "source_type": self.source_type
                        }
                    )
                    news_items.append(news_item)
            
            elif self.source_type == "news":
                # 新闻数据
                items = data.get("data", {}).get("items", [])
                for item_wrapper in items:
                    # 过滤广告和直播内容
                    if (item_wrapper.get("resource_type") in ["theme", "ad"] or 
                        not item_wrapper.get("resource", {}).get("uri")):
                        continue
                    
                    resource = item_wrapper.get("resource", {})
                    if resource.get("type") == "live":
                        continue
                    
                    news_item = NewsItem(
                        source_id=self.source_id,
                        title=resource.get("title") or resource.get("content_short", ""),
                        url=resource.get("uri", ""),
                        description=resource.get("content_text", ""),
                        published_at=datetime.fromtimestamp(resource.get("display_time", 0)),
                        extra={
                            "type": "news",
                            "source_type": self.source_type
                        }
                    )
                    news_items.append(news_item)
            
            elif self.source_type == "hot":
                # 热门数据
                items = data.get("data", {}).get("day_items", [])
                for item in items:
                    news_item = NewsItem(
                        source_id=self.source_id,
                        title=item.get("title", ""),
                        url=item.get("uri", ""),
                        description=item.get("content_short", ""),
                        published_at=datetime.now(),  # 热门新闻使用当前时间
                        extra={
                            "type": "hottest",
                            "source_type": self.source_type
                        }
                    )
                    news_items.append(news_item)
            
            logger.info(f"华尔街见闻({self.source_type}): 解析到 {len(news_items)} 条新闻")
            return news_items
            
        except Exception as e:
            logger.error(f"华尔街见闻({self.source_type}): 解析JSON数据失败 - {e}")
            return []
    
    async def fetch_news(self):
        """获取华尔街见闻新闻数据"""
        try:
            # 使用父类的方法获取数据
            response = await self.fetch_json(
                self.url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Referer": "https://wallstreetcn.com/"
                }
            )
            
            if response:
                items = await self.parse_json_response(response)
                if items:
                    logger.success(f"成功获取 {len(items)} 条 华尔街见闻({self.source_type}) 新闻")
                    return self.create_success_response(items)
                else:
                    logger.info(f"华尔街见闻({self.source_type}) 没有新数据")
                    return self.create_success_response([])
            else:
                logger.error(f"华尔街见闻({self.source_type}): 获取数据失败")
                return self.create_error_response("获取数据失败")
                
        except Exception as e:
            logger.error(f"华尔街见闻({self.source_type}): 获取新闻失败 - {e}")
            return self.create_error_response(str(e))


# 创建不同类型的华尔街见闻新闻源实例
wallstreetcn_quick_source = WallstreetcnSource("quick")
wallstreetcn_news_source = WallstreetcnSource("news")
wallstreetcn_hot_source = WallstreetcnSource("hot")


# 导出获取函数
async def get_wallstreetcn_quick_news():
    """获取华尔街见闻快讯"""
    return await wallstreetcn_quick_source.fetch_news()


async def get_wallstreetcn_news():
    """获取华尔街见闻新闻"""
    return await wallstreetcn_news_source.fetch_news()


async def get_wallstreetcn_hot_news():
    """获取华尔街见闻热门"""
    return await wallstreetcn_hot_source.fetch_news()


# 统一的获取函数
async def wallstreetcn_getter():
    """华尔街见闻新闻获取器(默认快讯)"""
    return await get_wallstreetcn_quick_news()


async def wallstreetcn_quick_getter():
    """华尔街见闻快讯获取器"""
    return await get_wallstreetcn_quick_news()


async def wallstreetcn_news_getter():
    """华尔街见闻新闻获取器"""
    return await get_wallstreetcn_news()


async def wallstreetcn_hot_getter():
    """华尔街见闻热门获取器"""
    return await get_wallstreetcn_hot_news()