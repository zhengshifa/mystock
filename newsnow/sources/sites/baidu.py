"""百度热搜新闻源"""

import json
import re
from typing import List
from datetime import datetime

from sources.base import HTMLSource
from database.models import NewsItem
from utils.logger import get_logger

logger = get_logger(__name__)


class BaiduSource(HTMLSource):
    """百度热搜新闻源"""
    
    def __init__(self):
        super().__init__("baidu", "百度热搜", "https://top.baidu.com/board?tab=realtime")
        self.interval = 300  # 5分钟
    
    async def fetch_news(self):
        """获取百度热搜新闻"""
        try:
            html_content = await self.fetcher.get_text(self.url)
            items = self.parse_html_response(html_content)
            
            # 限制条目数量
            max_items = self.config.get("MAX_NEWS_PER_SOURCE", 50)
            items = items[:max_items]
            
            logger.info(f"成功获取百度热搜 {len(items)} 条新闻")
            return self.create_success_response(items)
            
        except Exception as e:
            error_msg = f"获取百度热搜失败: {e}"
            logger.error(error_msg)
            return self.create_error_response(error_msg)
    
    def parse_html_response(self, html: str) -> List[NewsItem]:
        """解析百度热搜HTML响应"""
        items = []
        
        try:
            # 提取JSON数据
            json_match = re.search(r'<!--s-data:(.*?)-->', html, re.DOTALL)
            if not json_match:
                logger.warning("未找到百度热搜数据")
                return items
            
            data = json.loads(json_match.group(1))
            
            # 获取热搜数据
            cards = data.get('data', {}).get('cards', [])
            if not cards:
                logger.warning("百度热搜cards数据为空")
                return items
            
            # 查找实时热点卡片
            realtime_card = None
            for card in cards:
                if card.get('type') == 'realtime':
                    realtime_card = card
                    break
            
            if not realtime_card:
                logger.warning("未找到百度实时热点卡片")
                return items
            
            content_list = realtime_card.get('content', [])
            
            for i, item in enumerate(content_list):
                try:
                    # 提取基本信息
                    query = item.get('query', '').strip()
                    if not query:
                        continue
                    
                    # 构建URL
                    url = item.get('url', '')
                    if not url:
                        # 如果没有直接URL，构建搜索URL
                        url = f"https://www.baidu.com/s?wd={query}"
                    
                    # 获取热度和排名
                    hot_score = item.get('hotScore', 0)
                    index = item.get('index', i + 1)
                    
                    # 获取描述
                    desc = item.get('desc', '')
                    
                    # 构建extra信息
                    extra = {
                        'rank': index,
                        'hot_score': hot_score
                    }
                    
                    if desc:
                        extra['desc'] = desc
                    
                    # 创建新闻条目
                    news_item = self.create_news_item(
                        title=query,
                        url=url,
                        description=desc or f"热度: {hot_score}",
                        extra=extra
                    )
                    
                    items.append(news_item)
                    
                except Exception as e:
                    logger.warning(f"解析单个百度热搜条目失败: {e}")
                    continue
            
        except json.JSONDecodeError as e:
            logger.error(f"解析百度热搜JSON失败: {e}")
        except Exception as e:
            logger.error(f"解析百度热搜HTML失败: {e}")
        
        return items


# 创建实例
baidu_source = BaiduSource()


async def baidu_getter():
    """百度热搜获取器"""
    return await baidu_source.fetch_news()