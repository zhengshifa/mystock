"""Product Hunt新闻源"""

import re
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
from bs4 import BeautifulSoup

from sources.base import HTMLSource
from database.models import NewsItem, SourceResponse
from utils.logger import get_logger

logger = get_logger(__name__)


class ProductHuntSource(HTMLSource):
    """Product Hunt新闻源"""
    
    def __init__(self):
        super().__init__("producthunt", "Product Hunt", "https://www.producthunt.com")
        self.description = "Product Hunt热门产品"
        self.fetch_interval = 600  # 10分钟

    async def fetch_news(self):
        """获取Product Hunt热门产品"""
        try:
            # 添加必要的请求头，模拟真实浏览器
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            }
            
            try:
                # 使用 get_text 方法获取 HTML 字符串内容
                html_content = await self.fetcher.get_text(self.url)
                if not html_content:
                    return self.create_error_response("获取HTML内容失败")
                
                news_items = await self.parse_html_response(html_content)
                
                if news_items:
                    logger.success(f"成功获取 {len(news_items)} 个 Product Hunt 产品")
                    return self.create_success_response(news_items)
                else:
                    logger.info("Product Hunt 没有新数据")
                    return self.create_success_response([])
                    
            except Exception as fetch_error:
                logger.warning(f"Product Hunt HTML获取失败: {fetch_error}")
                return self.create_error_response(f"HTML获取失败: {fetch_error}")
            
        except Exception as e:
            logger.error(f"Product Hunt: 获取产品失败 - {e}")
            return self.create_error_response(str(e))
    
    async def parse_html_response(self, html_content: str) -> List[NewsItem]:
        """解析HTML响应"""
        soup = BeautifulSoup(html_content, 'html.parser')
        news_items = []
        
        # 查找产品条目 - 使用更通用的选择器
        # 首先尝试原始选择器
        items = soup.select('[data-test="homepage-section-0"] [data-test^="post-item"]')
        
        # 如果没找到，尝试其他可能的选择器
        if not items:
            items = soup.find_all(attrs={"data-test": lambda x: x and x.startswith("post-item")}) if soup.find_all(attrs={"data-test": lambda x: x and x.startswith("post-item")}) else []
        
        # 如果还是没找到，尝试查找包含产品信息的通用元素
        if not items:
            items = soup.find_all("article") or soup.find_all(class_=re.compile(r"post|product|item", re.I))
        
        for item in items:
            try:
                # 提取产品链接
                link_elem = item.find("a")
                if not link_elem:
                    continue
                
                relative_url = link_elem.get('href')
                if not relative_url:
                    continue
                
                # 构建完整URL
                if relative_url.startswith('/'):
                    url = f"https://www.producthunt.com{relative_url}"
                else:
                    url = relative_url
                
                # 提取产品名称
                title = ""
                # 尝试多种方式提取标题
                title_selectors = [
                    '[data-test^="post-name"]',
                    'h3', 'h2', 'h4',
                    '.post-name', '.product-name', '.title'
                ]
                
                for selector in title_selectors:
                    title_elem = item.select_one(selector)
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        # 移除序号
                        title = re.sub(r'^\d+\.\s*', '', title)
                        break
                
                if not title:
                    # 如果还是没找到标题，尝试从链接文本获取
                    title = link_elem.get_text(strip=True)
                    title = re.sub(r'^\d+\.\s*', '', title)
                
                if not title:
                    continue
                
                # 提取投票数
                vote_text = ""
                vote_selectors = [
                    '[data-test="vote-button"]',
                    '.vote-button', '.upvote', '.votes',
                    '[class*="vote"]', '[class*="upvote"]'
                ]
                
                for selector in vote_selectors:
                    vote_elem = item.select_one(selector)
                    if vote_elem:
                        vote_text = vote_elem.get_text(strip=True)
                        break
                
                # 提取产品描述
                description = ""
                desc_selectors = [
                    '.post-description', '.product-description',
                    'p', '.description', '.tagline'
                ]
                
                for selector in desc_selectors:
                    desc_elem = item.select_one(selector)
                    if desc_elem:
                        description = desc_elem.get_text(strip=True)[:200]
                        break
                
                # 提取产品ID
                product_id = item.get('data-test', '')
                if product_id.startswith('post-item-'):
                    product_id = product_id.replace('post-item-', '')
                else:
                    product_id = relative_url
                
                # 构建额外信息
                extra_info = f"△︎ {vote_text}" if vote_text else "新产品"
                
                news_item = NewsItem(
                    source_id=self.source_id,
                    title=title,
                    url=url,
                    description=description,
                    published_at=datetime.now(),
                    extra={
                        "votes": vote_text,
                        "info": extra_info,
                        "product_id": product_id
                    }
                )
                
                news_items.append(news_item)
                
            except Exception as e:
                logger.warning(f"解析Product Hunt产品条目失败: {e}")
                continue
        
        return news_items


# 创建Product Hunt新闻源实例
producthunt_source = ProductHuntSource()


# 导出获取函数
async def get_producthunt_news():
    """获取Product Hunt热门产品"""
    return await producthunt_source.fetch_news()


# 兼容性别名
producthunt_getter = get_producthunt_news