/**
 * 简单的测试新闻源
 * 用于验证调度器基本功能
 */

import type { SourceGetter } from "../types"

const source: SourceGetter = async (limit = 10) => {
  // 模拟新闻数据
  const mockNews = [
    {
      title: "测试新闻1 - 调度器运行正常",
      link: "https://example.com/news1",
      description: "这是一条测试新闻，用于验证调度器功能",
      id: "test-1",
      url: "https://example.com/news1"
    },
    {
      title: "测试新闻2 - MongoDB连接成功",
      link: "https://example.com/news2", 
      description: "MongoDB数据库连接测试通过",
      id: "test-2",
      url: "https://example.com/news2"
    },
    {
      title: "测试新闻3 - 新闻源发现正常",
      link: "https://example.com/news3",
      description: "新闻源自动发现功能正常工作",
      id: "test-3",
      url: "https://example.com/news3"
    }
  ]

  // 根据limit参数返回指定数量的新闻
  return mockNews.slice(0, limit)
}

export default source


