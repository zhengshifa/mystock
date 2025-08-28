import * as cheerio from "cheerio"
import type { NewsItem } from "@shared/types"
import { defineSource } from "../utils/source"
import { myFetch } from "../utils/fetch"

/**
 * 获取Hacker News数据
 * 支持自动重试和代理切换
 */
export default defineSource(async () => {
  const baseURL = "https://news.ycombinator.com"
  const maxRetries = 3
  
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      console.log(`[HACKERNEWS] 尝试获取数据 (第${attempt}次): ${baseURL}`)
      
      const html: any = await myFetch(baseURL)
      
      if (!html) {
        throw new Error("获取到的HTML内容为空")
      }
      
      console.log(`[HACKERNEWS] 成功获取HTML内容，长度: ${html.length}`)
      
      const $ = cheerio.load(html)
      const $main = $(".athing")
      
      if ($main.length === 0) {
        throw new Error("未找到新闻条目，可能页面结构已变化")
      }
      
      console.log(`[HACKERNEWS] 找到 ${$main.length} 个新闻条目`)
      
      const news: NewsItem[] = []
      $main.each((_, el) => {
        try {
          const a = $(el).find(".titleline a").first()
          const title = a.text()?.trim()
          const id = $(el).attr("id")
          const score = $(`#score_${id}`).text()?.trim()
          const url = `${baseURL}/item?id=${id}`
          
          if (url && id && title) {
            news.push({
              url,
              title,
              id,
              extra: {
                info: score || "0 points",
              },
            })
          }
        } catch (itemError) {
          console.warn(`[HACKERNEWS] 处理单个新闻条目时出错:`, itemError)
          // 继续处理其他条目
        }
      })
      
      if (news.length === 0) {
        throw new Error("解析后没有有效的新闻数据")
      }
      
      console.log(`[HACKERNEWS] 成功解析 ${news.length} 条新闻`)
      return news
      
    } catch (error) {
      console.error(`[HACKERNEWS] 第${attempt}次尝试失败:`, error)
      
      if (attempt === maxRetries) {
        console.error(`[HACKERNEWS] 已达到最大重试次数，放弃获取`)
        throw error
      }
      
      // 等待后重试
      const delay = 2000 * attempt
      console.log(`[HACKERNEWS] 等待 ${delay}ms 后重试...`)
      await new Promise(resolve => setTimeout(resolve, delay))
    }
  }
  
  throw new Error("Hacker News数据获取失败")
})
