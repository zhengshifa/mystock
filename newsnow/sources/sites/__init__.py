"""新闻源站点实现"""

# 财经类新闻源
from .baidu import baidu_source, baidu_getter
from .weibo import weibo_source, weibo_getter
from .zhihu import zhihu_source, zhihu_getter

# 科技类新闻源
from .github import github_source, github_getter
from .kr36 import kr36_source, kr36_getter
from .producthunt import producthunt_source, get_producthunt_news
from .solidot import solidot_source, solidot_getter
from .v2ex import v2ex_source, v2ex_getter, get_v2ex_latest_news

# 所有新闻源
__all__ = [
    # 财经类
    'baidu_source', 'baidu_getter',
    'weibo_source', 'weibo_getter',
    'zhihu_source', 'zhihu_getter',
    
    # 科技类
    'github_source', 'github_getter',
    'kr36_source', 'kr36_getter',
    'producthunt_source', 'get_producthunt_news',
    'solidot_source', 'solidot_getter',
    'v2ex_source', 'v2ex_getter', 'get_v2ex_latest_news',
]