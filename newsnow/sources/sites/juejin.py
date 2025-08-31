"""掘金新闻源"""

import asyncio
import json
from typing import List
from datetime import datetime

from sources.base import JSONSource
from database.models import NewsItem
from utils.logger import get_logger

logger = get_logger(__name__)


class JuejinSource(JSONSource):
    """掘金新闻源"""
    
    def __init__(self):
        super().__init__("juejin", "掘金", "https://api.juejin.cn/content_api/v1/content/article_rank?category_id=1&type=hot&spider=0")
        self.interval = 300  # 5分钟
        self.max_retries = 3  # 最大重试次数
    
    async def fetch_news(self):
        """获取掘金热门文章，添加重试和错误处理"""
        for attempt in range(self.max_retries):
            try:
                # 添加必要的请求头，模拟真实浏览器
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    "Accept": "application/json, text/plain, */*",
                    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Referer": "https://juejin.cn/",
                    "Origin": "https://juejin.cn",
                    "Connection": "keep-alive"
                }
                
                # 先尝试获取原始响应来调试
                raw_response = await self.fetcher.get(self.url, headers=headers)
                
                # 检查响应状态和内容
                if raw_response.status_code != 200:
                    logger.warning(f"掘金API返回状态码: {raw_response.status_code}")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    else:
                        return self.create_error_response(f"API返回状态码: {raw_response.status_code}")
                
                # 检查响应内容
                if not raw_response.content:
                    logger.warning("掘金API返回空内容")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    else:
                        return self.create_error_response("API返回空内容")
                
                # 尝试解析JSON
                try:
                    response = raw_response.json()
                except Exception as json_error:
                    logger.warning(f"掘金API JSON解析失败: {json_error}")
                    
                    # 检查响应头，看是否是压缩内容
                    content_encoding = raw_response.headers.get('content-encoding', '')
                    if content_encoding:
                        logger.warning(f"响应使用压缩编码: {content_encoding}")
                        
                        # 尝试处理压缩内容
                        try:
                            if content_encoding == 'br':
                                # Brotli压缩
                                import brotli
                                decompressed_content = brotli.decompress(raw_response.content)
                                response = json.loads(decompressed_content.decode('utf-8'))
                                logger.info("成功解压Brotli压缩内容")
                            elif content_encoding == 'gzip':
                                # Gzip压缩
                                import gzip
                                decompressed_content = gzip.decompress(raw_response.content)
                                response = json.loads(decompressed_content.decode('utf-8'))
                                logger.info("成功解压Gzip压缩内容")
                            elif content_encoding == 'deflate':
                                # Deflate压缩
                                import zlib
                                decompressed_content = zlib.decompress(raw_response.content)
                                response = json.loads(decompressed_content.decode('utf-8'))
                                logger.info("成功解压Deflate压缩内容")
                            else:
                                raise ValueError(f"不支持的压缩编码: {content_encoding}")
                                
                        except Exception as decompress_error:
                            logger.warning(f"解压失败: {decompress_error}")
                            # 记录响应编码信息用于调试
                            logger.warning(f"响应编码: {content_encoding}, 内容长度: {len(raw_response.content)} bytes")
                            
                            if attempt < self.max_retries - 1:
                                await asyncio.sleep(2 ** attempt)
                                continue
                            else:
                                return self.create_error_response(f"解压失败: {decompress_error}")
                    else:
                        # 没有压缩编码，记录响应信息
                        logger.warning(f"响应编码: {content_encoding}, 内容长度: {len(raw_response.content)} bytes")
                        
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(2 ** attempt)
                            continue
                        else:
                            return self.create_error_response(f"JSON解析失败: {json_error}")
                
                if response and isinstance(response, dict):
                    items = self.parse_json_response(response)
                    if items:
                        logger.success(f"成功获取 {len(items)} 条掘金热门文章")
                        return self.create_success_response(items)
                    else:
                        logger.info("掘金没有新数据")
                        return self.create_success_response([])
                else:
                    logger.warning(f"掘金API返回数据异常 (尝试 {attempt + 1}/{self.max_retries})")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(2 ** attempt)  # 指数退避
                        continue
                    else:
                        logger.error("掘金API重试次数已用完")
                        return self.create_error_response("API返回数据异常")
                        
            except Exception as e:
                logger.warning(f"掘金API请求失败 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # 指数退避
                    continue
                else:
                    logger.error(f"掘金API最终失败: {e}")
                    return self.create_error_response(str(e))
        
        return self.create_error_response("重试次数已用完")

    def parse_json_response(self, data: dict) -> List[NewsItem]:
        """解析掘金JSON响应"""
        items = []
        
        try:
            if not data or 'data' not in data:
                logger.warning("掘金API返回数据格式异常")
                return items
            
            articles = data.get('data', [])
            
            if not articles:
                logger.warning("掘金热门文章数据为空")
                return items
            
            for article in articles:
                try:
                    content = article.get('content', {})
                    if not content:
                        continue
                        
                    title = content.get('title', '').strip()
                    content_id = content.get('content_id', '').strip()
                    
                    if not title or not content_id:
                        continue
                    
                    # 构建文章URL
                    article_url = f"https://juejin.cn/post/{content_id}"
                    
                    # 创建新闻条目
                    news_item = self.create_news_item(
                        title=title,
                        url=article_url,
                        description="掘金热门文章",
                        extra={
                            'content_id': content_id
                        }
                    )
                    
                    items.append(news_item)
                    
                except Exception as e:
                    logger.warning(f"解析单个掘金文章失败: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"解析掘金JSON失败: {e}")
        
        return items


# 创建实例
juejin_source = JuejinSource()


async def juejin_getter():
    """掘金获取器"""
    return await juejin_source.fetch_news()