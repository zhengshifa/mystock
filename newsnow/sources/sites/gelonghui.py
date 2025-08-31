"""格隆汇新闻源实现"""

import re
from datetime import datetime, timedelta
from typing import List, Dict, Any
from bs4 import BeautifulSoup

from sources.base import HTMLSource
from database.models import NewsItem, SourceResponse
from utils.logger import get_logger

logger = get_logger(__name__)


class GelonghuiSource(HTMLSource):
    """格隆汇新闻源"""
    
    def __init__(self):
        """初始化格隆汇新闻源"""
        super().__init__("gelonghui", "格隆汇", "https://www.gelonghui.com/news/")
        self.base_url = "https://www.gelonghui.com"
        self.interval = 120  # 2分钟
    
    def parse_relative_date(self, relative_time: str) -> datetime:
        """解析相对时间字符串"""
        try:
            now = datetime.now()
            
            # 匹配各种时间格式
            if "刚刚" in relative_time or "刚才" in relative_time:
                return now
            elif "分钟前" in relative_time:
                minutes = int(re.search(r'(\d+)分钟前', relative_time).group(1))
                return now - timedelta(minutes=minutes)
            elif "小时前" in relative_time:
                hours = int(re.search(r'(\d+)小时前', relative_time).group(1))
                return now - timedelta(hours=hours)
            elif "天前" in relative_time or "日前" in relative_time:
                days = int(re.search(r'(\d+)[天日]前', relative_time).group(1))
                return now - timedelta(days=days)
            elif "昨天" in relative_time:
                return now - timedelta(days=1)
            elif "前天" in relative_time:
                return now - timedelta(days=2)
            else:
                # 尝试解析具体日期格式
                date_match = re.search(r'(\d{4})[-/年](\d{1,2})[-/月](\d{1,2})', relative_time)
                if date_match:
                    year, month, day = map(int, date_match.groups())
                    return datetime(year, month, day)
                
                # 如果无法解析，返回当前时间
                return now
        except Exception as e:
            logger.warning(f"格隆汇: 解析时间失败 '{relative_time}' - {e}")
            return datetime.now()
    
    async def parse_html_response(self, html: str) -> List[NewsItem]:
        """解析格隆汇HTML响应"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            news_items = []
            
            # 查找新闻容器
            main_containers = soup.find_all(class_="article-content")
            
            for container in main_containers:
                try:
                    # 查找链接和标题
                    link_element = container.find(class_="detail-right")
                    if not link_element:
                        continue
                    
                    a_tag = link_element.find("a")
                    if not a_tag:
                        continue
                    
                    url_path = a_tag.get("href")
                    if not url_path:
                        continue
                    
                    # 构建完整URL
                    url = self.base_url + url_path if url_path.startswith("/") else url_path
                    
                    # 获取标题
                    title_element = a_tag.find("h2")
                    if not title_element:
                        continue
                    
                    title = title_element.get_text(strip=True)
                    if not title:
                        continue
                    
                    # 获取时间信息
                    time_element = container.find(class_="time")
                    published_at = datetime.now()
                    info = ""
                    
                    if time_element:
                        # 获取第一个span的内容作为info
                        info_span = time_element.find("span")
                        if info_span:
                            info = info_span.get_text(strip=True)
                        
                        # 获取第三个span的内容作为时间
                        time_spans = time_element.find_all("span")
                        if len(time_spans) >= 3:
                            relative_time = time_spans[2].get_text(strip=True)
                            published_at = self.parse_relative_date(relative_time)
                    
                    # 创建新闻项
                    news_item = NewsItem(
                        title=title,
                        url=url,
                        source_id=self.source_id,
                        description="",
                        published_at=published_at,
                        extra={
                            "type": "realtime",
                            "info": info
                        }
                    )
                    news_items.append(news_item)
                    
                except Exception as e:
                    logger.warning(f"格隆汇: 解析单条新闻失败 - {e}")
                    continue
            
            logger.info(f"格隆汇: 解析到 {len(news_items)} 条新闻")
            return news_items
            
        except Exception as e:
            logger.error(f"格隆汇: 解析HTML失败 - {e}")
            return []
    
    async def fetch_news(self) -> SourceResponse:
        """获取格隆汇新闻"""
        try:
            # 获取HTML内容
            html = await self.fetch_html(self.url)
            
            # 解析HTML
            items = await self.parse_html_response(str(html))
            
            if items:
                logger.success(f"成功获取 {len(items)} 条 格隆汇 新闻")
                return self.create_success_response(items)
            else:
                logger.info("格隆汇 没有新数据")
                return self.create_success_response([])
                
        except Exception as e:
            logger.error(f"获取 格隆汇 新闻失败: {e}")
            return self.create_error_response(str(e))


# 创建格隆汇新闻源实例
gelonghui_source = GelonghuiSource()


# 导出获取函数
async def get_gelonghui_news():
    """获取格隆汇新闻"""
    return await gelonghui_source.fetch_news()


# 统一的获取函数
async def gelonghui_getter():
    """格隆汇新闻获取器"""
    return await get_gelonghui_news()