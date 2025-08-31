"""中国政府网政策新闻源实现"""

from datetime import datetime
from typing import List, Dict, Any
from bs4 import BeautifulSoup
import re

from sources.base import RSSSource
from database.models import NewsItem, SourceResponse
from utils.logger import get_logger

logger = get_logger(__name__)


class GovPolicySource(RSSSource):
    """中国政府网政策新闻源"""
    
    def __init__(self):
        """初始化政府政策新闻源"""
        source_id = "gov-policy"
        name = "中国政府网政策"
        url = "https://rsshub.app/gov/zhengce/zuixin"
        super().__init__(source_id, name, url)
        self.base_url = "https://www.gov.cn"
        self.interval = 600  # 10分钟
    
    async def fetch_news(self):
        """获取政府政策新闻"""
        try:
            # 使用父类的RSS获取方法
            feed = await self.fetch_rss(self.url)
            
            if feed and feed.entries:
                items = []
                max_items = self.config.get("MAX_NEWS_PER_SOURCE", 20)
                
                for entry in feed.entries[:max_items]:
                    try:
                        news_item = self.parse_rss_item(entry)
                        if news_item.title and news_item.url:
                            items.append(news_item)
                    except Exception as e:
                        logger.warning(f"解析政府政策RSS条目失败: {e}")
                        continue
                
                if items:
                    logger.success(f"成功获取 {len(items)} 条 政府政策 新闻")
                    return self.create_success_response(items)
                else:
                    logger.info("政府政策 没有新数据")
                    return self.create_success_response([])
            else:
                logger.info("政府政策 RSS数据为空")
                return self.create_success_response([])
                
        except Exception as e:
            logger.error(f"政府政策: 获取新闻失败 - {e}")
            return self.create_error_response(str(e))
    
    def parse_rss_item(self, entry) -> NewsItem:
        """解析RSS条目为新闻项"""
        try:
            # 提取标题
            title = entry.title if hasattr(entry, 'title') else ""
            
            # 提取链接
            url = entry.link if hasattr(entry, 'link') else ""
            
            # 提取发布时间
            published_at = datetime.now()
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published_at = datetime(*entry.published_parsed[:6])
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                published_at = datetime(*entry.updated_parsed[:6])
            
            # 提取描述内容
            description = ""
            if hasattr(entry, 'summary') and entry.summary:
                # 清理HTML标签
                soup = BeautifulSoup(entry.summary, 'html.parser')
                description = soup.get_text(strip=True)
                # 限制描述长度
                if len(description) > 200:
                    description = description[:200] + "..."
            
            # 提取作者信息
            author = ""
            if hasattr(entry, 'author') and entry.author:
                author = entry.author
            
            # 创建新闻项
            news_item = NewsItem(
                title=title,
                url=url,
                source_id=self.source_id,
                description=description,
                author=author,
                published_at=published_at,
                extra={
                    "type": "policy",
                    "source": "中国政府网",
                    "category": "政策法规"
                }
            )
            
            return news_item
            
        except Exception as e:
            logger.error(f"解析政府政策RSS条目失败: {e}")
            raise


# 创建政府政策新闻源实例
gov_policy_source = GovPolicySource()


# 导出获取函数
async def get_gov_policy_news():
    """获取政府政策新闻"""
    return await gov_policy_source.fetch_news()


# 统一的获取函数
async def gov_policy_getter():
    """政府政策新闻获取器"""
    return await get_gov_policy_news()


async def gov_zhengce_getter():
    """政府政策获取器(兼容性函数)"""
    return await gov_policy_getter()
