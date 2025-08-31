"""路透社新闻源实现"""

import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

from sources.base import HTMLSource
from database.models import NewsItem, SourceResponse
from utils.logger import get_logger
from utils.fetch import get

logger = get_logger(__name__)


class ReutersSource(HTMLSource):
    """路透社新闻源"""
    
    def __init__(self):
        """初始化路透社新闻源"""
        source_id = "reuters"
        name = "Reuters"
        url = "https://www.reuters.com"
        super().__init__(source_id, name, url)
        self.base_url = "https://www.reuters.com"
        self.rss_url = "https://www.reuters.com/rssFeed/businessNews"
        self.interval = 300  # 5分钟
    
    async def fetch_news(self):
        """获取路透社新闻"""
        try:
            # 首先尝试从RSS获取新闻
            news_items = await self._fetch_from_rss()
            
            # 如果RSS失败或没有数据，尝试从主页获取
            if not news_items:
                logger.info("路透社: RSS获取失败，尝试从主页获取")
                news_items = await self._fetch_from_homepage()
            
            if news_items:
                logger.success(f"成功获取 {len(news_items)} 条 路透社 新闻")
                return self.create_success_response(news_items)
            else:
                logger.info("路透社 没有新数据")
                return self.create_success_response([])
            
        except Exception as e:
            logger.error(f"路透社: 获取新闻失败 - {e}")
            return self.create_error_response(str(e))
    
    async def _fetch_from_rss(self) -> List[NewsItem]:
        """从RSS获取新闻"""
        try:
            # 获取RSS XML
            response = await get(self.rss_url)
            if not response:
                return []
            
            xml_content = response.text if hasattr(response, 'text') else ''
            if not xml_content:
                return []
            
            # 解析XML
            root = ET.fromstring(xml_content)
            news_items = []
            
            # 查找所有item元素
            for item in root.findall('.//item'):
                try:
                    title_elem = item.find('title')
                    link_elem = item.find('link')
                    pub_date_elem = item.find('pubDate')
                    description_elem = item.find('description')
                    
                    if title_elem is None or link_elem is None:
                        continue
                    
                    title = title_elem.text
                    url = link_elem.text
                    
                    if not title or not url:
                        continue
                    
                    # 解析发布时间
                    published_at = datetime.now()
                    if pub_date_elem is not None and pub_date_elem.text:
                        try:
                            # RSS日期格式: Wed, 02 Oct 2002 13:00:00 GMT
                            from email.utils import parsedate_to_datetime
                            published_at = parsedate_to_datetime(pub_date_elem.text)
                        except Exception:
                            published_at = datetime.now()
                    
                    # 获取描述
                    content = ""
                    if description_elem is not None and description_elem.text:
                        content = description_elem.text
                    
                    # 创建新闻项
                    news_item = NewsItem(
                        source_id=self.source_id,
                        title=title,
                        url=url,
                        description=content,
                        published_at=published_at,
                        extra={
                            "type": "news",
                            "source": "rss"
                        }
                    )
                    news_items.append(news_item)
                    
                except Exception as e:
                    logger.warning(f"路透社: 解析RSS条目失败 - {e}")
                    continue
            
            # 按时间排序，取最新的20条
            news_items.sort(key=lambda x: x.published_at, reverse=True)
            return news_items[:20]
            
        except Exception as e:
            logger.error(f"路透社: 从RSS获取新闻失败 - {e}")
            return []
    
    async def _fetch_from_homepage(self) -> List[NewsItem]:
        """从主页获取新闻"""
        try:
            # 获取主页HTML
            response = await get(self.url)
            if not response:
                return []
            
            html_content = response.text if hasattr(response, 'text') else ''
            if not html_content:
                return []
            
            return await self.parse_html_response(html_content)
            
        except Exception as e:
            logger.error(f"路透社: 从主页获取新闻失败 - {e}")
            return []
    
    async def parse_html_response(self, html: str) -> List[NewsItem]:
        """解析路透社HTML响应"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            news_items = []
            
            # 查找新闻链接
            # 路透社使用多种选择器来标识新闻链接
            selectors = [
                'a[href*="/business/"]',
                'a[href*="/markets/"]',
                'a[href*="/world/"]',
                'a[href*="/technology/"]',
                '.story-title a',
                '.media-story-card__headline__eqhp9 a',
                '.text__text__1FZLe a'
            ]
            
            found_links = set()
            
            for selector in selectors:
                links = soup.select(selector)
                
                for link in links:
                    try:
                        href = link.get('href')
                        if not href:
                            continue
                        
                        # 构建完整URL
                        if href.startswith('/'):
                            url = self.base_url + href
                        elif href.startswith('http'):
                            url = href
                        else:
                            continue
                        
                        # 避免重复
                        if url in found_links:
                            continue
                        found_links.add(url)
                        
                        # 过滤非新闻链接
                        if not self._is_news_url(url):
                            continue
                        
                        # 获取标题
                        title = link.get_text(strip=True)
                        if not title:
                            title = self._extract_title_from_url(url)
                        
                        if not title or len(title) < 10:
                            continue
                        
                        # 清理标题
                        title = self._clean_title(title)
                        
                        # 创建新闻项
                        news_item = NewsItem(
                            source_id=self.source_id,
                            title=title,
                            url=url,
                            description="",
                            published_at=datetime.now(),
                            extra={
                                "type": "news",
                                "source": "homepage"
                            }
                        )
                        news_items.append(news_item)
                        
                    except Exception as e:
                        logger.warning(f"路透社: 解析单条新闻失败 - {e}")
                        continue
            
            logger.info(f"路透社: 从主页解析到 {len(news_items)} 条新闻")
            return news_items[:20]  # 限制数量
            
        except Exception as e:
            logger.error(f"路透社: 解析HTML失败 - {e}")
            return []
    
    def _extract_title_from_url(self, url: str) -> Optional[str]:
        """从URL提取标题"""
        try:
            # 提取URL路径的最后部分
            path_parts = url.rstrip('/').split('/')
            if len(path_parts) < 2:
                return None
            
            # 获取最后一部分作为标题基础
            title_part = path_parts[-1]
            
            # 移除日期和ID部分
            title_part = re.sub(r'-\d{4}-\d{2}-\d{2}', '', title_part)
            title_part = re.sub(r'-id[A-Z0-9]+$', '', title_part)
            
            # 将连字符替换为空格
            title = re.sub(r'-+', ' ', title_part)
            
            # 首字母大写
            title = ' '.join(word.capitalize() for word in title.split())
            
            # 如果标题太短，返回None
            if len(title) < 5:
                return None
            
            return title
            
        except Exception:
            return None
    
    def _clean_title(self, title: str) -> str:
        """清理标题"""
        # 移除多余的空白字符
        title = re.sub(r'\s+', ' ', title).strip()
        
        # 移除常见的后缀
        suffixes = ['| Reuters', '- Reuters', 'Reuters']
        for suffix in suffixes:
            if title.endswith(suffix):
                title = title[:-len(suffix)].strip()
        
        return title
    
    def _is_news_url(self, url: str) -> bool:
        """判断是否为新闻URL"""
        # 包含新闻相关路径
        news_patterns = [
            '/business/', '/markets/', '/world/', '/technology/',
            '/breakingviews/', '/legal/', '/sustainability/'
        ]
        
        # 排除的路径
        exclude_patterns = [
            '/video/', '/audio/', '/graphics/', '/pictures/',
            '/authors/', '/about/', '/contact/', '/privacy/',
            '/terms/', '/subscribe', '/newsletter', '/account',
            '/live-events/', '/podcasts/'
        ]
        
        # 检查是否包含新闻路径
        has_news_pattern = any(pattern in url for pattern in news_patterns)
        
        # 检查是否包含排除路径
        has_exclude_pattern = any(pattern in url for pattern in exclude_patterns)
        
        return has_news_pattern and not has_exclude_pattern


# 创建路透社新闻源实例
reuters_source = ReutersSource()


# 导出获取函数
async def get_reuters_news():
    """获取路透社新闻"""
    return await reuters_source.fetch_news()


# 统一的获取函数
async def reuters_getter():
    """路透社新闻获取器"""
    return await get_reuters_news()