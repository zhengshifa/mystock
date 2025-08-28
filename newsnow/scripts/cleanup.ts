#!/usr/bin/env tsx

/**
 * 数据清理脚本
 * 定期清理过期的新闻数据，保持数据库性能
 */

import { consola } from 'consola'
import { initMongoDB, getMongoDatabase, closeMongoDB } from '../server/database/mongodb'
import { getConfig } from './config'

/**
 * 清理过期的新闻数据
 */
async function cleanupExpiredNews() {
  try {
    const db = await getMongoDatabase()
    const collection = db.collection('news')
    
    const config = getConfig()
    const cutoffDate = new Date(Date.now() - config.cleanup.keepDays * 24 * 60 * 60 * 1000)
    
    consola.info(`清理 ${cutoffDate.toISOString()} 之前的过期数据...`)
    
    // 删除过期的新闻
    const result = await collection.deleteMany({
      createdAt: { $lt: cutoffDate }
    })
    
    consola.success(`成功清理 ${result.deletedCount} 条过期新闻`)
    
    // 可选：清理重复数据（基于标题和来源）
    await cleanupDuplicateNews(collection)
    
    return result.deletedCount
  } catch (error) {
    consola.error('清理过期数据失败:', error)
    throw error
  }
}

/**
 * 清理重复的新闻数据
 */
async function cleanupDuplicateNews(collection: any) {
  try {
    consola.info('检查并清理重复数据...')
    
    // 使用聚合管道查找重复数据
    const duplicates = await collection.aggregate([
      {
        $group: {
          _id: {
            title: '$title',
            sourceId: '$sourceId'
          },
          count: { $sum: 1 },
          docs: { $push: '$_id' }
        }
      },
      {
        $match: {
          count: { $gt: 1 }
        }
      }
    ]).toArray()
    
    if (duplicates.length === 0) {
      consola.info('没有发现重复数据')
      return 0
    }
    
    let totalDeleted = 0
    
    for (const duplicate of duplicates) {
      // 保留最新的数据，删除其他重复项
      const docsToDelete = duplicate.docs.slice(1) // 保留第一个（最新的）
      
      const deleteResult = await collection.deleteMany({
        _id: { $in: docsToDelete }
      })
      
      totalDeleted += deleteResult.deletedCount
      consola.info(`清理 ${duplicate._id.sourceId} 的重复标题 "${duplicate._id.title}": 删除 ${deleteResult.deletedCount} 条`)
    }
    
    consola.success(`总共清理 ${totalDeleted} 条重复数据`)
    return totalDeleted
  } catch (error) {
    consola.error('清理重复数据失败:', error)
    return 0
  }
}

/**
 * 清理空的或无效的数据
 */
async function cleanupInvalidNews() {
  try {
    const db = await getMongoDatabase()
    const collection = db.collection('news')
    
    consola.info('清理无效数据...')
    
    // 删除没有标题的数据
    const noTitleResult = await collection.deleteMany({
      $or: [
        { title: { $exists: false } },
        { title: null },
        { title: '' }
      ]
    })
    
    // 删除没有链接的数据
    const noLinkResult = await collection.deleteMany({
      $or: [
        { link: { $exists: false } },
        { link: null },
        { link: '' }
      ]
    })
    
    const totalDeleted = noTitleResult.deletedCount + noLinkResult.deletedCount
    
    if (totalDeleted > 0) {
      consola.success(`清理无效数据完成: 无标题 ${noTitleResult.deletedCount} 条，无链接 ${noLinkResult.deletedCount} 条`)
    } else {
      consola.info('没有发现无效数据')
    }
    
    return totalDeleted
  } catch (error) {
    consola.error('清理无效数据失败:', error)
    return 0
  }
}

/**
 * 获取数据库统计信息
 */
async function getDatabaseStats() {
  try {
    const db = await getMongoDatabase()
    const collection = db.collection('news')
    
    const totalCount = await collection.countDocuments()
    const sourceStats = await collection.aggregate([
      {
        $group: {
          _id: '$sourceId',
          count: { $sum: 1 },
          latest: { $max: '$createdAt' },
          oldest: { $min: '$createdAt' }
        }
      },
      {
        $sort: { count: -1 }
      }
    ]).toArray()
    
    consola.info(`数据库统计信息:`)
    consola.info(`总新闻数: ${totalCount}`)
    consola.info(`各来源统计:`)
    
    sourceStats.forEach(stat => {
      consola.info(`  ${stat._id}: ${stat.count} 条 (${stat.oldest?.toISOString()} ~ ${stat.latest?.toISOString()})`)
    })
    
    return { totalCount, sourceStats }
  } catch (error) {
    consola.error('获取数据库统计信息失败:', error)
    return null
  }
}

/**
 * 主清理函数
 */
async function runCleanup() {
  consola.info('开始数据清理任务...')
  
  try {
    await initMongoDB()
    consola.success('MongoDB连接成功')
    
    // 获取清理前的统计信息
    const beforeStats = await getDatabaseStats()
    
    // 执行清理任务
    const expiredCount = await cleanupExpiredNews()
    const duplicateCount = await cleanupDuplicateNews(await getMongoDatabase().then(db => db.collection('news')))
    const invalidCount = await cleanupInvalidNews()
    
    // 获取清理后的统计信息
    const afterStats = await getDatabaseStats()
    
    // 输出清理结果
    consola.success('数据清理任务完成!')
    consola.info(`清理结果:`)
    consola.info(`  过期数据: ${expiredCount} 条`)
    consola.info(`  重复数据: ${duplicateCount} 条`)
    consola.info(`  无效数据: ${invalidCount} 条`)
    consola.info(`  总计清理: ${expiredCount + duplicateCount + invalidCount} 条`)
    
    if (beforeStats && afterStats) {
      const reduction = beforeStats.totalCount - afterStats.totalCount
      consola.info(`数据库大小减少: ${reduction} 条`)
    }
    
  } catch (error) {
    consola.error('数据清理任务失败:', error)
  } finally {
    await closeMongoDB()
  }
}

// 主程序入口
async function main() {
  const args = process.argv.slice(2)
  
  if (args.includes('--stats') || args.includes('-s')) {
    // 只显示统计信息
    await initMongoDB()
    await getDatabaseStats()
    await closeMongoDB()
  } else {
    // 执行完整清理
    await runCleanup()
  }
}

// 优雅退出处理
process.on('SIGINT', async () => {
  consola.info('收到退出信号，正在关闭...')
  await closeMongoDB()
  process.exit(0)
})

// 运行主程序
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(console.error)
}


