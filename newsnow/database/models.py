"""数据库模型定义"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class NewsItem:
    """新闻条目模型"""
    title: str
    url: str
    source_id: str
    description: Optional[str] = None
    image: Optional[str] = None
    author: Optional[str] = None
    published_at: Optional[datetime] = None
    extra: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "title": self.title,
            "url": self.url,
            "source_id": self.source_id,
            "description": self.description,
            "image": self.image,
            "author": self.author,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "extra": self.extra
        }


@dataclass
class SourceResponse:
    """新闻源响应模型"""
    status: str  # success, error, cache
    source_id: str
    items: List[NewsItem]
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "status": self.status,
            "source_id": self.source_id,
            "items": [item.to_dict() for item in self.items],
            "error_message": self.error_message,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class SourceInfo:
    """新闻源信息模型"""
    id: str
    name: str
    url: str
    type: str = "unknown"
    description: Optional[str] = None
    enabled: bool = True
    last_fetch: Optional[datetime] = None
    fetch_count: int = 0
    error_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "type": self.type,
            "description": self.description,
            "enabled": self.enabled,
            "last_fetch": self.last_fetch.isoformat() if self.last_fetch else None,
            "fetch_count": self.fetch_count,
            "error_count": self.error_count
        }
