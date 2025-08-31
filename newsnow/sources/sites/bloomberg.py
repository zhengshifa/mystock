"""彭博社新闻源实现"""

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


class BloombergSource(HTMLSource):
    """彭博社新闻源"""
    
    def __init__(self):
        """初始化彭博社新闻源"""
        source_id = "bloomberg"
        name = "Bloomberg"
        url = "https://www.bloomberg.com"
        super().__init__(source_id, name, url)
        self.base_url = "https://www.bloomberg.com"
        self.sitemap_url = "https://www.bloomberg.com/sitemap_news.xml"
        self.interval = 300  # 5分钟
    
    async def fetch_news(self):
        """获取彭博社新闻"""
        try:
            # 首先尝试从sitemap获取新闻
            news_items = await self._fetch_from_sitemap()
            
            # 如果sitemap失败或没有数据，尝试从主页获取
            if not news_items:
                logger.info("彭博社: sitemap获取失败，尝试从主页获取")
                news_items = await self._fetch_from_homepage()
            
            if news_items:
                logger.success(f"成功获取 {len(news_items)} 条 彭博社 新闻")
                return self.create_success_response(news_items)
            else:
                logger.info("彭博社 没有新数据")
                return self.create_success_response([])
            
        except Exception as e:
            logger.error(f"彭博社: 获取新闻失败 - {e}")
            return self.create_error_response(str(e))
    
    async def _fetch_from_sitemap(self) -> List[NewsItem]:
        """从sitemap获取新闻"""
        try:
            # 获取sitemap XML
            response = await get(self.sitemap_url)
            if not response:
                return []
            
            xml_content = response.text if hasattr(response, 'text') else ''
            if not xml_content:
                return []
            
            # 解析XML
            root = ET.fromstring(xml_content)
            news_items = []
            
            # 查找所有url元素
            for url_elem in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
                try:
                    loc_elem = url_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                    lastmod_elem = url_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod')
                    
                    if loc_elem is None:
                        continue
                    
                    url = loc_elem.text
                    if not url or '/news/' not in url:
                        continue
                    
                    # 解析发布时间
                    published_at = datetime.now()
                    if lastmod_elem is not None and lastmod_elem.text:
                        try:
                            # 处理ISO格式时间
                            time_str = lastmod_elem.text.replace('Z', '+00:00')
                            published_at = datetime.fromisoformat(time_str.replace('+00:00', ''))
                        except ValueError:
                            published_at = datetime.now()
                    
                    # 从URL提取标题
                    title = self._extract_title_from_url(url)
                    if not title:
                        continue
                    
                    # 创建新闻项
                    news_item = NewsItem(
                        source_id=self.source_id,
                        title=title,
                        url=url,
                        description="",
                        published_at=published_at,
                        extra={
                            "type": "news",
                            "source": "sitemap"
                        }
                    )
                    news_items.append(news_item)
                    
                except Exception as e:
                    logger.warning(f"彭博社: 解析sitemap条目失败 - {e}")
                    continue
            
            # 按时间排序，取最新的20条
            news_items.sort(key=lambda x: x.published_at, reverse=True)
            return news_items[:20]
            
        except Exception as e:
            logger.error(f"彭博社: 从sitemap获取新闻失败 - {e}")
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
            logger.error(f"彭博社: 从主页获取新闻失败 - {e}")
            return []
    
    async def parse_html_response(self, html: str) -> List[NewsItem]:
        """解析彭博社HTML响应"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            news_items = []
            
            # 查找新闻链接
            # 彭博社使用多种选择器来标识新闻链接
            selectors = [
                'a[href*="/news/"]',
                'a[href*="/articles/"]',
                '.story-list-story__headline-link',
                '.single-story-module__headline-link'
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
                        logger.warning(f"彭博社: 解析单条新闻失败 - {e}")
                        continue
            
            logger.info(f"彭博社: 从主页解析到 {len(news_items)} 条新闻")
            return news_items[:20]  # 限制数量
            
        except Exception as e:
            logger.error(f"彭博社: 解析HTML失败 - {e}")
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
            
            # 移除常见的后缀
            title_part = re.sub(r'\.(html|htm)$', '', title_part)
            
            # 将连字符和下划线替换为空格
            title = re.sub(r'[-_]+', ' ', title_part)
            
            # 首字母大写
            title = ' '.join(word.capitalize() for word in title.split())
            
            # 如果标题太短，返回None
            if len(title) < 5:
                return None
            
            return title
            
        except Exception:
            return None
    
    def _is_news_url(self, url: str) -> bool:
        """判断是否为新闻URL"""
        # 包含新闻相关路径
        news_patterns = ['/news/', '/articles/', '/story/']
        
        # 排除的路径
        exclude_patterns = [
            '/live/', '/video/', '/audio/', '/podcast/',
            '/opinion/', '/graphics/', '/photo/',
            '/subscribe', '/newsletter', '/account'
        ]
        
        # 检查是否包含新闻路径
        has_news_pattern = any(pattern in url for pattern in news_patterns)
        
        # 检查是否包含排除路径
        has_exclude_pattern = any(pattern in url for pattern in exclude_patterns)
        
        return has_news_pattern and not has_exclude_pattern


# 创建彭博社新闻源实例
bloomberg_source = BloombergSource()


# 导出获取函数
async def get_bloomberg_news():
    """获取彭博社新闻"""
    return await bloomberg_source.fetch_news()


# 统一的获取函数
async def bloomberg_getter():
    """彭博社新闻获取器"""
    return await get_bloomberg_news()