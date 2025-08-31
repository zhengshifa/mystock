"""36氪新闻源"""

import re
from typing import List
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

from sources.base import HTMLSource
from database.models import NewsItem
from utils.logger import get_logger

logger = get_logger(__name__)


class Kr36Source(HTMLSource):
    """36氪新闻源"""
    
    def __init__(self):
        super().__init__("36kr", "36氪", "https://www.36kr.com/newsflashes")
        self.interval = 300  # 5分钟
        
    def parse_relative_date(self, relative_str: str) -> datetime:
        """解析相对时间字符串"""
        now = datetime.now()
        
        # 匹配各种时间格式
        if "刚刚" in relative_str or "刚才" in relative_str:
            return now
        elif "分钟前" in relative_str:
            minutes = re.search(r'(\d+)分钟前', relative_str)
            if minutes:
                return now - timedelta(minutes=int(minutes.group(1)))
        elif "小时前" in relative_str:
            hours = re.search(r'(\d+)小时前', relative_str)
            if hours:
                return now - timedelta(hours=int(hours.group(1)))
        elif "天前" in relative_str:
            days = re.search(r'(\d+)天前', relative_str)
            if days:
                return now - timedelta(days=int(days.group(1)))
        elif "昨天" in relative_str:
            return now - timedelta(days=1)
        
        return now
    
    async def fetch_news(self):
        """获取36氪新闻"""
        try:
            html_content = await self.fetcher.get_text(self.url)
            items = self.parse_html_response(html_content)
            
            # 限制条目数量
            max_items = self.config.get("MAX_NEWS_PER_SOURCE", 50)
            items = items[:max_items]
            
            logger.info(f"成功获取36氪 {len(items)} 条新闻")
            return self.create_success_response(items)
            
        except Exception as e:
            error_msg = f"获取36氪新闻失败: {e}"
            logger.error(error_msg)
            return self.create_error_response(error_msg)
    
    def parse_html_response(self, html: str) -> List[NewsItem]:
        """解析36氪HTML响应"""
        items = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # 查找快讯条目
            news_items = soup.find_all('div', class_='newsflash-item')
            
            for item in news_items:
                try:
                    # 提取标题
                    title_elem = item.find('div', class_='title')
                    if not title_elem:
                        continue
                    title = title_elem.get_text(strip=True)
                    
                    # 提取链接
                    link_elem = item.find('a')
                    if link_elem and link_elem.get('href'):
                        url = link_elem['href']
                        if url.startswith('/'):
                            url = f"https://www.36kr.com{url}"
                    else:
                        url = self.base_url
                    
                    # 提取时间
                    time_elem = item.find('span', class_='time')
                    pub_date = datetime.now()
                    if time_elem:
                        time_text = time_elem.get_text(strip=True)
                        pub_date = self.parse_relative_date(time_text)
                    
                    # 提取内容摘要
                    content_elem = item.find('div', class_='content')
                    description = ""
                    if content_elem:
                        description = content_elem.get_text(strip=True)[:200]
                    
                    # 创建新闻条目
                    news_item = self.create_news_item(
                        title=title,
                        url=url,
                        description=description,
                        published_at=pub_date
                    )
                    
                    items.append(news_item)
                    
                except Exception as e:
                    logger.warning(f"解析单个36氪条目失败: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"解析36氪HTML失败: {e}")
        
        return items


# 创建实例
kr36_source = Kr36Source()


async def kr36_getter():
    """36氪获取器"""
    return await kr36_source.fetch_news()