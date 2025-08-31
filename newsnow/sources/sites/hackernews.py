"""Hacker News 新闻源实现"""

from typing import List, Optional
from datetime import datetime
from bs4 import BeautifulSoup

from database.models import NewsItem, SourceResponse
from utils.fetch import get_text
from utils.logger import get_logger
from sources.base import HTMLSource

logger = get_logger(__name__)


class HackerNewsSource(HTMLSource):
    """Hacker News 新闻源"""
    
    def __init__(self):
        super().__init__(
            source_id="hackernews",
            name="Hacker News",
            url="https://news.ycombinator.com"
        )
    
    async def fetch_news(self) -> SourceResponse:
        """获取 Hacker News 新闻"""
        try:
            # 获取首页HTML
            html = await get_text(self.url)
            if not html:
                return SourceResponse(
                    source_id=self.source_id,
                    source_name=self.name,
                    items=[],
                    success=False,
                    error="无法获取页面内容"
                )
            
            # 解析HTML
            soup = BeautifulSoup(html, 'html.parser')
            items = []
            
            # 查找所有新闻条目
            story_rows = soup.select('.athing')
            
            for i, story in enumerate(story_rows[:30]):  # 只取前30条
                try:
                    # 获取标题和链接
                    title_elem = story.select_one('.titleline > a')
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    link = title_elem.get('href', '')
                    
                    # 处理相对链接
                    if link.startswith('item?id='):
                        link = f"https://news.ycombinator.com/{link}"
                    elif not link.startswith('http'):
                        link = f"https://news.ycombinator.com/{link}"
                    
                    # 获取故事ID
                    story_id = story.get('id', '')
                    
                    # 查找对应的元数据行（下一个兄弟元素）
                    meta_row = story.find_next_sibling('tr')
                    score = 0
                    comments_count = 0
                    author = ""
                    
                    if meta_row:
                        # 获取分数
                        score_elem = meta_row.select_one('.score')
                        if score_elem:
                            score_text = score_elem.get_text(strip=True)
                            try:
                                score = int(score_text.split()[0])
                            except (ValueError, IndexError):
                                score = 0
                        
                        # 获取作者
                        author_elem = meta_row.select_one('.hnuser')
                        if author_elem:
                            author = author_elem.get_text(strip=True)
                        
                        # 获取评论数
                        comments_elem = meta_row.select_one('a[href*="item?id="]')
                        if comments_elem:
                            comments_text = comments_elem.get_text(strip=True)
                            if 'comment' in comments_text:
                                try:
                                    comments_count = int(comments_text.split()[0])
                                except (ValueError, IndexError):
                                    comments_count = 0
                    
                    # 创建新闻条目
                    news_item = NewsItem(
                        title=title,
                        url=link,
                        source_id=self.source_id,
                        author=author,
                        published_at=datetime.now(),
                        extra={
                            "score": score,
                            "comments": comments_count,
                            "author": author,
                            "story_id": story_id,
                            "rank": i + 1
                        }
                    )
                    
                    items.append(news_item)
                    
                except Exception as e:
                    logger.warning(f"解析 Hacker News 条目失败: {e}")
                    continue
            
            logger.info(f"成功获取 {len(items)} 条 Hacker News 新闻")
            
            return SourceResponse(
                status="success",
                source_id=self.source_id,
                items=items
            )
            
        except Exception as e:
            logger.error(f"获取 Hacker News 新闻失败: {e}")
            return SourceResponse(
                status="error",
                source_id=self.source_id,
                items=[],
                error_message=str(e)
            )
    
    def parse_item(self, element) -> Optional[NewsItem]:
        """解析单个新闻条目（基类方法实现）"""
        # 这个方法在 fetch_news 中已经实现了更复杂的逻辑
        # 这里提供一个简化版本以满足基类要求
        try:
            title_elem = element.select_one('.titleline > a')
            if not title_elem:
                return None
            
            title = title_elem.get_text(strip=True)
            link = title_elem.get('href', '')
            
            if link.startswith('item?id='):
                link = f"https://news.ycombinator.com/{link}"
            elif not link.startswith('http'):
                link = f"https://news.ycombinator.com/{link}"
            
            story_id = element.get('id', '')
            
            return NewsItem(
                title=title,
                url=link,
                source_id=self.source_id,
                published_at=datetime.now(),
                extra={"story_id": story_id}
            )
            
        except Exception as e:
            logger.warning(f"解析 Hacker News 条目失败: {e}")
            return None