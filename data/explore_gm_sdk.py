#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
掘金量化 GM SDK 数据接口探索脚本
"""

import gm
import inspect
import json
import os
import pkgutil
from datetime import datetime, timedelta

def explore_gm_package():
    """探索gm包的结构和子模块"""
    print("=" * 50)
    print("掘金量化 GM SDK 包结构探索")
    print("=" * 50)
    
    # 获取gm包的路径
    gm_path = gm.__path__ if hasattr(gm, '__path__') else None
    print(f"GM 包路径: {gm_path}")
    print(f"GM 包文件: {gm.__file__ if hasattr(gm, '__file__') else 'Unknown'}")
    print(f"GM 版本: {getattr(gm, '__version__', 'Unknown')}")
    
    # 获取所有属性
    gm_attributes = dir(gm)
    print(f"\nGM 模块属性 ({len(gm_attributes)} 个):")
    for attr in gm_attributes:
        if not attr.startswith('_'):
            attr_obj = getattr(gm, attr)
            attr_type = type(attr_obj).__name__
            print(f"  - {attr} ({attr_type})")
    
    # 查找子模块
    submodules = []
    if hasattr(gm, '__path__'):
        for importer, modname, ispkg in pkgutil.iter_modules(gm.__path__, gm.__name__ + "."):
            submodules.append(modname)
            print(f"发现子模块: {modname}")
    
    return {
        "gm_path": str(gm_path) if gm_path else None,
        "gm_file": getattr(gm, '__file__', None),
        "version": getattr(gm, '__version__', 'Unknown'),
        "attributes": [attr for attr in gm_attributes if not attr.startswith('_')],
        "submodules": submodules
    }

def try_import_common_modules():
    """尝试导入常见的gm子模块"""
    print("\n" + "=" * 50)
    print("尝试导入常见子模块")
    print("=" * 50)
    
    common_modules = [
        'gm.api',
        'gm.data',
        'gm.trade',
        'gm.strategy',
        'gm.backtest',
        'gm.realtime',
        'gm.utils',
        'gm.indicators',
        'gm.market_data',
        'gm.portfolio'
    ]
    
    successful_imports = {}
    
    for module_name in common_modules:
        try:
            module = __import__(module_name, fromlist=[''])
            attrs = [attr for attr in dir(module) if not attr.startswith('_')]
            successful_imports[module_name] = {
                'attributes': attrs,
                'functions': [],
                'classes': []
            }
            
            # 分类属性
            for attr_name in attrs:
                attr = getattr(module, attr_name)
                if inspect.isfunction(attr):
                    successful_imports[module_name]['functions'].append(attr_name)
                elif inspect.isclass(attr):
                    successful_imports[module_name]['classes'].append(attr_name)
            
            print(f"✓ {module_name}: {len(attrs)} 个属性")
            print(f"  函数: {len(successful_imports[module_name]['functions'])}")
            print(f"  类: {len(successful_imports[module_name]['classes'])}")
            
        except ImportError as e:
            print(f"✗ {module_name}: 导入失败 - {e}")
        except Exception as e:
            print(f"✗ {module_name}: 其他错误 - {e}")
    
    return successful_imports

def explore_gm_api():
    """专门探索gm.api模块"""
    print("\n" + "=" * 50)
    print("探索 gm.api 模块")
    print("=" * 50)
    
    try:
        from gm import api
        
        # 获取所有API函数
        api_functions = []
        for attr_name in dir(api):
            if not attr_name.startswith('_'):
                attr = getattr(api, attr_name)
                if callable(attr):
                    try:
                        sig = inspect.signature(attr)
                        doc = inspect.getdoc(attr) or "无文档"
                        api_functions.append({
                            'name': attr_name,
                            'signature': str(sig),
                            'doc': doc[:200] + '...' if len(doc) > 200 else doc
                        })
                        print(f"\n函数: {attr_name}")
                        print(f"  签名: {attr_name}{sig}")
                        print(f"  文档: {doc[:100]}..." if len(doc) > 100 else f"  文档: {doc}")
                    except Exception as e:
                        print(f"  获取 {attr_name} 信息时出错: {e}")
        
        # 保存API函数信息
        with open('gm_api_functions.json', 'w', encoding='utf-8') as f:
            json.dump(api_functions, f, ensure_ascii=False, indent=2)
        
        return api_functions
        
    except ImportError as e:
        print(f"无法导入 gm.api: {e}")
        return []
    except Exception as e:
        print(f"探索 gm.api 时出错: {e}")
        return []

if __name__ == "__main__":
    try:
        # 探索包结构
        package_info = explore_gm_package()
        
        # 尝试导入常见模块
        imported_modules = try_import_common_modules()
        
        # 专门探索API模块
        api_functions = explore_gm_api()
        
        # 保存完整信息
        complete_info = {
            'package_info': package_info,
            'imported_modules': imported_modules,
            'api_functions_count': len(api_functions),
            'exploration_time': datetime.now().isoformat()
        }
        
        with open('gm_complete_exploration.json', 'w', encoding='utf-8') as f:
            json.dump(complete_info, f, ensure_ascii=False, indent=2)
        
        print(f"\n探索完成！")
        print(f"成功导入 {len(imported_modules)} 个模块")
        print(f"发现 {len(api_functions)} 个API函数")
        print("详细信息已保存到:")
        print("  - gm_complete_exploration.json")
        print("  - gm_api_functions.json")
        
    except Exception as e:
        print(f"探索过程中出现错误: {e}")
        import traceback
        traceback.print_exc()