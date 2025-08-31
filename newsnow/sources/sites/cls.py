"""财联社新闻源实现"""

import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode

from sources.base import JSONSource
from database.models import NewsItem, SourceResponse
from utils.logger import get_logger

logger = get_logger(__name__)


class ClsSource(JSONSource):
    """财联社新闻源"""
    
    def __init__(self, source_type: str = "telegraph"):
        """初始化财联社新闻源
        
        Args:
            source_type: 新闻类型 (telegraph/depth/hot)
        """
        self.source_type = source_type
        source_id = f"cls-{source_type}"
        name = "财联社"
        url = "https://www.cls.cn/nodeapi/updateTelegraphList"  # 默认URL
        super().__init__(source_id, name, url)
        self.base_url = "https://www.cls.cn"
        self.interval = 300  # 5分钟
        
        # 根据类型设置不同的API URL
        if source_type == "telegraph":
            self.url = "https://www.cls.cn/nodeapi/updateTelegraphList"
        elif source_type == "depth":
            self.url = "https://www.cls.cn/v3/depth/home/assembled/1000"
        elif source_type == "hot":
            self.url = "https://www.cls.cn/v2/article/hot/list"
        else:
            raise ValueError(f"不支持的新闻类型: {source_type}")
    
    def _get_search_params(self, more_params: Optional[Dict] = None) -> Dict[str, str]:
        """生成财联社API所需的参数"""
        params = {
            "appName": "CailianpressWeb",
            "os": "web",
            "sv": "7.7.5"
        }
        
        if more_params:
            params.update(more_params)
        
        # 生成签名
        param_str = urlencode(sorted(params.items()))
        # 简化的签名生成，实际可能需要更复杂的加密
        sign = hashlib.md5(param_str.encode()).hexdigest()
        params["sign"] = sign
        
        return params
    
    async def fetch_news(self):
        """获取财联社新闻数据"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                # 添加必要的查询参数
                params = self._get_search_params()
                
                # 使用父类的方法获取数据，但传入查询参数
                response = await self.fetch_json(
                    self.url,
                    params=params,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "Referer": "https://www.cls.cn/",
                        "Accept": "application/json, text/plain, */*",
                        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
                    }
                )
                
                if response and isinstance(response, dict) and response.get("success") and response.get("data"):
                    items = await self.parse_json_response(response.get("data", {}))
                    if items:
                        logger.success(f"成功获取 {len(items)} 条 财联社({self.source_type}) 新闻")
                        return self.create_success_response(items)
                    else:
                        logger.info(f"财联社({self.source_type}) 没有新数据")
                        return self.create_success_response([])
                else:
                    logger.warning(f"财联社({self.source_type}): 获取数据失败 (尝试 {attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:
                        import asyncio
                        await asyncio.sleep(2 ** attempt)  # 指数退避
                        continue
                    else:
                        logger.error(f"财联社({self.source_type}): 重试次数已用完")
                        return self.create_error_response("获取数据失败")
                        
            except Exception as e:
                logger.warning(f"财联社({self.source_type}): 获取新闻失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    import asyncio
                    await asyncio.sleep(2 ** attempt)  # 指数退避
                    continue
                else:
                    logger.error(f"财联社({self.source_type}): 最终失败: {e}")
                    return self.create_error_response(str(e))
        
        return self.create_error_response("重试次数已用完")
    
    async def parse_json_response(self, data: Dict[str, Any]) -> List[NewsItem]:
        """解析财联社JSON响应"""
        try:
            news_items = []
            
            if self.source_type == "telegraph":
                # 电报数据
                items = data.get("data", {}).get("roll_data", [])
                for item in items:
                    # 过滤广告
                    if item.get("is_ad", 0) == 1:
                        continue
                    
                    news_item = NewsItem(
                        source_id=self.source_id,
                        title=item.get("title") or item.get("brief", ""),
                        url=f"https://www.cls.cn/detail/{item.get('id')}",
                        description=item.get("brief", ""),
                        published_at=datetime.fromtimestamp(item.get("ctime", 0)),
                        extra={
                            "type": "realtime",
                            "source_type": self.source_type,
                            "mobile_url": item.get("shareurl", "")
                        }
                    )
                    news_items.append(news_item)
            
            elif self.source_type == "depth":
                # 深度数据
                depth_list = data.get("data", {}).get("depth_list", [])
                # 按时间排序
                depth_list.sort(key=lambda x: x.get("ctime", 0), reverse=True)
                
                for item in depth_list:
                    news_item = NewsItem(
                        source_id=self.source_id,
                        title=item.get("title") or item.get("brief", ""),
                        url=f"https://www.cls.cn/detail/{item.get('id')}",
                        description=item.get("brief", ""),
                        published_at=datetime.fromtimestamp(item.get("ctime", 0)),
                        extra={
                            "type": "depth",
                            "source_type": self.source_type,
                            "mobile_url": item.get("shareurl", "")
                        }
                    )
                    news_items.append(news_item)
            
            elif self.source_type == "hot":
                # 热门数据
                items = data.get("data", [])
                for item in items:
                    news_item = NewsItem(
                        source_id=self.source_id,
                        title=item.get("title") or item.get("brief", ""),
                        url=f"https://www.cls.cn/detail/{item.get('id')}",
                        description=item.get("brief", ""),
                        published_at=datetime.now(),  # 热门新闻使用当前时间
                        extra={
                            "type": "hottest",
                            "source_type": self.source_type,
                            "mobile_url": item.get("shareurl", "")
                        }
                    )
                    news_items.append(news_item)
            
            logger.info(f"财联社({self.source_type}): 解析到 {len(news_items)} 条新闻")
            return news_items
            
        except Exception as e:
            logger.error(f"财联社({self.source_type}): 解析JSON数据失败 - {e}")
            return []


# 创建不同类型的财联社新闻源实例
cls_telegraph_source = ClsSource("telegraph")
cls_depth_source = ClsSource("depth")
cls_hot_source = ClsSource("hot")


# 导出获取函数
async def get_cls_telegraph_news():
    """获取财联社电报"""
    return await cls_telegraph_source.fetch_news()


async def get_cls_depth_news():
    """获取财联社深度"""
    return await cls_depth_source.fetch_news()


async def get_cls_hot_news():
    """获取财联社热门"""
    return await cls_hot_source.fetch_news()


# 统一的获取函数
async def cls_getter():
    """财联社新闻获取器(默认电报)"""
    return await get_cls_telegraph_news()


async def get_cls_news():
    """获取财联社新闻(兼容性函数)"""
    return await cls_getter()


async def cls_telegraph_getter():
    """财联社电报获取器"""
    return await get_cls_telegraph_news()


async def cls_depth_getter():
    """财联社深度获取器"""
    return await get_cls_depth_news()


async def cls_hot_getter():
    """财联社热门获取器"""
    return await get_cls_hot_news()