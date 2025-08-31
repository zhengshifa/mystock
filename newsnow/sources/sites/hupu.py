"""虎扑新闻源"""

import re
from typing import List
from datetime import datetime
from bs4 import BeautifulSoup

from sources.base import HTMLSource
from database.models import NewsItem, SourceResponse
from utils.logger import get_logger

logger = get_logger(__name__)


class HupuSource(HTMLSource):
    """虎扑新闻源"""
    
    def __init__(self):
        super().__init__("hupu", "虎扑", "https://bbs.hupu.com/topic-daily-hot")
        self.interval = 300  # 5分钟
    
    def parse_html_response(self, html: str) -> List[NewsItem]:
        """解析虎扑HTML响应"""
        items = []
        
        try:
            # 使用正则表达式匹配热榜项结构
            pattern = r'<li class="bbs-sl-web-post-body">[\s\S]*?<a href="(\/[^"]+?\.html)"[^>]*?class="p-title"[^>]*>([^<]+)<\/a>'
            matches = re.findall(pattern, html)
            
            for i, (path, title) in enumerate(matches):
                try:
                    # 构建完整URL
                    url = f"https://bbs.hupu.com{path}"
                    
                    # 清理标题
                    title = title.strip()
                    if not title:
                        continue
                    
                    # 构建extra信息
                    extra = {
                        'rank': i + 1
                    }
                    
                    # 创建新闻条目
                    news_item = self.create_news_item(
                        title=title,
                        url=url,
                        description=f"虎扑热榜第{i+1}名",
                        extra=extra
                    )
                    
                    items.append(news_item)
                    
                except Exception as e:
                    logger.warning(f"解析单个虎扑条目失败: {e}")
                    continue
            
            # 如果正则匹配失败，尝试使用BeautifulSoup
            if not items:
                soup = BeautifulSoup(html, 'html.parser')
                
                # 查找热榜条目
                post_items = soup.find_all('li', class_='bbs-sl-web-post-body')
                
                for i, item in enumerate(post_items):
                    try:
                        # 提取标题和链接
                        title_elem = item.find('a', class_='p-title')
                        if not title_elem:
                            continue
                        
                        title = title_elem.get_text(strip=True)
                        path = title_elem.get('href', '')
                        
                        if not title or not path:
                            continue
                        
                        # 构建完整URL
                        if path.startswith('/'):
                            url = f"https://bbs.hupu.com{path}"
                        else:
                            url = path
                        
                        # 构建extra信息
                        extra = {
                            'rank': i + 1
                        }
                        
                        # 创建新闻条目
                        news_item = self.create_news_item(
                            title=title,
                            url=url,
                            description=f"虎扑热榜第{i+1}名",
                            extra=extra
                        )
                        
                        items.append(news_item)
                        
                    except Exception as e:
                        logger.warning(f"解析单个虎扑条目失败: {e}")
                        continue
            
        except Exception as e:
            logger.error(f"解析虎扑HTML失败: {e}")
        
        return items
    
    async def fetch_news(self) -> SourceResponse:
        """获取虎扑新闻"""
        try:
            # 获取HTML内容
            html = await self.fetch_html(self.url)
            
            # 解析HTML
            items = self.parse_html_response(str(html))
            
            if items:
                logger.success(f"成功获取 {len(items)} 条 虎扑 新闻")
                return self.create_success_response(items)
            else:
                logger.info("虎扑 没有新数据")
                return self.create_success_response([])
                
        except Exception as e:
            logger.error(f"获取 虎扑 新闻失败: {e}")
            return self.create_error_response(str(e))


# 创建实例
hupu_source = HupuSource()


async def hupu_getter():
    """虎扑获取器"""
    return await hupu_source.fetch_news()