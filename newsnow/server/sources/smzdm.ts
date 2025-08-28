import * as cheerio from "cheerio"
import type { NewsItem } from "@shared/types"
import { defineSource } from "../utils/source"
import { myFetch } from "../utils/fetch"

export default defineSource(async () => {
  const baseURL = "https://post.smzdm.com/hot_1/"
  const html: any = await myFetch(baseURL)
  const $ = cheerio.load(html)
  const $main = $("#feed-main-list .z-feed-title")
  const news: NewsItem[] = []
  $main.each((_, el) => {
    const a = $(el).find("a")
    const url = a.attr("href")!
    const title = a.text()
    news.push({
      url,
      title,
      id: url,
    })
  })
  return news
})
