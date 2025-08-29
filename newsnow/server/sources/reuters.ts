import { defineSource } from "../utils/source"
import { NewsItem } from "../types"
import { myFetch } from "../utils/fetch"
import * as cheerio from "cheerio"

export default defineSource(async () => {
  try {
    // 尝试从Reuters RSS feed获取新闻
    const rssUrl = "https://feeds.reuters.com/reuters/topNews"
    
    const response = await myFetch(rssUrl, {
      headers: {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
      },
    })
    
    const text = await response.text()
    const $ = cheerio.load(text, { xmlMode: true })
    
    const items: NewsItem[] = []
    
    $("item").each((index, element) => {
      if (index >= 20) return false // 限制20条新闻
      
      const $el = $(element)
      const title = $el.find("title").text().trim()
      const link = $el.find("link").text().trim()
      const pubDate = $el.find("pubDate").text().trim()
      const guid = $el.find("guid").text().trim()
      
      if (title && link) {
        items.push({
          id: guid || link.split("/").pop() || link,
          title: title,
          link: link,
          publishedAt: pubDate ? new Date(pubDate) : new Date(),
          extra: {
            source: "Reuters"
          }
        })
      }
    })
    
    if (items.length > 0) {
      return items
    }
    
    // 备用方案：从Reuters主页获取新闻
    throw new Error("RSS feed empty, trying fallback")
    
  } catch (error) {
    console.error("Reuters RSS fetch error:", error)
    
    // 备用方案：尝试从Reuters主页获取新闻
    try {
      const fallbackUrl = "https://www.reuters.com/"
      const response = await myFetch(fallbackUrl, {
        headers: {
          "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        },
      })
      
      const html = await response.text()
      const $ = cheerio.load(html)
      
      const items: NewsItem[] = []
      
      // 尝试从主页提取新闻链接
      $("a[href*='/world/'], a[href*='/business/'], a[href*='/markets/']").each((index, element) => {
        if (index >= 20) return false
        
        const $el = $(element)
        const href = $el.attr("href")
        let title = $el.text().trim()
        
        // 如果链接本身没有文本，尝试从子元素获取
        if (!title) {
          title = $el.find("span, div, h1, h2, h3, h4, h5, h6").first().text().trim()
        }
        
        if (href && title && title.length > 10) {
          const fullUrl = href.startsWith("http") ? href : `https://www.reuters.com${href}`
          
          items.push({
            id: href.split("/").pop() || href,
            title: title,
            link: fullUrl,
            publishedAt: new Date(),
            extra: {
              source: "Reuters"
            }
          })
        }
      })
      
      return items
      
    } catch (fallbackError) {
      console.error("Reuters fallback error:", fallbackError)
      return []
    }
  }
})