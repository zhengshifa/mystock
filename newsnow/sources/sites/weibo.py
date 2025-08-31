"""微博热搜新闻源"""

import json
from typing import List, Dict, Any
from datetime import datetime

from sources.base import JSONSource
from database.models import NewsItem
from utils.logger import get_logger

logger = get_logger(__name__)


class WeiboSource(JSONSource):
    """微博热搜新闻源"""
    
    def __init__(self):
        super().__init__("weibo", "微博热搜", "https://weibo.com/ajax/side/hotSearch")
        self.interval = 300  # 5分钟
    
    def parse_json_response(self, data: Dict[str, Any]) -> List[NewsItem]:
        """解析微博热搜JSON响应"""
        items = []
        
        # 获取热搜数据
        realtime_data = data.get('data', {}).get('realtime', [])
        if not realtime_data:
            logger.warning("微博热搜realtime数据为空")
            return items
        
        for i, item in enumerate(realtime_data):
            try:
                # 提取基本信息
                word = item.get('word', '').strip()
                if not word:
                    continue
                    
                # 构建URL
                word_scheme = item.get('word_scheme', f"#{word}#")
                url = f"https://s.weibo.com/weibo?q={word_scheme}"
                
                # 获取热度和其他信息
                raw_hot = item.get('raw_hot', 0)
                num = item.get('num', 0)
                rank = item.get('rank', i + 1)
                
                # 获取标签信息
                label_name = item.get('label_name', '')
                emoticon = item.get('emoticon', '')
                
                # 构建extra信息
                extra = {
                    'rank': rank,
                    'hot': raw_hot,
                    'num': num
                }
                
                if label_name:
                    extra['label'] = label_name
                if emoticon:
                    extra['emoticon'] = emoticon
                    
                # 创建新闻条目
                news_item = self.create_news_item(
                    title=word,
                    url=url,
                    description=f"热度: {raw_hot}",
                    extra=extra
                )
                
                items.append(news_item)
                
            except Exception as e:
                logger.warning(f"解析单个微博热搜条目失败: {e}")
                continue
        
        return items


# 创建实例
weibo_source = WeiboSource()


async def weibo_getter():
    """微博热搜获取器"""
    return await weibo_source.fetch_news()