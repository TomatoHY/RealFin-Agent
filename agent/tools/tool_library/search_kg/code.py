import json
import os
import traceback

from typing import Optional, Any, Dict

from ..utils import _log_debug


def search_kg(
entity_name: str, kg_file_path: str = None
) -> Optional[Dict[str, Any]]:
    """
    搜索知识图谱（kg.json）获取实体组信息
    
    Args:
        entity_name (str): 要搜索的实体名称，可以是ID、别名或描述中的关键词
        kg_file_path (str): kg.json文件的路径，如果为None则使用默认路径（相对于当前文件所在目录）
    
    Returns:
        Optional[Dict[str, Any]]: 如果找到匹配的实体，返回包含以下字段的字典:
            - id: 实体ID
            - aliases: 别名列表
            - description: 描述
            - region: 地区
            - count: 成员数量
            - members: 成员列表
            如果未找到或出错，返回错误信息字符串
    """
    try:
        # 检查输入是否为空
        if not entity_name or not entity_name.strip():
            error_msg = "错误: 实体名称不能为空"
            _log_debug(f"  -> {error_msg}")
            return error_msg
        
        _log_debug(f"--- 正在搜索知识图谱，查找实体: '{entity_name}' ---")
        
        # 如果没有指定路径，使用默认路径（相对于当前文件所在目录）
        if kg_file_path is None:
            kg_file_path = os.path.join(os.path.dirname(__file__), 'kg.json')
        
        # 如果是相对路径且不是相对于当前文件的，尝试解析为相对于当前文件的路径
        elif not os.path.isabs(kg_file_path) and not os.path.exists(kg_file_path):
            # 尝试相对于当前文件所在目录
            alt_path = os.path.join(os.path.dirname(__file__), kg_file_path)
            if os.path.exists(alt_path):
                kg_file_path = alt_path
            else:
                # 尝试相对于项目根目录（data/kg.json）
                alt_path = os.path.join(os.path.dirname(__file__), os.path.basename(kg_file_path))
                if os.path.exists(alt_path):
                    kg_file_path = alt_path
        
        # 加载kg.json文件
        if not os.path.exists(kg_file_path):
            error_msg = f"错误: 知识图谱文件不存在: {kg_file_path}"
            _log_debug(f"  -> {error_msg}")
            return error_msg
        
        with open(kg_file_path, 'r', encoding='utf-8') as f:
            entities = json.load(f)
        
        # 搜索匹配的实体
        entity_name_lower = entity_name.strip().lower()
        
        for entity in entities:
            # 检查ID
            if entity_name_lower == entity.get('id', '').lower():
                _log_debug(f"*** 找到实体（通过ID）: {entity.get('id')} ***")
                return entity
            
            # 检查别名
            aliases = entity.get('aliases', [])
            for alias in aliases:
                if entity_name_lower == alias.lower():
                    _log_debug(f"*** 找到实体（通过别名）: {alias} (ID: {entity.get('id')}) ***")
                    return entity
            
            # 检查别名中是否包含关键词（部分匹配，但排除空字符串）
            if len(entity_name_lower) > 0:
                for alias in aliases:
                    alias_lower = alias.lower()
                    if entity_name_lower in alias_lower or alias_lower in entity_name_lower:
                        _log_debug(f"*** 找到实体（通过别名部分匹配）: {alias} (ID: {entity.get('id')}) ***")
                        return entity
        
        # 未找到匹配的实体
        error_msg = f"错误: 未找到匹配的实体 '{entity_name}'。请检查实体名称是否正确。"
        _log_debug(f"  -> {error_msg}")
        return error_msg
    
    except FileNotFoundError:
        error_msg = f"错误: 知识图谱文件不存在: {kg_file_path}"
        _log_debug(f"  -> {error_msg}")
        return error_msg
    except json.JSONDecodeError as e:
        error_msg = f"错误: 解析知识图谱JSON文件失败: {str(e)}"
        _log_debug(f"  -> {error_msg}")
        return error_msg
    except Exception as e:
        error_msg = f"错误: 搜索知识图谱时出错: {str(e)}"
        _log_debug(f"  -> {error_msg}")
        traceback.print_exc()
        return error_msg
