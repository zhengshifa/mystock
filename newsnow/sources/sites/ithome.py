"""IT之家新闻源"""

import re
from typing import List
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

from sources.base import HTMLSource
from database.models import NewsItem, SourceResponse
from utils.logger import get_logger

logger = get_logger(__name__)


class IthomeSource(HTMLSource):
    """IT之家新闻源"""
    
    def __init__(self):
        super().__init__("ithome", "IT之家", "https://www.ithome.com/list/")
        self.interval = 300  # 5分钟
        
    def parse_relative_date(self, date_str: str) -> datetime:
        """解析相对时间字符串"""
        now = datetime.now()
        
        # 匹配各种时间格式
        if "刚刚" in date_str or "刚才" in date_str:
            return now
        elif "分钟前" in date_str:
            minutes = re.search(r'(\d+)分钟前', date_str)
            if minutes:
                return now - timedelta(minutes=int(minutes.group(1)))
        elif "小时前" in date_str:
            hours = re.search(r'(\d+)小时前', date_str)
            if hours:
                return now - timedelta(hours=int(hours.group(1)))
        elif "天前" in date_str:
            days = re.search(r'(\d+)天前', date_str)
            if days:
                return now - timedelta(days=int(days.group(1)))
        elif "昨天" in date_str:
            return now - timedelta(days=1)
        elif "前天" in date_str:
            return now - timedelta(days=2)
        
        # 尝试解析具体日期格式 (如: 2024/1/15)
        date_match = re.search(r'(\d{4})/(\d{1,2})/(\d{1,2})', date_str)
        if date_match:
            year, month, day = map(int, date_match.groups())
            return datetime(year, month, day)
        
        return now
        
    def is_ad(self, url: str, title: str) -> bool:
        """判断是否为广告"""
        ad_keywords = [
            '广告', '推广', '赞助', '合作', '活动',
            '优惠', '折扣', '促销', '特价', '限时'
        ]
        
        # 检查标题中是否包含广告关键词
        for keyword in ad_keywords:
            if keyword in title:
                return True
        
        # 检查URL中是否包含广告标识
        if 'ad' in url.lower() or 'promo' in url.lower():
            return True
            
        return False
    
    def parse_html_response(self, html: str) -> List[NewsItem]:
        """解析IT之家HTML响应"""
        items = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # 查找新闻条目
            news_items = soup.find_all('div', class_='bl')
            
            for item in news_items:
                try:
                    # 提取标题和链接
                    title_elem = item.find('a')
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    url = title_elem.get('href', '')
                    
                    if not title or not url:
                        continue
                    
                    # 过滤广告
                    if self.is_ad(url, title):
                        continue
                    
                    # 确保URL是完整的
                    if url.startswith('/'):
                        url = f"https://www.ithome.com{url}"
                    elif not url.startswith('http'):
                        url = f"https://www.ithome.com/{url}"
                    
                    # 提取时间
                    time_elem = item.find('span', class_='time')
                    pub_date = datetime.now()
                    if time_elem:
                        time_text = time_elem.get_text(strip=True)
                        pub_date = self.parse_relative_date(time_text)
                    
                    # 提取摘要
                    desc_elem = item.find('div', class_='desc')
                    description = ""
                    if desc_elem:
                        description = desc_elem.get_text(strip=True)[:200]
                    
                    # 提取评论数
                    comment_elem = item.find('span', class_='comment')
                    comment_count = 0
                    if comment_elem:
                        comment_text = comment_elem.get_text(strip=True)
                        comment_match = re.search(r'(\d+)', comment_text)
                        if comment_match:
                            comment_count = int(comment_match.group(1))
                    
                    # 构建extra信息
                    extra = {}
                    if comment_count > 0:
                        extra['comment_count'] = comment_count
                    
                    # 创建新闻条目
                    news_item = self.create_news_item(
                        title=title,
                        url=url,
                        description=description,
                        published_at=pub_date,
                        extra=extra
                    )
                    
                    items.append(news_item)
                    
                except Exception as e:
                    logger.warning(f"解析单个IT之家条目失败: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"解析IT之家HTML失败: {e}")
        
        return items
    
    async def fetch_news(self) -> SourceResponse:
        """获取IT之家新闻"""
        try:
            # 获取HTML内容
            html = await self.fetch_html(self.url)
            
            # 解析HTML
            items = self.parse_html_response(str(html))
            
            if items:
                logger.success(f"成功获取 {len(items)} 条 IT之家 新闻")
                return self.create_success_response(items)
            else:
                logger.info("IT之家 没有新数据")
                return self.create_success_response([])
                
        except Exception as e:
            logger.error(f"获取 IT之家 新闻失败: {e}")
            return self.create_error_response(str(e))


# 创建实例
ithome_source = IthomeSource()


async def ithome_getter():
    """IT之家获取器"""
    return await ithome_source.fetch_news()