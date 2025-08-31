"""Solidot 新闻源实现"""

import re
from datetime import datetime
from typing import List, Dict, Any
from bs4 import BeautifulSoup

from sources.base import BaseSource
from utils.fetch import get_text
from utils.logger import get_logger

logger = get_logger(__name__)


class SolidotSource(BaseSource):
    """Solidot 新闻源"""
    
    def __init__(self):
        super().__init__("solidot", "Solidot", "https://www.solidot.org")
        self.base_url = "https://www.solidot.org"
        self.interval = 300  # 5分钟
    
    def parse_relative_date(self, date_str: str) -> int:
        """解析相对时间字符串"""
        try:
            # 处理格式如: "2024年01月15日 14时30分"
            date_clean = date_str.replace("年", "-").replace("月", "-").replace("日", " ")
            date_clean = date_clean.replace("时", ":").replace("分", "")
            
            # 解析日期时间
            dt = datetime.strptime(date_clean.strip(), "%Y-%m-%d %H:%M")
            return int(dt.timestamp() * 1000)
        except Exception as e:
            logger.warning(f"解析日期失败: {date_str}, 错误: {e}")
            return int(datetime.now().timestamp() * 1000)
    
    async def fetch_news(self):
        """获取 Solidot 新闻"""
        try:
            logger.info(f"开始获取 {self.name} 新闻")
            
            html = await get_text(self.base_url)
            if not html:
                raise Exception("获取HTML内容失败")
            
            soup = BeautifulSoup(html, 'html.parser')
            news_blocks = soup.find_all('div', class_='block_m')
            
            if not news_blocks:
                raise Exception("未找到新闻块")
            
            news_list = []
            
            for block in news_blocks:
                try:
                    # 查找标题链接
                    title_link = block.find('div', class_='bg_htit')
                    if not title_link:
                        continue
                    
                    link_elem = title_link.find('a')
                    if not link_elem:
                        continue
                    
                    url = link_elem.get('href')
                    title = link_elem.get_text(strip=True)
                    
                    if not url or not title:
                        continue
                    
                    # 查找时间
                    time_elem = block.find('div', class_='talk_time')
                    date_str = ""
                    pub_date = int(datetime.now().timestamp() * 1000)
                    
                    if time_elem:
                        time_text = time_elem.get_text(strip=True)
                        # 提取时间部分，格式如: "发表于2024年01月15日 14时30分"
                        date_match = re.search(r'发表于(.*?分)', time_text)
                        if date_match:
                            date_str = date_match.group(1)
                            pub_date = self.parse_relative_date(date_str)
                    
                    # 构建完整URL
                    full_url = self.base_url + url if url.startswith('/') else url
                    
                    news_item = {
                        'id': url,
                        'title': title,
                        'url': full_url,
                        'published_at': pub_date,
                        'source_id': self.source_id,
                        'extra': {
                            'date': date_str
                        }
                    }
                    
                    news_list.append(news_item)
                    
                except Exception as e:
                    logger.warning(f"解析单个新闻项失败: {e}")
                    continue
            
            # 转换为NewsItem对象
            items = []
            for news_data in news_list:
                item = self.create_news_item(
                    title=news_data.get('title', ''),
                    url=news_data.get('url', ''),
                    published_at=datetime.fromtimestamp(news_data.get('published_at', 0) / 1000) if news_data.get('published_at') else None,
                    extra=news_data.get('extra', {})
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


# 创建实例并导出函数
solidot_source = SolidotSource()

async def solidot_getter():
    """获取Solidot新闻"""
    return await solidot_source.fetch_news()

async def get_solidot_news():
    """获取Solidot新闻 (兼容旧接口)"""
    return await solidot_source.fetch_news()