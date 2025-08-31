"""V2EX 新闻源实现"""

import json
import asyncio
from datetime import datetime
from typing import List, Dict, Any

from sources.base import BaseSource
from utils.fetch import get
from utils.logger import get_logger

logger = get_logger(__name__)


class V2exSource(BaseSource):
    """V2EX 新闻源"""
    
    def __init__(self):
        super().__init__("v2ex", "V2EX", "https://www.v2ex.com")
        self.base_url = "https://www.v2ex.com"
        self.interval = 300  # 5分钟
        self.feeds = ["create", "ideas", "programmer", "share"]
    
    async def fetch_feed(self, feed_name: str) -> List[Dict[str, Any]]:
        """获取单个feed的数据"""
        try:
            url = f"{self.base_url}/feed/{feed_name}.json"
            response = await get(url)
            
            if not response:
                logger.warning(f"获取 {feed_name} feed 失败")
                return []
            
            data = response.json() if hasattr(response, 'json') else json.loads(response.text)
            items = data.get('items', [])
            
            news_list = []
            for item in items:
                try:
                    item_id = item.get('id')
                    title = item.get('title')
                    url = item.get('url')
                    date_published = item.get('date_published')
                    date_modified = item.get('date_modified')
                    
                    if not all([item_id, title, url]):
                        continue
                    
                    # 使用修改时间或发布时间
                    date_str = date_modified or date_published
                    pub_date = int(datetime.now().timestamp() * 1000)
                    
                    if date_str:
                        try:
                            # 解析ISO格式时间
                            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                            pub_date = int(dt.timestamp() * 1000)
                        except Exception as e:
                            logger.warning(f"解析时间失败: {date_str}, 错误: {e}")
                    
                    news_item = {
                        'id': item_id,
                        'title': title,
                        'url': url,
                        'published_at': pub_date,
                        'source_id': self.source_id,
                        'extra': {
                            'date': date_str,
                            'feed': feed_name
                        }
                    }
                    
                    news_list.append(news_item)
                    
                except Exception as e:
                    logger.warning(f"解析 {feed_name} 单个条目失败: {e}")
                    continue
            
            return news_list
            
        except Exception as e:
            logger.error(f"获取 {feed_name} feed 失败: {e}")
            return []
    
    async def fetch_news(self):
        """获取 V2EX 新闻"""
        try:
            logger.info(f"开始获取 {self.name} 新闻")
            
            all_news = []
            
            # 并发获取所有feeds
            import asyncio
            tasks = [self.fetch_feed(feed) for feed in self.feeds]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"获取 {self.feeds[i]} feed 失败: {result}")
                    continue
                
                if isinstance(result, list):
                    all_news.extend(result)
            
            # 按时间排序，最新的在前
            all_news.sort(key=lambda x: x.get('published_at', 0), reverse=True)
            
            # 去重，保留最新的
            seen_ids = set()
            unique_news = []
            for news in all_news:
                news_id = news.get('id')
                if news_id not in seen_ids:
                    seen_ids.add(news_id)
                    unique_news.append(news)
            
            # 转换为NewsItem对象
            items = []
            for news_data in unique_news:
                item = self.create_news_item(
                    title=news_data.get('title', ''),
                    url=news_data.get('url', ''),
                    description=news_data.get('content', ''),
                    author=news_data.get('member', {}).get('username', ''),
                    published_at=datetime.fromtimestamp(news_data.get('published_at', 0)) if news_data.get('published_at') else None,
                    extra={
                        'replies': news_data.get('replies', 0),
                        'node': news_data.get('node', {})
                    }
                )
                items.append(item)
            
            # 限制条目数量
            max_items = self.config.get("MAX_NEWS_PER_SOURCE", 50)
            items = items[:max_items]
            
            logger.info(f"成功获取 {len(items)} 条 {self.name} 新闻")
            return self.create_success_response(items)
            
        except Exception as e:
            error_msg = f"获取 {self.name} 新闻失败: {e}"
            logger.error(error_msg)
            return self.create_error_response(error_msg)


class V2exShareSource(BaseSource):
    """V2EX Share分类新闻源"""
    
    def __init__(self):
        super().__init__("v2ex-share", "V2EX Share", "https://www.v2ex.com")
        self.base_url = "https://www.v2ex.com"
        self.interval = 300  # 5分钟
        self.feeds = ["share"]  # 只获取share分类
    
    async def fetch_feed(self, feed_name: str) -> List[Dict[str, Any]]:
        """获取单个feed的数据"""
        try:
            url = f"{self.base_url}/feed/{feed_name}.json"
            response = await get(url)
            
            if not response:
                return []
            
            data = response.json() if hasattr(response, 'json') else json.loads(response.text)
            return data if isinstance(data, list) else []
            
        except Exception as e:
            logger.error(f"获取V2EX feed {feed_name}失败: {e}")
            return []
    
    async def fetch_news(self):
        """获取V2EX Share分类新闻"""
        try:
            logger.info(f"开始获取 {self.name} 新闻")
            
            all_items = []
            
            # 获取所有feed的数据
            for feed_name in self.feeds:
                items = await self.fetch_feed(feed_name)
                all_items.extend(items)
            
            if not all_items:
                return self.create_success_response([])
            
            # 按时间排序，取最新的20条
            all_items.sort(key=lambda x: x.get('created', 0), reverse=True)
            all_items = all_items[:20]
            
            news_items = []
            for item in all_items:
                try:
                    news_item = self.create_news_item(
                        title=item.get('title', ''),
                        url=f"{self.base_url}/t/{item.get('id', '')}",
                        published_at=datetime.fromtimestamp(item.get('created', 0)),
                        description=item.get('content_rendered', '')[:200] + '...' if item.get('content_rendered') else '',
                        author=item.get('member', {}).get('username', ''),
                        extra={
                            'node': item.get('node', {}).get('title', ''),
                            'replies': item.get('replies', 0)
                        }
                    )
                    news_items.append(news_item)
                except Exception as e:
                    logger.error(f"处理V2EX新闻项失败: {e}")
                    continue
            
            logger.info(f"成功获取 {len(news_items)} 条 {self.name} 新闻")
            return self.create_success_response(news_items)
            
        except Exception as e:
            logger.error(f"获取 {self.name} 新闻失败: {e}")
            return self.create_error_response(str(e))


# 创建实例
v2ex_source = V2exSource()
v2ex_share_source = V2exShareSource()


async def v2ex_getter():
    """V2EX获取器"""
    return await v2ex_source.fetch_news()


async def get_v2ex_latest_news():
    """获取V2EX最新新闻（兼容旧接口）"""
    return await v2ex_getter()


async def v2ex_share_getter():
    """V2EX Share获取器"""
    return await v2ex_share_source.fetch_news()