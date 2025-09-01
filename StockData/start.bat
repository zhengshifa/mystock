@echo off
echo 启动股票数据收集器...
echo.

REM 检查uv是否安装
where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo 错误: 未找到uv，请先安装uv
    echo 安装命令: pip install uv
    pause
    exit /b 1
)

REM 检查.env文件是否存在
if not exist ".env" (
    echo 警告: 未找到.env配置文件
    echo 请复制config.env.example为.env并配置相关参数
    echo.
    copy config.env.example .env
    echo 已创建.env文件，请编辑配置后重新运行
    pause
    exit /b 1
)

REM 启动程序
echo 使用守护进程模式启动...
uv run python main.py --mode daemon

pause
