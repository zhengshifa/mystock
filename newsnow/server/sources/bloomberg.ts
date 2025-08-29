import { defineSource } from "../utils/source"
import { NewsItem } from "../types"
import { myFetch } from "../utils/fetch"
import * as cheerio from "cheerio"

export default defineSource(async () => {
  const url = "https://www.bloomberg.com/feeds/sitemap_news.xml"
  
  try {
    const response = await myFetch(url, {
      headers: {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/xml, text/xml, */*",
      },
    })
    
    const text = await response.text()
    const $ = cheerio.load(text, { xmlMode: true })
    
    const items: NewsItem[] = []
    
    $("url").each((_, element) => {
      const $el = $(element)
      const loc = $el.find("loc").text()
      const lastmod = $el.find("lastmod").text()
      const title = $el.find("news\\:title").text() || $el.find("title").text()
      
      if (loc && title && loc.includes("/news/articles/")) {
        items.push({
          id: loc.split("/").pop() || loc,
          title: title.trim(),
          link: loc,
          publishedAt: lastmod ? new Date(lastmod) : new Date(),
          extra: {
            source: "Bloomberg"
          }
        })
      }
    })
    
    return items.slice(0, 20) // 限制返回20条最新新闻
    
  } catch (error) {
    console.error("Bloomberg fetch error:", error)
    
    // 备用方案：尝试从Bloomberg主页获取新闻
    try {
      const fallbackUrl = "https://www.bloomberg.com/"
      const response = await myFetch(fallbackUrl, {
        headers: {
          "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        },
      })
      
      const html = await response.text()
      const $ = cheerio.load(html)
      
      const items: NewsItem[] = []
      
      // 尝试从主页提取新闻链接
      $("a[href*='/news/articles/']").each((index, element) => {
        if (index >= 20) return false
        
        const $el = $(element)
        const href = $el.attr("href")
        const title = $el.text().trim() || $el.find("span, div").first().text().trim()
        
        if (href && title && title.length > 10) {
          const fullUrl = href.startsWith("http") ? href : `https://www.bloomberg.com${href}`
          
          items.push({
            id: href.split("/").pop() || href,
            title: title,
            link: fullUrl,
            publishedAt: new Date(),
            extra: {
              source: "Bloomberg"
            }
          })
        }
      })
      
      return items
      
    } catch (fallbackError) {
      console.error("Bloomberg fallback error:", fallbackError)
      return []
    }
  }
})