"""雅虎财经新闻源实现"""

import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

from sources.base import HTMLSource
from database.models import NewsItem, SourceResponse
from utils.logger import get_logger
from utils.fetch import get

logger = get_logger(__name__)


class YahooFinanceSource(HTMLSource):
    """雅虎财经新闻源"""
    
    def __init__(self):
        """初始化雅虎财经新闻源"""
        source_id = "yahoo-finance"
        name = "Yahoo Finance"
        url = "https://finance.yahoo.com/news"
        super().__init__(source_id, name, url)
        self.base_url = "https://finance.yahoo.com"
        self.interval = 300  # 5分钟
    
    async def fetch_news(self):
        """获取雅虎财经新闻"""
        try:
            # 获取主页新闻
            news_items = await self._fetch_from_news_page()
            
            # 如果主页获取失败，尝试备用方法
            if not news_items:
                logger.info("雅虎财经: 新闻页面获取失败，尝试备用方法")
                news_items = await self._fetch_alternative()
            
            if news_items:
                logger.success(f"成功获取 {len(news_items)} 条 雅虎财经 新闻")
                return self.create_success_response(news_items)
            else:
                logger.info("雅虎财经 没有新数据")
                return self.create_success_response([])
            
        except Exception as e:
            logger.error(f"雅虎财经: 获取新闻失败 - {e}")
            return self.create_error_response(str(e))
    
    async def _fetch_from_news_page(self) -> List[NewsItem]:
        """从新闻页面获取新闻"""
        try:
            # 获取新闻页面HTML
            response = await get(self.url)
            if not response:
                return []
            
            html_content = response.text if hasattr(response, 'text') else ''
            if not html_content:
                return []
            
            return await self.parse_html_response(html_content)
            
        except Exception as e:
            logger.error(f"雅虎财经: 从新闻页面获取失败 - {e}")
            return []
    
    async def _fetch_alternative(self) -> List[NewsItem]:
        """备用获取方法 - 从特定股票页面获取新闻"""
        try:
            # 尝试从热门股票页面获取新闻
            stock_symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
            all_news = []
            
            for symbol in stock_symbols:
                try:
                    stock_url = f"{self.base_url}/quote/{symbol}"
                    response = await get(stock_url)
                    
                    if response and hasattr(response, 'text'):
                        news_items = await self._parse_stock_page_news(response.text, symbol)
                        all_news.extend(news_items)
                        
                        # 限制每个股票的新闻数量
                        if len(news_items) >= 3:
                            break
                            
                except Exception as e:
                    logger.warning(f"雅虎财经: 获取{symbol}新闻失败 - {e}")
                    continue
            
            # 去重并排序
            seen_urls = set()
            unique_news = []
            for item in all_news:
                if item.url not in seen_urls:
                    seen_urls.add(item.url)
                    unique_news.append(item)
            
            return unique_news[:15]  # 限制总数量
            
        except Exception as e:
            logger.error(f"雅虎财经: 备用方法获取失败 - {e}")
            return []
    
    async def parse_html_response(self, html: str) -> List[NewsItem]:
        """解析雅虎财经HTML响应"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            news_items = []
            
            # 查找新闻链接的多种选择器
            selectors = [
                'a[href*="/news/"]',
                'a[href*="/finance/news/"]',
                '.js-content-viewer a',
                r'.Ov\(h\) a',  # Yahoo特殊类名
                '.news-item a',
                '.story-item a'
            ]
            
            found_links = set()
            
            for selector in selectors:
                try:
                    links = soup.select(selector)
                    
                    for link in links:
                        try:
                            href = link.get('href')
                            if not href:
                                continue
                            
                            # 构建完整URL
                            if href.startswith('/'):
                                url = urljoin(self.base_url, href)
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
                                    "source": "news_page"
                                }
                            )
                            news_items.append(news_item)
                            
                        except Exception as e:
                            logger.warning(f"雅虎财经: 解析单条新闻失败 - {e}")
                            continue
                            
                except Exception as e:
                    logger.warning(f"雅虎财经: 选择器{selector}解析失败 - {e}")
                    continue
            
            logger.info(f"雅虎财经: 从新闻页面解析到 {len(news_items)} 条新闻")
            return news_items[:20]  # 限制数量
            
        except Exception as e:
            logger.error(f"雅虎财经: 解析HTML失败 - {e}")
            return []
    
    async def _parse_stock_page_news(self, html: str, symbol: str) -> List[NewsItem]:
        """解析股票页面的新闻"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            news_items = []
            
            # 在股票页面查找新闻相关的链接
            news_selectors = [
                'a[href*="/news/"]',
                '.news a',
                '.related-news a'
            ]
            
            for selector in news_selectors:
                links = soup.select(selector)
                
                for link in links:
                    try:
                        href = link.get('href')
                        if not href:
                            continue
                        
                        # 构建完整URL
                        if href.startswith('/'):
                            url = urljoin(self.base_url, href)
                        elif href.startswith('http'):
                            url = href
                        else:
                            continue
                        
                        # 过滤非新闻链接
                        if not self._is_news_url(url):
                            continue
                        
                        # 获取标题
                        title = link.get_text(strip=True)
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
                                "source": "stock_page",
                                "related_symbol": symbol
                            }
                        )
                        news_items.append(news_item)
                        
                    except Exception as e:
                        logger.warning(f"雅虎财经: 解析股票页面新闻失败 - {e}")
                        continue
            
            return news_items[:5]  # 每个股票页面限制5条
            
        except Exception as e:
            logger.error(f"雅虎财经: 解析股票页面失败 - {e}")
            return []
    
    def _extract_title_from_url(self, url: str) -> Optional[str]:
        """从URL提取标题"""
        try:
            parsed = urlparse(url)
            path_parts = parsed.path.strip('/').split('/')
            
            if len(path_parts) < 2:
                return None
            
            # 获取最后一部分作为标题基础
            title_part = path_parts[-1]
            
            # 移除文件扩展名
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
    
    def _clean_title(self, title: str) -> str:
        """清理标题"""
        # 移除多余的空白字符
        title = re.sub(r'\s+', ' ', title).strip()
        
        # 移除常见的后缀
        suffixes = [
            '| Yahoo Finance', '- Yahoo Finance', 'Yahoo Finance',
            '| Finance', '- Finance'
        ]
        for suffix in suffixes:
            if title.endswith(suffix):
                title = title[:-len(suffix)].strip()
        
        # 移除常见的前缀
        prefixes = ['Yahoo Finance: ', 'Finance: ']
        for prefix in prefixes:
            if title.startswith(prefix):
                title = title[len(prefix):].strip()
        
        return title
    
    def _is_news_url(self, url: str) -> bool:
        """判断是否为新闻URL"""
        # 包含新闻相关路径
        news_patterns = ['/news/', '/finance/news/']
        
        # 排除的路径
        exclude_patterns = [
            '/video/', '/live/', '/screener/', '/watchlists/',
            '/portfolio/', '/my/', '/account/', '/premium/',
            '/calendar/', '/sectors/', '/industries/',
            '/crypto/', '/options/', '/futures/'
        ]
        
        # 检查是否包含新闻路径
        has_news_pattern = any(pattern in url for pattern in news_patterns)
        
        # 检查是否包含排除路径
        has_exclude_pattern = any(pattern in url for pattern in exclude_patterns)
        
        # 检查域名是否为雅虎财经
        parsed = urlparse(url)
        is_yahoo_finance = 'finance.yahoo.com' in parsed.netloc
        
        return has_news_pattern and not has_exclude_pattern and is_yahoo_finance


# 创建雅虎财经新闻源实例
yahoo_finance_source = YahooFinanceSource()


# 导出获取函数
async def get_yahoo_finance_news():
    """获取雅虎财经新闻"""
    return await yahoo_finance_source.fetch_news()


# 统一的获取函数
async def yahoo_finance_getter():
    """雅虎财经新闻获取器"""
    return await get_yahoo_finance_news()