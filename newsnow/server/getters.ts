import type { SourceID } from "../shared/types"
import type { SourceGetter } from "./types"

// 手动导入所有新闻源
import _36kr from "./sources/_36kr"
import baidu from "./sources/baidu"
import bilibili from "./sources/bilibili"
import cankaoxiaoxi from "./sources/cankaoxiaoxi"
import chongbuluo from "./sources/chongbuluo"
import cls from "./sources/cls"
import coolapk from "./sources/coolapk"
import douyin from "./sources/douyin"
import fastbull from "./sources/fastbull"
import gelonghui from "./sources/gelonghui"
import ghxi from "./sources/ghxi"
import github from "./sources/github"
import hackernews from "./sources/hackernews"
import hupu from "./sources/hupu"
import ifeng from "./sources/ifeng"
import ithome from "./sources/ithome"
import jin10 from "./sources/jin10"
import juejin from "./sources/juejin"
import kaopu from "./sources/kaopu"
import kuaishou from "./sources/kuaishou"
import linuxdo from "./sources/linuxdo"
import mktnews from "./sources/mktnews"
import nowcoder from "./sources/nowcoder"
import pcbeta from "./sources/pcbeta"
import producthunt from "./sources/producthunt"
import smzdm from "./sources/smzdm"
import solidot from "./sources/solidot"
import sputniknewscn from "./sources/sputniknewscn"
import sspai from "./sources/sspai"
import thepaper from "./sources/thepaper"
import tieba from "./sources/tieba"
import toutiao from "./sources/toutiao"
import v2ex from "./sources/v2ex"
import wallstreetcn from "./sources/wallstreetcn"
import weibo from "./sources/weibo"
import xueqiu from "./sources/xueqiu"
import zaobao from "./sources/zaobao"
import zhihu from "./sources/zhihu"
import bloomberg from "./sources/bloomberg"
import reuters from "./sources/reuters"
import yahooFinance from "./sources/yahoo-finance"

// 新闻源映射
const sourceModules = {
  "36kr": _36kr,
  baidu,
  bilibili,
  cankaoxiaoxi,
  chongbuluo,
  cls,
  coolapk,
  douyin,
  fastbull,
  gelonghui,
  ghxi,
  github,
  hackernews,
  hupu,
  ifeng,
  ithome,
  jin10,
  juejin,
  kaopu,
  kuaishou,
  linuxdo,
  mktnews,
  nowcoder,
  pcbeta,
  producthunt,
  smzdm,
  solidot,
  sputniknewscn,
  sspai,
  thepaper,
  tieba,
  toutiao,
  v2ex,
  wallstreetcn,
  weibo,
  xueqiu,
  zaobao,
  zhihu,
  bloomberg,
  reuters,
  "yahoo-finance": yahooFinance
}

// 创建getters对象
export const getters = (function () {
  const getters = {} as Record<SourceID, SourceGetter>
  
  Object.entries(sourceModules).forEach(([id, module]) => {
    if (module && typeof module === 'function') {
      // 直接是函数的情况
      getters[id as SourceID] = module as SourceGetter
    } else if (module && typeof module === 'object') {
      // 是对象且有 default 导出的情况
      if (module.default && typeof module.default === 'function') {
        getters[id as SourceID] = module.default
      }
    }
  })
  
  return getters
})()
