"""新闻源模块"""

from typing import Dict, List, Optional, Callable, Awaitable
from loguru import logger

from database.models import SourceResponse
from .base import define_source, define_rss_source, define_rsshub_source
# 新闻源获取器注册表
_source_getters: Dict[str, Callable[[], Awaitable[SourceResponse]]] = {}


def register_source(source_id: str, getter: Callable[[], Awaitable[SourceResponse]]) -> None:
    """注册新闻源获取器"""
    _source_getters[source_id] = getter
    logger.debug(f"注册新闻源: {source_id}")


def get_source_getter(source_id: str) -> Optional[Callable[[], Awaitable[SourceResponse]]]:
    """获取新闻源获取器"""
    return _source_getters.get(source_id)


def get_available_sources() -> List[str]:
    """获取所有可用的新闻源ID"""
    return list(_source_getters.keys())


def get_source_info(source_id: str) -> Optional[Dict[str, str]]:
    """获取新闻源信息"""
    getter = _source_getters.get(source_id)
    if getter:
        return {
            "id": source_id,
            "name": getattr(getter, "name", source_id),
            "url": getattr(getter, "url", ""),
            "type": getattr(getter, "source_type", "unknown")
        }
    return None


def get_all_sources_info() -> List[Dict[str, str]]:
    """获取所有新闻源信息"""
    sources_info = []
    for source_id in _source_getters.keys():
        info = get_source_info(source_id)
        if info:
            sources_info.append(info)
    return sources_info


# 注册一些示例新闻源
def _register_default_sources():
    """注册默认新闻源"""
    
    # Hacker News
    @define_source("hackernews", "Hacker News", "https://news.ycombinator.com")
    async def hackernews_getter() -> SourceResponse:
        from .sites.hackernews import HackerNewsSource
        source = HackerNewsSource()
        return await source.fetch_news()
    
    register_source("hackernews", hackernews_getter)
    
    # 36氪 RSS
    kr36_rss = define_rss_source("36kr", "36氪", "https://36kr.com/feed")
    register_source("36kr", kr36_rss)
    
    # 知乎热榜 RSSHub
    zhihu_hot = define_rsshub_source("zhihu_hot", "知乎热榜", "/zhihu/hotlist")
    register_source("zhihu_hot", zhihu_hot)
    
    # 微博热搜 RSSHub
    weibo_hot = define_rsshub_source("weibo_hot", "微博热搜", "/weibo/search/hot")
    register_source("weibo_hot", weibo_hot)
    
    # GitHub Trending RSSHub
    github_trending = define_rsshub_source("github_trending", "GitHub Trending", "/github/trending/daily")
    register_source("github_trending", github_trending)
    
    # V2EX 最新主题 RSSHub
    v2ex_latest = define_rsshub_source("v2ex_latest", "V2EX 最新主题", "/v2ex/topics/latest")
    register_source("v2ex_latest", v2ex_latest)
    
    # 少数派 RSS
    sspai_rss = define_rss_source("sspai", "少数派", "https://sspai.com/feed")
    register_source("sspai", sspai_rss)
    
    # IT之家 RSS
    ithome_rss = define_rss_source("ithome", "IT之家", "https://www.ithome.com/rss/")
    register_source("ithome", ithome_rss)
    
    # 百度热搜 RSSHub
    baidu_hot = define_rsshub_source("baidu_hot", "百度热搜", "/baidu/trending")
    register_source("baidu_hot", baidu_hot)
    
    # 虎扑步行街 RSSHub
    hupu_bxj = define_rsshub_source("hupu_bxj", "虎扑步行街", "/hupu/bxj")
    register_source("hupu_bxj", hupu_bxj)
    
    # 掘金热门 RSSHub
    juejin_hot = define_rsshub_source("juejin_hot", "掘金热门", "/juejin/trending")
    register_source("juejin_hot", juejin_hot)
    
    # 知乎热榜
    @define_source("zhihu", "知乎热榜", "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total")
    async def zhihu_getter() -> SourceResponse:
        from .sites.zhihu import zhihu_getter as zhihu_func
        return await zhihu_func()
    
    register_source("zhihu", zhihu_getter)
    
    # 微博热搜
    @define_source("weibo", "微博热搜", "https://weibo.com/ajax/side/hotSearch")
    async def weibo_getter() -> SourceResponse:
        from .sites.weibo import weibo_getter as weibo_func
        return await weibo_func()
    
    register_source("weibo", weibo_getter)
    
    # 36氪快讯
    @define_source("kr36", "36氪快讯", "https://36kr.com/newsflashes")
    async def kr36_getter() -> SourceResponse:
        from .sites.kr36 import kr36_getter as kr36_func
        return await kr36_func()
    
    register_source("kr36", kr36_getter)
    
    # 百度热搜
    @define_source("baidu", "百度热搜", "https://top.baidu.com/board?tab=realtime")
    async def baidu_getter() -> SourceResponse:
        from .sites.baidu import baidu_getter as baidu_func
        return await baidu_func()
    
    register_source("baidu", baidu_getter)
    
    # IT之家
    @define_source("ithome", "IT之家", "https://www.ithome.com/")
    async def ithome_getter() -> SourceResponse:
        from .sites.ithome import ithome_getter as ithome_func
        return await ithome_func()
    
    register_source("ithome", ithome_getter)
    
    # 虎扑热榜
    @define_source("hupu", "虎扑热榜", "https://bbs.hupu.com/all-gambia")
    async def hupu_getter() -> SourceResponse:
        from .sites.hupu import hupu_getter as hupu_func
        return await hupu_func()
    
    register_source("hupu", hupu_getter)
    
    # 掘金热门
    @define_source("juejin", "掘金热门", "https://api.juejin.cn/content_api/v1/content/article_rank?category_id=1&type=hot&spider=0")
    async def juejin_getter() -> SourceResponse:
        from .sites.juejin import juejin_getter as juejin_func
        return await juejin_func()
    
    register_source("juejin", juejin_getter)
    
    # V2EX
    @define_source("v2ex", "V2EX", "https://www.v2ex.com/api/topics/latest.json")
    async def v2ex_getter() -> SourceResponse:
        from .sites.v2ex import v2ex_getter as v2ex_func
        return await v2ex_func()
    
    register_source("v2ex", v2ex_getter)
    
    # Solidot
    @define_source("solidot", "Solidot", "https://www.solidot.org/")
    async def solidot_getter() -> SourceResponse:
        from .sites.solidot import solidot_getter as solidot_func
        return await solidot_func()
    
    register_source("solidot", solidot_getter)
    
    # Product Hunt
    @define_source("producthunt", "Product Hunt", "https://www.producthunt.com/")
    async def producthunt_getter() -> SourceResponse:
        from .sites.producthunt import producthunt_getter as producthunt_func
        return await producthunt_func()
    
    register_source("producthunt", producthunt_getter)
    
    # GitHub Trending
    @define_source("github", "GitHub Trending", "https://github.com/trending")
    async def github_getter() -> SourceResponse:
        from .sites.github import github_getter as github_func
        return await github_func()
    
    register_source("github", github_getter)
    
    # 财联社
    @define_source("cls", "财联社", "https://www.cls.cn/")
    async def cls_getter() -> SourceResponse:
        from .sites.cls import get_cls_news
        return await get_cls_news()
    
    register_source("cls", cls_getter)
    
    # 华尔街见闻
    @define_source("wallstreetcn", "华尔街见闻", "https://wallstreetcn.com/")
    async def wallstreetcn_getter() -> SourceResponse:
        from .sites.wallstreetcn import get_wallstreetcn_news
        return await get_wallstreetcn_news()
    
    register_source("wallstreetcn", wallstreetcn_getter)
    
    # 雪球
    @define_source("xueqiu", "雪球", "https://xueqiu.com/")
    async def xueqiu_getter() -> SourceResponse:
        from .sites.xueqiu import get_xueqiu_news
        return await get_xueqiu_news()
    
    register_source("xueqiu", xueqiu_getter)
    
    # 格隆汇
    @define_source("gelonghui", "格隆汇", "https://www.gelonghui.com/")
    async def gelonghui_getter() -> SourceResponse:
        from .sites.gelonghui import get_gelonghui_news
        return await get_gelonghui_news()
    
    register_source("gelonghui", gelonghui_getter)
    
    # 快讯通财经
    @define_source("fastbull", "快讯通财经", "https://www.fastbull.cn/")
    async def fastbull_getter() -> SourceResponse:
        from .sites.fastbull import get_fastbull_news
        return await get_fastbull_news()
    
    register_source("fastbull", fastbull_getter)
    
    # 路透社
    @define_source("reuters", "路透社", "https://www.reuters.com/")
    async def reuters_getter() -> SourceResponse:
        from .sites.reuters import get_reuters_news
        return await get_reuters_news()
    
    register_source("reuters", reuters_getter)
    
    # 彭博社
    @define_source("bloomberg", "彭博社", "https://www.bloomberg.com/")
    async def bloomberg_getter() -> SourceResponse:
        from .sites.bloomberg import get_bloomberg_news
        return await get_bloomberg_news()
    
    register_source("bloomberg", bloomberg_getter)
    
    # 雅虎财经
    @define_source("yahoo_finance", "雅虎财经", "https://finance.yahoo.com/")
    async def yahoo_finance_getter() -> SourceResponse:
        from .sites.yahoo_finance import get_yahoo_finance_news
        return await get_yahoo_finance_news()
    
    register_source("yahoo_finance", yahoo_finance_getter)
    
    # 中国政府网政策
    @define_source("gov_policy", "中国政府网政策", "https://rsshub.app/gov/zhengce/zuixin")
    async def gov_policy_getter() -> SourceResponse:
        from .sites.gov_policy import get_gov_policy_news
        return await get_gov_policy_news()
    
    register_source("gov_policy", gov_policy_getter)
    
    logger.info(f"已注册 {len(_source_getters)} 个默认新闻源")


# 自动注册默认新闻源
_register_default_sources()


# 导出主要接口
__all__ = [
    "register_source",
    "get_source_getter", 
    "get_available_sources",
    "get_source_info",
    "get_all_sources_info",
    "define_source",
    "define_rss_source",
    "define_rsshub_source"
]