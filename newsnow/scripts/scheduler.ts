#!/usr/bin/env tsx

/**
 * 新闻数据定时获取调度器
 * 自动定时获取各新闻源数据并持久化到MongoDB
 */

import { config } from 'dotenv'
import { consola } from 'consola'
import { initMongoDB, getMongoDatabase, closeMongoDB } from '../server/database/mongodb'
import { getters } from '../server/getters'
import type { SourceID } from '../shared/types'
import { sleep } from '../server/utils'

// 加载环境变量
config({ path: '.env.scheduler' })

// 配置
const CONFIG = {
  // 数据获取间隔（毫秒）
  FETCH_INTERVAL: 5 * 60 * 1000, // 5分钟
  // 每次获取的最大新闻数量
  MAX_NEWS_PER_SOURCE: 50,
  // 重试次数
  MAX_RETRIES: 3,
  // 重试延迟（毫秒）
  RETRY_DELAY: 1000
}

/**
 * 获取单个新闻源的数据
 */
async function fetchSourceData(sourceId: SourceID) {
  const getter = getters[sourceId]
  if (!getter) {
    consola.warn(`未找到新闻源: ${sourceId}`)
    return null
  }

  try {
    consola.info(`开始获取新闻源: ${sourceId}`)
    const news = await getter(CONFIG.MAX_NEWS_PER_SOURCE)
    
    if (news && news.length > 0) {
      consola.success(`成功获取 ${sourceId} 的 ${news.length} 条新闻`)
      return { sourceId, news }
    } else {
      consola.info(`${sourceId} 没有新数据`)
      return null
    }
  } catch (error) {
    consola.error(`获取 ${sourceId} 数据失败:`, error)
    return null
  }
}

/**
 * 保存新闻数据到MongoDB
 */
async function saveNewsToMongoDB(sourceId: SourceID, news: any[]) {
  try {
    const db = await getMongoDatabase()
    const collection = db.collection('news')
    
    // 为每条新闻添加元数据
    const newsWithMetadata = news.map(item => ({
      ...item,
      sourceId,
      fetchedAt: new Date(),
      createdAt: new Date()
    }))
    
    // 批量插入数据
    const result = await collection.insertMany(newsWithMetadata)
    consola.success(`成功保存 ${sourceId} 的 ${result.insertedCount} 条新闻到MongoDB`)
    
    return result.insertedCount
  } catch (error) {
    consola.error(`保存 ${sourceId} 数据到MongoDB失败:`, error)
    throw error
  }
}

/**
 * 处理单个新闻源
 */
async function processSource(sourceId: SourceID) {
  let retries = 0
  
  while (retries < CONFIG.MAX_RETRIES) {
    try {
      const result = await fetchSourceData(sourceId)
      
      if (result && result.news.length > 0) {
        await saveNewsToMongoDB(sourceId, result.news)
      }
      
      return true
    } catch (error) {
      retries++
      consola.warn(`${sourceId} 处理失败，重试 ${retries}/${CONFIG.MAX_RETRIES}`)
      
      if (retries < CONFIG.MAX_RETRIES) {
        await sleep(CONFIG.RETRY_DELAY * retries)
      } else {
        consola.error(`${sourceId} 处理失败，已达到最大重试次数`)
        return false
      }
    }
  }
  
  return false
}

/**
 * 主调度函数
 */
async function runScheduler() {
  consola.info('启动新闻数据定时获取调度器...')
  
  try {
    // 初始化MongoDB连接
    await initMongoDB()
    consola.success('MongoDB连接成功')
    
    // 获取所有可用的新闻源
    const sourceIds = Object.keys(getters) as SourceID[]
    consola.info(`发现 ${sourceIds.length} 个新闻源: ${sourceIds.join(', ')}`)
    
    // 主循环
    while (true) {
      const startTime = Date.now()
      consola.info(`开始新一轮数据获取...`)
      
      // 并发处理所有新闻源
      const promises = sourceIds.map(sourceId => processSource(sourceId))
      const results = await Promise.allSettled(promises)
      
      // 统计结果
      const successCount = results.filter(r => r.status === 'fulfilled' && r.value).length
      const failCount = results.length - successCount
      
      consola.success(`本轮完成: 成功 ${successCount} 个，失败 ${failCount} 个`)
      
      // 计算下一轮等待时间
      const elapsed = Date.now() - startTime
      const waitTime = Math.max(0, CONFIG.FETCH_INTERVAL - elapsed)
      
      consola.info(`等待 ${Math.round(waitTime / 1000)} 秒后进行下一轮...`)
      await sleep(waitTime)
    }
    
  } catch (error) {
    consola.error('调度器运行失败:', error)
  } finally {
    // 清理资源
    await closeMongoDB()
    consola.info('调度器已停止')
  }
}

/**
 * 单次运行模式（用于测试）
 */
async function runOnce() {
  consola.info('运行单次数据获取...')
  
  try {
    await initMongoDB()
    consola.success('MongoDB连接成功')
    
    const sourceIds = Object.keys(getters) as SourceID[]
    consola.info(`发现 ${sourceIds.length} 个新闻源`)
    
    if (sourceIds.length === 0) {
      consola.warn('没有找到任何新闻源，请检查源文件导入')
      return
    }
    
    // 串行处理所有新闻源
    for (const sourceId of sourceIds) {
      await processSource(sourceId)
      // 添加短暂延迟避免请求过于频繁
      await sleep(1000)
    }
    
    consola.success('单次数据获取完成')
  } catch (error) {
    consola.error('单次数据获取失败:', error)
  } finally {
    await closeMongoDB()
  }
}

// 主程序入口
async function main() {
  try {
    consola.info('启动新闻调度器...')
    const args = process.argv.slice(2)
    
    if (args.includes('--once') || args.includes('-o')) {
      consola.info('运行单次模式')
      await runOnce()
    } else {
      consola.info('运行定时模式')
      await runScheduler()
    }
  } catch (error) {
    consola.error('调度器启动失败:', error)
    process.exit(1)
  }
}

// 优雅退出处理
process.on('SIGINT', async () => {
  consola.info('收到退出信号，正在关闭...')
  await closeMongoDB()
  process.exit(0)
})

process.on('SIGTERM', async () => {
  consola.info('收到终止信号，正在关闭...')
  await closeMongoDB()
  process.exit(0)
})

// 运行主程序
main().catch(console.error)


