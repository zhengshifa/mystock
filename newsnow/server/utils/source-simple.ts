/**
 * 简化的新闻源工具函数
 */

import type { NewsItem, SourceGetter, SourceOption } from "../types"
import { fetchWithProxy } from "./fetch-simple"

/**
 * 定义新闻源
 */
export function defineSource(source: SourceGetter): SourceGetter {
  return source
}

/**
 * 定义RSS源
 */
export function defineRSSSource(url: string, option?: SourceOption): SourceGetter {
  return async (limit?: number) => {
    try {
      const response = await fetchWithProxy(url)
      const text = await response.text()
      
      // 简单的RSS解析（这里可以扩展为更完整的解析）
      const items: NewsItem[] = []
      const titleMatches = text.match(/<title[^>]*>([^<]+)<\/title>/g)
      const linkMatches = text.match(/<link[^>]*>([^<]+)<\/link>/g)
      
      if (titleMatches && linkMatches) {
        const maxItems = limit || 20
        const count = Math.min(titleMatches.length, linkMatches.length, maxItems)
        
        for (let i = 0; i < count; i++) {
          const title = titleMatches[i].replace(/<[^>]*>/g, '').trim()
          const link = linkMatches[i].replace(/<[^>]*>/g, '').trim()
          
          if (title && link && link.startsWith('http')) {
            items.push({
              title,
              link,
              id: link,
              url: link
            })
          }
        }
      }
      
      return items
    } catch (error) {
      console.error(`RSS源获取失败: ${url}`, error)
      return []
    }
  }
}

/**
 * 代理源（简化版本）
 */
export function proxySource(proxyUrl: string, source: SourceGetter): SourceGetter {
  // 简化版本，直接返回原源
  return source
}

/**
 * 基础新闻源模板
 */
export function createBasicSource(
  url: string,
  titleSelector: string,
  linkSelector: string,
  descriptionSelector?: string
): SourceGetter {
  return async (limit?: number) => {
    try {
      const html = await fetchWithProxy(url).then(res => res.text())
      const items: NewsItem[] = []
      
      // 简单的HTML解析（这里可以扩展为使用cheerio等库）
      const titleRegex = new RegExp(`<[^>]*class="[^"]*${titleSelector}[^"]*"[^>]*>([^<]+)</[^>]*>`, 'g')
      const linkRegex = new RegExp(`href="([^"]+)"`, 'g')
      
      const titles = [...html.matchAll(titleRegex)].map(match => match[1])
      const links = [...html.matchAll(linkRegex)].filter(link => link[1].startsWith('http'))
      
      const maxItems = limit || 20
      const count = Math.min(titles.length, links.length, maxItems)
      
      for (let i = 0; i < count; i++) {
        if (titles[i] && links[i]) {
          items.push({
            title: titles[i].trim(),
            link: links[i][1],
            id: links[i][1],
            url: links[i][1]
          })
        }
      }
      
      return items
    } catch (error) {
      console.error(`基础源获取失败: ${url}`, error)
      return []
    }
  }
}


