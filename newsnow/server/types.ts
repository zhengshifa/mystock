/**
 * 新闻源类型定义
 */

export interface NewsItem {
  title: string
  link: string
  description?: string
  image?: string
  author?: string
  publishedAt?: Date
  id?: string
  url?: string
  extra?: Record<string, any>
}

export interface SourceGetter {
  (limit?: number): Promise<NewsItem[]>
}

export type SourceID = string

export interface SourceOption {
  hiddenDate?: boolean
  limit?: number
}

export interface RSSHubOption {
  sorted?: boolean
  [key: string]: any
}

export interface RSSHubInfo {
  items: Array<{
    title: string
    url: string
    id?: string
    date_published?: string
  }>
}
