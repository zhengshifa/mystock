import { defineSource } from "../utils/source"
import { myFetch } from "../utils/fetch"
import * as cheerio from "cheerio"

export default defineSource({
  "yahoo-finance": {
    async fetch() {
      const response = await myFetch("https://finance.yahoo.com/news/")
      const $ = cheerio.load(response)
      const items: any[] = []

      // 抓取新闻标题和链接
      $('h3 a, .js-content-viewer').each((_, element) => {
        const $element = $(element)
        const title = $element.text().trim()
        let url = $element.attr('href')
        
        if (title && url) {
          // 处理相对链接
          if (url.startsWith('/')) {
            url = `https://finance.yahoo.com${url}`
          }
          
          items.push({
            title,
            url,
            extra: {
              date: new Date().toISOString()
            }
          })
        }
      })

      return items.slice(0, 20) // 限制返回前20条新闻
    },

    // 备用方法：抓取特定股票的新闻页面
    async fetchAlt() {
      try {
        const response = await myFetch("https://finance.yahoo.com/topic/stock-market-news/")
        const $ = cheerio.load(response)
        const items: any[] = []

        // 尝试不同的选择器
        $('h3 a, [data-test-locator="StreamTitle"] a, .js-stream-content a').each((_, element) => {
          const $element = $(element)
          const title = $element.text().trim()
          let url = $element.attr('href')
          
          if (title && url && title.length > 10) {
            // 处理相对链接
            if (url.startsWith('/')) {
              url = `https://finance.yahoo.com${url}`
            }
            
            items.push({
              title,
              url,
              extra: {
                date: new Date().toISOString()
              }
            })
          }
        })

        return items.slice(0, 15)
      } catch (error) {
        console.error('Yahoo Finance fetchAlt error:', error)
        return []
      }
    }
  }
})