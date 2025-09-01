"""
配置管理类
使用pydantic进行配置验证和环境变量管理
"""
import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置类"""
    
    # 掘金量化配置
    gm_token: str = Field(..., env="GM_TOKEN", description="掘金量化API Token")
    gm_username: str = Field(..., env="GM_USERNAME", description="掘金量化用户名")
    
    # MongoDB配置
    mongodb_uri: str = Field("mongodb://localhost:27017/", env="MONGODB_URI", description="MongoDB连接URI")
    mongodb_database: str = Field("stock_data", env="MONGODB_DATABASE", description="MongoDB数据库名")
    mongodb_username: Optional[str] = Field(None, env="MONGODB_USERNAME", description="MongoDB用户名")
    mongodb_password: Optional[str] = Field(None, env="MONGODB_PASSWORD", description="MongoDB密码")
    
    # 日志配置
    log_level: str = Field("INFO", env="LOG_LEVEL", description="日志级别")
    log_file: str = Field("logs/stock_collector.log", env="LOG_FILE", description="日志文件路径")
    
    # 数据收集配置
    collection_interval: int = Field(60, env="COLLECTION_INTERVAL", description="数据收集间隔(秒)")
    max_retry_count: int = Field(3, env="MAX_RETRY_COUNT", description="最大重试次数")
    batch_size: int = Field(1000, env="BATCH_SIZE", description="批量处理大小")
    
    # 代理配置
    http_proxy: Optional[str] = Field(None, env="HTTP_PROXY", description="HTTP代理")
    https_proxy: Optional[str] = Field(None, env="HTTPS_PROXY", description="HTTPS代理")
    
    class Config:
        """配置类配置"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def setup_proxy(self) -> None:
        """设置代理环境变量"""
        if self.http_proxy:
            os.environ["HTTP_PROXY"] = self.http_proxy
        if self.https_proxy:
            os.environ["HTTPS_PROXY"] = self.https_proxy
    
    def get_mongodb_connection_string(self) -> str:
        """获取MongoDB连接字符串"""
        if self.mongodb_username and self.mongodb_password:
            # 从URI中提取主机和端口
            uri_parts = self.mongodb_uri.rstrip("/").split("://")
            if len(uri_parts) == 2:
                protocol, host_port = uri_parts
                # 使用admin数据库进行认证
                return f"{protocol}://{self.mongodb_username}:{self.mongodb_password}@{host_port}/admin"
        return self.mongodb_uri


# 全局配置实例 - 延迟初始化
settings = None

def get_settings() -> Settings:
    """获取配置实例，延迟初始化"""
    global settings
    if settings is None:
        settings = Settings()
    return settings
