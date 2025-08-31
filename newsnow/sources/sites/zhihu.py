"""知乎热榜新闻源"""

import json
import re
from datetime import datetime
from typing import List, Dict, Any

from sources.base import JSONSource
from database.models import NewsItem
from utils.logger import get_logger

logger = get_logger(__name__)

class ZhihuSource(JSONSource):
    """知乎热榜新闻源"""
    
    def __init__(self):
        super().__init__("zhihu", "知乎热榜", "https://www.zhihu.com")
        self.base_url = "https://www.zhihu.com"
        self.interval = 600  # 10分钟
    
    def parse_json_response(self, data: Dict[str, Any]) -> List[NewsItem]:
        """解析知乎热榜JSON响应"""
        items = []
        data_list = data.get("data", [])
        
        for item in data_list:
            try:
                # 检查数据结构
                if item.get('type') != 'hot_list_feed':
                    continue
                
                target = item.get('target', {})
                if not target:
                    continue
                
                # 获取标题
                title_area = target.get('title_area', {})
                title = title_area.get('text', '').strip()
                
                if not title:
                    continue
                
                # 获取链接
                link_info = target.get('link', {})
                url = link_info.get('url', '')
                
                if not url:
                    continue
                
                # 获取热度信息
                metrics_area = target.get('metrics_area', {})
                metrics_text = metrics_area.get('text', '')
                
                # 获取摘要
                excerpt_area = target.get('excerpt_area', {})
                excerpt = excerpt_area.get('text', '').strip()
                
                # 获取趋势信息
                label_area = target.get('label_area', {})
                trend = label_area.get('trend', 0)
                
                # 创建新闻条目
                news_item = self.create_news_item(
                    title=title,
                    url=url,
                    description=excerpt,
                    extra={
                        'info': metrics_text,
                        'hover': excerpt,
                        'trend': trend,
                        'ranking': len(items) + 1
                    }
                )
                
                items.append(news_item)
                
            except Exception as e:
                logger.warning(f"解析单个知乎热榜条目失败: {e}")
                continue
        
        return items
    
    async def fetch_news(self):
        """获取知乎热榜新闻"""
        try:
            logger.info(f"开始获取 {self.name} 新闻")
            
            # 知乎热榜API
            api_url = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=50&desktop=true"
            
            json_data = await self.fetch_json(api_url)
            if not json_data:
                return self.create_error_response("获取JSON数据失败")
            
            items = self.parse_json_response(json_data)
            
            # 限制条目数量
            max_items = self.config.get("MAX_NEWS_PER_SOURCE", 50)
            items = items[:max_items]
            
            logger.info(f"成功获取 {len(items)} 条 {self.name} 新闻")
            return self.create_success_response(items)
            
        except Exception as e:
            error_msg = f"获取 {self.name} 新闻失败: {e}"
            logger.error(error_msg)
            return self.create_error_response(error_msg)


# 创建实例并导出函数
zhihu_source = ZhihuSource()

async def zhihu_getter():
    """获取知乎热榜新闻"""
    return await zhihu_source.fetch_news()

async def get_zhihu_news():
    """获取知乎热榜新闻 (兼容旧接口)"""
    return await zhihu_source.fetch_news()