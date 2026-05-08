import json
import os

from ..utils import _truncate_json_content


def read_package_description(
package_key: str, level: str, max_tokens: int
) -> dict:
    """
    Load and return structured package documentation from JSON files.
    Truncate content according to max_tokens.
    """
    tool_package_path = os.path.join(os.path.dirname(__file__), 'tool_package.json')
    
    try:
        with open(tool_package_path, 'r', encoding='utf-8') as f:
            packages = json.load(f)
        
        if package_key not in packages:
            return {
                "status": "error",
                "error_type": "NOT_FOUND",
                "message": f"Package '{package_key}' not found"
            }
        
        package_data = packages[package_key]
        
        # 根据 level 构建返回内容
        if level == "brief":
            # 支持新格式 (one_line_desc) 和旧格式 (lite_desc)
            desc = package_data.get("one_line_desc", package_data.get("lite_desc", ""))
            # 处理 tools：可能是字符串数组或对象数组
            tools_list = package_data.get("tools", [])
            if tools_list and isinstance(tools_list[0], str):
                tools = tools_list
            else:
                tools = [tool.get("tool_name", "") if isinstance(tool, dict) else str(tool) for tool in tools_list]
            
            content = {
                "package_key": package_key,
                "package_name": package_data.get("package_name", ""),
                "one_line_desc": desc,
                "tools": tools
            }
        elif level == "full":
            content = {
                "package_key": package_key,
                "package_name": package_data.get("package_name", ""),
                "one_line_desc": package_data.get("one_line_desc", package_data.get("lite_desc", "")),
                "detailed_desc": package_data.get("detailed_desc", ""),
                "lite_desc": package_data.get("lite_desc", ""),
                "tools": package_data.get("tools", [])
            }
        else:
            return {
                "status": "error",
                "error_type": "INVALID_PARAMETER",
                "message": f"Invalid level: {level}. Must be 'brief' or 'full'"
            }
        
        # 截断内容以符合 max_tokens
        truncated_content, tokens_used = _truncate_json_content(content, max_tokens)
        
        return {
            "package_key": package_key,
            "level": level,
            "content": truncated_content,
            "tokens_used": tokens_used
        }
    
    except FileNotFoundError:
        return {
            "status": "error",
            "error_type": "FILE_NOT_FOUND",
            "message": f"Tool package file not found: {tool_package_path}"
        }
    except json.JSONDecodeError as e:
        return {
            "status": "error",
            "error_type": "JSON_DECODE_ERROR",
            "message": f"Failed to parse tool package file: {e}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error_type": "INTERNAL_EXCEPTION",
            "message": f"Unexpected error: {e}"
        }
