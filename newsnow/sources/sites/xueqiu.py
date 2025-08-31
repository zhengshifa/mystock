"""雪球新闻源实现"""

from datetime import datetime
from typing import List, Dict, Any

from sources.base import JSONSource
from database.models import NewsItem, SourceResponse
from utils.logger import get_logger

logger = get_logger(__name__)


class XueqiuSource(JSONSource):
    """雪球新闻源"""
    
    def __init__(self):
        """初始化雪球新闻源"""
        source_id = "xueqiu-hotstock"
        name = "雪球"
        url = "https://stock.xueqiu.com/v5/stock/hot_stock/list.json?size=30&_type=10&type=10"
        super().__init__(source_id, name, url)
        self.base_url = "https://xueqiu.com"
        self.interval = 120  # 2分钟
    
    async def fetch_news(self):
        """获取雪球热门股票数据"""
        try:
            # 首先访问雪球主页获取cookie
            cookie_response = await self.fetcher.get(
                "https://xueqiu.com/hq",
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            )
            
            # 提取cookie
            cookies = {}
            try:
                if hasattr(cookie_response, 'cookies') and cookie_response.cookies:
                    for cookie in cookie_response.cookies:
                        if hasattr(cookie, 'name') and hasattr(cookie, 'value'):
                            cookies[cookie.name] = cookie.value
                        elif isinstance(cookie, dict):
                            cookies[cookie.get('name', '')] = cookie.get('value', '')
            except Exception as e:
                logger.warning(f"提取cookie失败: {e}")
                cookies = {}
            
            # 构建cookie字符串
            cookie_str = "; ".join([f"{k}={v}" for k, v in cookies.items()]) if cookies else ""
            
            # 获取热门股票数据
            response = await self.fetch_json(
                self.url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Cookie": cookie_str,
                    "Referer": "https://xueqiu.com/"
                }
            )
            
            if response:
                items = await self.parse_json_response(response)
                if items:
                    logger.success(f"成功获取 {len(items)} 条 雪球 新闻")
                    return self.create_success_response(items)
                else:
                    logger.info("雪球 没有新数据")
                    return self.create_success_response([])
            else:
                logger.error(f"雪球: 获取数据失败")
                return self.create_error_response("获取数据失败")
                
        except Exception as e:
            logger.error(f"雪球: 获取新闻失败 - {e}")
            return self.create_error_response(str(e))
    
    async def parse_json_response(self, data: Dict[str, Any]) -> List[NewsItem]:
        """解析雪球JSON响应"""
        try:
            news_items = []
            
            items = data.get("data", {}).get("items", [])
            
            for item in items:
                # 过滤广告
                if item.get("ad", 0) == 1:
                    continue
                
                code = item.get("code", "")
                name = item.get("name", "")
                percent = item.get("percent", 0)
                exchange = item.get("exchange", "")
                
                if not code or not name:
                    continue
                
                # 构建标题和URL
                title = name
                url = f"https://xueqiu.com/s/{code}"
                
                # 构建额外信息
                info = f"{percent}% {exchange}" if percent and exchange else ""
                
                news_item = NewsItem(
                    source_id=self.source_id,
                    title=title,
                    url=url,
                    description=f"股票代码: {code}, 涨跌幅: {percent}%, 交易所: {exchange}",
                    published_at=datetime.now(),
                    extra={
                        "type": "hottest",
                        "stock_code": code,
                        "percent": percent,
                        "exchange": exchange,
                        "info": info
                    }
                )
                news_items.append(news_item)
            
            logger.info(f"雪球: 解析到 {len(news_items)} 只热门股票")
            return news_items
            
        except Exception as e:
            logger.error(f"雪球: 解析JSON数据失败 - {e}")
            return []


# 创建雪球新闻源实例
xueqiu_source = XueqiuSource()


# 导出获取函数
async def get_xueqiu_hotstock_news():
    """获取雪球热门股票"""
    return await xueqiu_source.fetch_news()


# 统一的获取函数
async def xueqiu_getter():
    """雪球新闻获取器"""
    return await get_xueqiu_hotstock_news()


async def get_xueqiu_news():
    """获取雪球新闻(兼容性函数)"""
    return await xueqiu_getter()


async def xueqiu_hotstock_getter():
    """雪球热门股票获取器"""
    return await get_xueqiu_hotstock_news()