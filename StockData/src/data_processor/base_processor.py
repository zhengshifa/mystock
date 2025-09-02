#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据处理器基类

定义所有数据处理器的通用接口和功能，包括:
- 数据验证
- 数据转换
- 数据清洗
- 错误处理
- 性能监控
"""

import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from abc import ABC, abstractmethod
from loguru import logger
import pandas as pd

from ..database import RepositoryManager, DataType
from ..gm_api import GMClient


class DataProcessingError(Exception):
    """数据处理异常"""
    pass


class BaseDataProcessor(ABC):
    """数据处理器基类"""
    
    def __init__(self, 
                 gm_client: GMClient, 
                 repository_manager: RepositoryManager,
                 config: Dict[str, Any]):
        self.gm_client = gm_client
        self.repository_manager = repository_manager
        self.config = config
        
        # 处理器配置
        self.batch_size = config.get('batch_size', 1000)
        self.retry_times = config.get('retry_times', 3)
        self.retry_delay = config.get('retry_delay', 1)
        self.enable_validation = config.get('enable_validation', True)
        
        # 性能统计
        self.stats = {
            'processed_count': 0,
            'error_count': 0,
            'start_time': None,
            'last_process_time': None
        }
        
        logger.info(f"{self.__class__.__name__} 初始化完成")
    
    @property
    @abstractmethod
    def data_type(self) -> DataType:
        """数据类型"""
        pass
    
    @property
    @abstractmethod
    def processor_name(self) -> str:
        """处理器名称"""
        pass
    
    @abstractmethod
    async def fetch_data(self, **kwargs) -> Union[Dict[str, Any], List[Dict[str, Any]], None]:
        """获取数据"""
        pass
    
    @abstractmethod
    async def process_data(self, raw_data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """处理数据"""
        pass
    
    @abstractmethod
    async def save_data(self, processed_data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> bool:
        """保存数据"""
        pass
    
    async def run(self, **kwargs) -> bool:
        """运行数据处理流程"""
        try:
            logger.info(f"开始运行 {self.processor_name} 数据处理")
            self.stats['start_time'] = datetime.now()
            
            # 1. 获取数据
            raw_data = await self._fetch_with_retry(**kwargs)
            if not raw_data:
                logger.warning(f"{self.processor_name} 未获取到数据")
                return True
            
            # 2. 处理数据
            processed_data = await self._process_with_validation(raw_data)
            if not processed_data:
                logger.warning(f"{self.processor_name} 数据处理后为空")
                return True
            
            # 3. 保存数据
            success = await self._save_with_retry(processed_data)
            
            # 4. 更新统计信息
            self._update_stats(processed_data, success)
            
            self.stats['last_process_time'] = datetime.now()
            
            if success:
                logger.info(f"{self.processor_name} 数据处理完成")
            else:
                logger.error(f"{self.processor_name} 数据保存失败")
            
            return success
            
        except Exception as e:
            self.stats['error_count'] += 1
            logger.error(f"{self.processor_name} 数据处理异常: {e}")
            return False
    
    async def _fetch_with_retry(self, **kwargs) -> Union[Dict[str, Any], List[Dict[str, Any]], None]:
        """带重试的数据获取"""
        for attempt in range(self.retry_times):
            try:
                return await self.fetch_data(**kwargs)
            except Exception as e:
                logger.warning(f"{self.processor_name} 数据获取失败 (尝试 {attempt + 1}/{self.retry_times}): {e}")
                if attempt < self.retry_times - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                else:
                    raise DataProcessingError(f"数据获取失败: {e}")
    
    async def _process_with_validation(self, raw_data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """带验证的数据处理"""
        try:
            # 数据预处理验证
            if self.enable_validation:
                validated_data = await self._validate_raw_data(raw_data)
            else:
                validated_data = raw_data
            
            # 数据处理
            processed_data = await self.process_data(validated_data)
            
            # 数据后处理验证
            if self.enable_validation:
                final_data = await self._validate_processed_data(processed_data)
            else:
                final_data = processed_data
            
            return final_data
            
        except Exception as e:
            raise DataProcessingError(f"数据处理失败: {e}")
    
    async def _save_with_retry(self, processed_data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> bool:
        """带重试的数据保存"""
        for attempt in range(self.retry_times):
            try:
                return await self.save_data(processed_data)
            except Exception as e:
                logger.warning(f"{self.processor_name} 数据保存失败 (尝试 {attempt + 1}/{self.retry_times}): {e}")
                if attempt < self.retry_times - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                else:
                    logger.error(f"{self.processor_name} 数据保存最终失败: {e}")
                    return False
    
    async def _validate_raw_data(self, raw_data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """验证原始数据"""
        try:
            if isinstance(raw_data, list):
                if not raw_data:
                    raise DataProcessingError("原始数据列表为空")
                
                # 验证列表中的每个元素
                validated_list = []
                for item in raw_data:
                    if isinstance(item, dict) and item:
                        validated_list.append(item)
                
                if not validated_list:
                    raise DataProcessingError("原始数据列表中没有有效数据")
                
                return validated_list
            
            elif isinstance(raw_data, dict):
                if not raw_data:
                    raise DataProcessingError("原始数据字典为空")
                return raw_data
            
            else:
                raise DataProcessingError(f"不支持的原始数据类型: {type(raw_data)}")
                
        except Exception as e:
            raise DataProcessingError(f"原始数据验证失败: {e}")
    
    async def _validate_processed_data(self, processed_data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """验证处理后数据"""
        try:
            if isinstance(processed_data, list):
                if not processed_data:
                    logger.warning(f"{self.processor_name} 处理后数据列表为空")
                    return []
                
                # 验证列表中的每个元素
                validated_list = []
                for item in processed_data:
                    if self._is_valid_data_item(item):
                        validated_list.append(item)
                    else:
                        logger.warning(f"{self.processor_name} 发现无效数据项: {item}")
                
                return validated_list
            
            elif isinstance(processed_data, dict):
                if self._is_valid_data_item(processed_data):
                    return processed_data
                else:
                    raise DataProcessingError("处理后数据验证失败")
            
            else:
                raise DataProcessingError(f"不支持的处理后数据类型: {type(processed_data)}")
                
        except Exception as e:
            raise DataProcessingError(f"处理后数据验证失败: {e}")
    
    def _is_valid_data_item(self, item: Dict[str, Any]) -> bool:
        """验证单个数据项"""
        try:
            # 基本验证
            if not isinstance(item, dict) or not item:
                return False
            
            # 子类可以重写此方法进行特定验证
            return self._validate_data_item(item)
            
        except Exception:
            return False
    
    def _validate_data_item(self, item: Dict[str, Any]) -> bool:
        """验证数据项（子类可重写）"""
        return True
    
    def _update_stats(self, processed_data: Union[Dict[str, Any], List[Dict[str, Any]]], success: bool):
        """更新统计信息"""
        try:
            if isinstance(processed_data, list):
                count = len(processed_data)
            else:
                count = 1
            
            if success:
                self.stats['processed_count'] += count
            else:
                self.stats['error_count'] += count
                
        except Exception as e:
            logger.error(f"更新统计信息失败: {e}")
    
    # ==================== 数据转换工具方法 ====================
    
    def _convert_to_dataframe(self, data: List[Dict[str, Any]]) -> pd.DataFrame:
        """转换为DataFrame"""
        try:
            if not data:
                return pd.DataFrame()
            return pd.DataFrame(data)
        except Exception as e:
            logger.error(f"转换DataFrame失败: {e}")
            return pd.DataFrame()
    
    def _convert_from_dataframe(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """从DataFrame转换"""
        try:
            if df.empty:
                return []
            return df.to_dict('records')
        except Exception as e:
            logger.error(f"从DataFrame转换失败: {e}")
            return []
    
    def _clean_numeric_data(self, value: Any) -> Optional[float]:
        """清洗数值数据"""
        try:
            if value is None or value == '' or pd.isna(value):
                return None
            
            if isinstance(value, (int, float)):
                return float(value)
            
            if isinstance(value, str):
                # 移除常见的非数字字符
                cleaned = value.replace(',', '').replace('%', '').strip()
                if cleaned == '' or cleaned == '-' or cleaned.lower() == 'nan':
                    return None
                return float(cleaned)
            
            return float(value)
            
        except (ValueError, TypeError):
            return None
    
    def _clean_string_data(self, value: Any) -> Optional[str]:
        """清洗字符串数据"""
        try:
            if value is None or pd.isna(value):
                return None
            
            if isinstance(value, str):
                cleaned = value.strip()
                return cleaned if cleaned else None
            
            return str(value).strip()
            
        except Exception:
            return None
    
    def _format_datetime(self, value: Any, format_str: str = '%Y-%m-%d') -> Optional[str]:
        """格式化日期时间"""
        try:
            if value is None or pd.isna(value):
                return None
            
            if isinstance(value, str):
                # 尝试解析字符串日期
                if value.strip() == '' or value.strip() == '-':
                    return None
                
                # 常见日期格式
                for fmt in ['%Y-%m-%d', '%Y%m%d', '%Y/%m/%d', '%Y-%m-%d %H:%M:%S']:
                    try:
                        dt = datetime.strptime(value.strip(), fmt)
                        return dt.strftime(format_str)
                    except ValueError:
                        continue
                
                return value.strip()
            
            elif isinstance(value, datetime):
                return value.strftime(format_str)
            
            else:
                return str(value)
                
        except Exception:
            return None
    
    # ==================== 状态和统计方法 ====================
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = self.stats.copy()
        
        if stats['start_time']:
            runtime = datetime.now() - stats['start_time']
            stats['runtime_seconds'] = runtime.total_seconds()
            
            if runtime.total_seconds() > 0:
                stats['processing_rate'] = stats['processed_count'] / runtime.total_seconds()
            else:
                stats['processing_rate'] = 0
        
        stats['processor_name'] = self.processor_name
        stats['data_type'] = self.data_type.value
        
        return stats
    
    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            'processed_count': 0,
            'error_count': 0,
            'start_time': None,
            'last_process_time': None
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            return {
                'processor_name': self.processor_name,
                'data_type': self.data_type.value,
                'status': 'healthy',
                'stats': self.get_stats(),
                'config': {
                    'batch_size': self.batch_size,
                    'retry_times': self.retry_times,
                    'enable_validation': self.enable_validation
                }
            }
        except Exception as e:
            return {
                'processor_name': self.processor_name,
                'data_type': self.data_type.value,
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def __str__(self) -> str:
        return f"{self.processor_name}(data_type={self.data_type.value})"
    
    def __repr__(self) -> str:
        return self.__str__()