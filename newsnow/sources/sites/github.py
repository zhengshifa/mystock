"""GitHub 新闻源实现"""

import re
from datetime import datetime
from typing import List, Dict, Any
from bs4 import BeautifulSoup

from sources.base import BaseSource
from utils.fetch import get
from utils.logger import get_logger

logger = get_logger(__name__)


class GitHubSource(BaseSource):
    """GitHub 趋势项目新闻源"""
    
    def __init__(self):
        super().__init__("github", "GitHub Trending", "https://github.com")
        self.base_url = "https://github.com"
        self.interval = 1800  # 30分钟
    
    async def fetch_news(self):
        """获取 GitHub 趋势项目"""
        try:
            logger.info(f"开始获取 {self.name} 数据")
            
            url = "https://github.com/trending?spoken_language_code="
            response = await get(url)
            html = response.text
            
            if not html:
                raise Exception("获取HTML内容失败")
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # 查找趋势项目容器
            main_container = soup.find('main')
            if not main_container:
                raise Exception("未找到主容器")
            
            # 查找项目文章
            articles = main_container.select('.Box div[data-hpc] > article')
            
            if not articles:
                raise Exception("未找到趋势项目")
            
            news_list = []
            current_time = int(datetime.now().timestamp() * 1000)
            
            for article in articles:
                try:
                    # 查找项目标题和链接
                    title_link = article.select_one('h2 a')
                    if not title_link:
                        continue
                    
                    title = title_link.get_text(strip=True)
                    url_path = title_link.get('href')
                    
                    if not title or not url_path:
                        continue
                    
                    # 清理标题中的换行符
                    title = re.sub(r'\n+', ' ', title).strip()
                    
                    # 构建完整URL
                    full_url = self.base_url + url_path
                    
                    # 查找星标数
                    star_link = article.select_one('a[href$="/stargazers"]')
                    star_count = ""
                    if star_link:
                        star_text = star_link.get_text(strip=True)
                        star_count = re.sub(r'\s+', '', star_text)
                    
                    # 查找项目描述
                    desc_elem = article.select_one('p')
                    description = ""
                    if desc_elem:
                        description = desc_elem.get_text(strip=True)
                        description = re.sub(r'\n+', ' ', description).strip()
                    
                    news_item = {
                        'id': url_path,
                        'title': title,
                        'url': full_url,
                        'published_at': current_time,
                        'source_id': self.source_id,
                        'extra': {
                            'info': f"✰ {star_count}" if star_count else "✰ 0",
                            'hover': description,
                            'description': description
                        }
                    }
                    
                    news_list.append(news_item)
                    
                except Exception as e:
                    logger.warning(f"解析单个GitHub项目失败: {e}")
                    continue
            
            # 转换为NewsItem对象
            items = []
            for news_data in news_list:
                item = self.create_news_item(
                    title=news_data.get('title', ''),
                    url=news_data.get('url', ''),
                    description=news_data.get('extra', {}).get('description', ''),
                    published_at=datetime.fromtimestamp(news_data.get('published_at', 0) / 1000) if news_data.get('published_at') else None,
                    extra=news_data.get('extra', {})
                )
                items.append(item)
            
            # 限制条目数量
            max_items = self.config.get("MAX_NEWS_PER_SOURCE", 50)
            items = items[:max_items]
            
            logger.info(f"成功获取 {len(items)} 个 {self.name} 项目")
            return self.create_success_response(items)
            
        except Exception as e:
            error_msg = f"获取 {self.name} 数据失败: {e}"
            logger.error(error_msg)
            return self.create_error_response(error_msg)


class GitHubTrendingTodaySource(BaseSource):
    """GitHub 今日趋势项目新闻源"""
    
    def __init__(self):
        super().__init__("github-trending-today", "GitHub Trending Today", "https://github.com")
        self.base_url = "https://github.com"
        self.interval = 1800  # 30分钟
    
    async def fetch_news(self):
        """获取GitHub今日趋势项目"""
        return await GitHubSource().fetch_news()  # 复用GitHubSource的逻辑


# 创建实例并导出函数
github_source = GitHubSource()
github_trending_today_source = GitHubTrendingTodaySource()

async def github_getter():
    """获取GitHub趋势项目"""
    return await github_source.fetch_news()

async def get_github_trending_news():
    """获取GitHub趋势项目 (兼容旧接口)"""
    return await github_source.fetch_news()

async def github_trending_today_getter():
    """获取GitHub今日趋势项目"""
    return await github_trending_today_source.fetch_news()