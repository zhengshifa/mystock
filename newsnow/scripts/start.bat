@echo off
chcp 65001 >nul
echo ========================================
echo NewsNow 调度器启动脚本
echo ========================================
echo.

REM 检查环境配置文件
if not exist ".env.scheduler" (
    echo 警告: 未找到 .env.scheduler 配置文件
    echo 正在复制示例配置文件...
    copy "example.env.scheduler" ".env.scheduler"
    echo 请编辑 .env.scheduler 文件配置您的环境
    echo.
)

REM 检查MongoDB连接
echo 正在检查MongoDB连接...
node -e "
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
"

if %errorlevel% neq 0 (
    echo.
    echo 按任意键退出...
    pause >nul
    exit /b 1
)

echo.
echo 选择运行模式:
echo 1. 定时模式 (持续运行)
echo 2. 单次运行 (测试用)
echo 3. 数据清理
echo 4. 查看统计
echo.
set /p choice="请输入选择 (1-4): "

if "%choice%"=="1" (
    echo 启动定时模式...
    pnpm start
) else if "%choice%"=="2" (
    echo 启动单次运行模式...
    pnpm start:once
) else if "%choice%"=="3" (
    echo 执行数据清理...
    pnpm cleanup
) else if "%choice%"=="4" (
    echo 查看数据库统计...
    pnpm cleanup:stats
) else (
    echo 无效选择，退出...
)

echo.
echo 按任意键退出...
pause >nul


