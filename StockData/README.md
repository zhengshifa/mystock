# 股票数据项目 (StockData)

这是一个使用掘金量化SDK的股票数据项目，用于连接掘金量化平台并获取股票数据。

## 项目结构

```
StockData/
├── pyproject.toml          # 项目配置文件
├── README.md               # 项目说明文档
├── src/                    # 源代码目录
│   ├── __init__.py
│   └── gm_client.py        # 掘金量化客户端
├── tests/                  # 测试目录
│   └── __init__.py
└── test_gm_connection.py   # 连接测试脚本
```

## 环境要求

- Python >= 3.11
- 掘金量化平台账号和访问令牌

## 安装和设置

### 1. 创建虚拟环境

```bash
# 使用uv创建虚拟环境
uv venv

# 激活虚拟环境
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate
```

### 2. 安装依赖

```bash
# 使用uv安装掘金量化SDK
uv pip install gm
```

### 3. 配置访问令牌

在 `src/gm_client.py` 或 `test_gm_connection.py` 中配置您的掘金量化访问令牌：

```python
token = "your_token_here"
```

## 使用方法

### 运行测试脚本

```bash
# 使用uv运行测试脚本
uv run python test_gm_connection.py
```

### 使用客户端类

```python
from src.gm_client import GMClient

# 创建客户端实例
client = GMClient("your_token")

# 连接平台
if client.connect():
    # 获取账户信息
    account_info = client.get_account_info()
    print(account_info)
    
    # 断开连接
    client.disconnect()
```

## 功能特性

- 自动连接掘金量化平台
- 连接状态测试
- 账户信息获取
- 完整的错误处理和日志记录
- 类型提示支持

## 注意事项

- 请确保您的掘金量化账号有效且令牌未过期
- 首次使用可能需要完成掘金量化平台的实名认证
- 建议在测试环境中先验证连接功能

## 开发说明

- 使用 `uv` 管理Python环境和依赖
- 代码包含完整的函数级注释
- 遵循Python编码规范
- 包含完整的错误处理机制
