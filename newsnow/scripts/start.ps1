#!/usr/bin/env pwsh

<#
.SYNOPSIS
    NewsNow 调度器启动脚本
.DESCRIPTION
    提供交互式菜单来启动不同的调度器功能
.PARAMETER AutoStart
    自动启动定时模式，不显示菜单
#>

param(
    [switch]$AutoStart
)

# 设置控制台编码
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "NewsNow 调度器启动脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查环境配置文件
if (-not (Test-Path ".env.scheduler")) {
    Write-Host "警告: 未找到 .env.scheduler 配置文件" -ForegroundColor Yellow
    Write-Host "正在复制示例配置文件..." -ForegroundColor Green
    Copy-Item "example.env.scheduler" ".env.scheduler"
    Write-Host "请编辑 .env.scheduler 文件配置您的环境" -ForegroundColor Yellow
    Write-Host ""
}

# 检查MongoDB连接
Write-Host "正在检查MongoDB连接..." -ForegroundColor Blue
try {
    $mongoTest = @"
import('mongodb').then(async ({ MongoClient }) => {
    try {
        const client = new MongoClient('mongodb://localhost:27017');
        await client.connect();
        console.log('✓ MongoDB连接成功');
        await client.close();
    } catch (error) {
        console.log('✗ MongoDB连接失败:', error.message);
        console.log('请确保MongoDB服务正在运行');
        process.exit(1);
    }
}).catch(console.error);
"@
    
    node -e $mongoTest
    if ($LASTEXITCODE -ne 0) {
        Write-Host "MongoDB连接失败，请检查服务状态" -ForegroundColor Red
        Read-Host "按回车键退出"
        exit 1
    }
} catch {
    Write-Host "MongoDB连接检查失败: $_" -ForegroundColor Red
    Read-Host "按回车键退出"
    exit 1
}

Write-Host ""

# 如果指定了自动启动，直接启动定时模式
if ($AutoStart) {
    Write-Host "自动启动定时模式..." -ForegroundColor Green
    pnpm start
    exit 0
}

# 显示菜单
do {
    Write-Host "选择运行模式:" -ForegroundColor Yellow
    Write-Host "1. 定时模式 (持续运行)" -ForegroundColor White
    Write-Host "2. 单次运行 (测试用)" -ForegroundColor White
    Write-Host "3. 数据清理" -ForegroundColor White
    Write-Host "4. 查看统计" -ForegroundColor White
    Write-Host "5. 退出" -ForegroundColor White
    Write-Host ""
    
    $choice = Read-Host "请输入选择 (1-5)"
    
    switch ($choice) {
        "1" {
            Write-Host "启动定时模式..." -ForegroundColor Green
            pnpm start
            break
        }
        "2" {
            Write-Host "启动单次运行模式..." -ForegroundColor Green
            pnpm start:once
            break
        }
        "3" {
            Write-Host "执行数据清理..." -ForegroundColor Green
            pnpm cleanup
            break
        }
        "4" {
            Write-Host "查看数据库统计..." -ForegroundColor Green
            pnpm cleanup:stats
            break
        }
        "5" {
            Write-Host "退出..." -ForegroundColor Yellow
            exit 0
        }
        default {
            Write-Host "无效选择，请重新输入" -ForegroundColor Red
            continue
        }
    }
    
    Write-Host ""
    $continue = Read-Host "是否继续？(y/n)"
    if ($continue -eq "n" -or $continue -eq "N") {
        break
    }
    Write-Host ""
} while ($true)

Write-Host "感谢使用 NewsNow 调度器！" -ForegroundColor Green


