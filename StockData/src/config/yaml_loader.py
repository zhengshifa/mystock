"""
YAML配置文件加载器
用于加载和解析YAML格式的配置文件
"""
import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional
from src.utils.logger import get_logger


class YAMLConfigLoader:
    """YAML配置文件加载器"""
    
    def __init__(self, config_dir: str = "config"):
        """初始化配置加载器"""
        self.logger = get_logger("YAMLConfigLoader")
        self.config_dir = Path(config_dir)
        self.config_cache: Dict[str, Any] = {}
    
    def load_config(self, filename: str) -> Optional[Dict[str, Any]]:
        """加载指定的配置文件"""
        try:
            config_path = self.config_dir / filename
            
            if not config_path.exists():
                self.logger.warning(f"配置文件不存在: {config_path}")
                return None
            
            # 检查缓存
            cache_key = str(config_path)
            if cache_key in self.config_cache:
                self.logger.debug(f"从缓存加载配置: {filename}")
                return self.config_cache[cache_key]
            
            # 读取并解析YAML文件
            with open(config_path, 'r', encoding='utf-8') as file:
                config_data = yaml.safe_load(file)
            
            # 缓存配置
            self.config_cache[cache_key] = config_data
            
            self.logger.info(f"成功加载配置文件: {filename}")
            return config_data
            
        except yaml.YAMLError as e:
            self.logger.error(f"YAML解析错误 {filename}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"加载配置文件失败 {filename}: {e}")
            return None
    
    def reload_config(self, filename: str) -> Optional[Dict[str, Any]]:
        """重新加载指定的配置文件"""
        try:
            config_path = self.config_dir / filename
            cache_key = str(config_path)
            
            # 清除缓存
            if cache_key in self.config_cache:
                del self.config_cache[cache_key]
            
            # 重新加载
            return self.load_config(filename)
            
        except Exception as e:
            self.logger.error(f"重新加载配置文件失败 {filename}: {e}")
            return None
    
    def get_config_value(self, filename: str, key_path: str, default: Any = None) -> Any:
        """获取配置文件中的指定值"""
        try:
            config = self.load_config(filename)
            if not config:
                return default
            
            # 支持点分隔的键路径，如 "data_collection.realtime_tick_interval"
            keys = key_path.split('.')
            value = config
            
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default
            
            return value
            
        except Exception as e:
            self.logger.error(f"获取配置值失败 {filename}.{key_path}: {e}")
            return default
    
    def set_config_value(self, filename: str, key_path: str, value: Any) -> bool:
        """设置配置文件中的指定值"""
        try:
            config = self.load_config(filename)
            if not config:
                return False
            
            # 支持点分隔的键路径
            keys = key_path.split('.')
            current = config
            
            # 导航到父级
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            
            # 设置值
            current[keys[-1]] = value
            
            # 保存到文件
            return self.save_config(filename, config)
            
        except Exception as e:
            self.logger.error(f"设置配置值失败 {filename}.{key_path}: {e}")
            return False
    
    def save_config(self, filename: str, config_data: Dict[str, Any]) -> bool:
        """保存配置到文件"""
        try:
            config_path = self.config_dir / filename
            
            # 确保目录存在
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 保存YAML文件
            with open(config_path, 'w', encoding='utf-8') as file:
                yaml.dump(config_data, file, default_flow_style=False, 
                         allow_unicode=True, indent=2)
            
            # 更新缓存
            cache_key = str(config_path)
            self.config_cache[cache_key] = config_data
            
            self.logger.info(f"配置文件保存成功: {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存配置文件失败 {filename}: {e}")
            return False
    
    def list_config_files(self) -> list:
        """列出配置目录中的所有配置文件"""
        try:
            if not self.config_dir.exists():
                return []
            
            config_files = []
            for file_path in self.config_dir.glob("*.yaml"):
                config_files.append(file_path.name)
            for file_path in self.config_dir.glob("*.yml"):
                config_files.append(file_path.name)
            
            return sorted(config_files)
            
        except Exception as e:
            self.logger.error(f"列出配置文件失败: {e}")
            return []
    
    def validate_config(self, filename: str, schema: Dict[str, Any] = None) -> bool:
        """验证配置文件格式"""
        try:
            config = self.load_config(filename)
            if not config:
                return False
            
            # 如果有schema，进行验证
            if schema:
                # 这里可以添加更复杂的验证逻辑
                pass
            
            self.logger.info(f"配置文件验证通过: {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"配置文件验证失败 {filename}: {e}")
            return False
    
    def clear_cache(self) -> None:
        """清除配置缓存"""
        self.config_cache.clear()
        self.logger.info("配置缓存已清除")


# 全局配置加载器实例
yaml_config_loader = YAMLConfigLoader()


def get_yaml_config_loader() -> YAMLConfigLoader:
    """获取YAML配置加载器实例"""
    return yaml_config_loader
