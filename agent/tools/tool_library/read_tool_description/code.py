import json
import os

from ..utils import _truncate_json_content


def read_tool_description(
    tool_name: str,
    level: str,
    focus: list | None,
    max_tokens: int
) -> dict:
    """
    Load and return structured tool documentation from JSON files.
    Truncate content according to max_tokens.
    """
    contracts_path = os.path.join(os.path.dirname(__file__), 'realfin_toolkit.json')
    
    try:
        with open(contracts_path, 'r', encoding='utf-8') as f:
            tools = json.load(f)
        
        if tool_name not in tools:
            return {
                "status": "error",
                "error_type": "NOT_FOUND",
                "message": f"Tool '{tool_name}' not found"
            }
        
        tool_data = tools[tool_name]
        
        # 根据 level 构建返回内容
        if level == "contract":
            content = {
                "tool_name": tool_data.get("tool_name", ""),
                "package_key": tool_data.get("package_key", ""),
                "description": tool_data.get("description", ""),
                "arguments": tool_data.get("arguments", {}),
                "returns": tool_data.get("returns", {})
            }
        elif level == "schema":
            content = {
                "tool_name": tool_data.get("tool_name", ""),
                "input_semantics": tool_data.get("input_semantics", []),
                "output_semantics": tool_data.get("output_semantics", []),
                "produces": tool_data.get("produces", []),
                "consumes": tool_data.get("consumes", [])
            }
        elif level == "full":
            content = tool_data.copy()
        else:
            return {
                "status": "error",
                "error_type": "INVALID_PARAMETER",
                "message": f"Invalid level: {level}. Must be 'contract', 'schema', or 'full'"
            }
        
        # 如果提供了 focus，过滤返回的字段
        if focus is not None and len(focus) > 0:
            filtered_content = {}
            focus_set = set(focus)
            
            if "inputs" in focus_set:
                if "input_semantics" in content:
                    filtered_content["input_semantics"] = content["input_semantics"]
                if "arguments" in content:
                    filtered_content["arguments"] = content["arguments"]
            
            if "date_format" in focus_set:
                # 查找日期格式相关的信息
                if "input_semantics" in content:
                    date_fields = [
                        field for field in content["input_semantics"]
                        if "date" in field.get("semantic_type", "").lower() or "time" in field.get("semantic_type", "").lower()
                    ]
                    if date_fields:
                        filtered_content["date_format_fields"] = date_fields
            
            if "returns" in focus_set:
                if "output_semantics" in content:
                    filtered_content["output_semantics"] = content["output_semantics"]
                if "returns" in content:
                    filtered_content["returns"] = content["returns"]
            
            if "constraints" in focus_set:
                # 查找约束相关的信息（如 enum, required 等）
                constraints = {}
                if "arguments" in content:
                    for arg_name, arg_info in content["arguments"].items():
                        arg_constraints = {}
                        if "enum" in arg_info:
                            arg_constraints["enum"] = arg_info["enum"]
                        if "required" in arg_info:
                            arg_constraints["required"] = arg_info["required"]
                        if arg_constraints:
                            constraints[arg_name] = arg_constraints
                if constraints:
                    filtered_content["constraints"] = constraints
            
            if "error_model" in focus_set:
                if "error_model" in content:
                    filtered_content["error_model"] = content["error_model"]
            
            # 保留 tool_name 和 package_key（如果存在）
            if "tool_name" in content:
                filtered_content["tool_name"] = content["tool_name"]
            if "package_key" in content:
                filtered_content["package_key"] = content["package_key"]
            
            content = filtered_content
        
        # 截断内容以符合 max_tokens
        truncated_content, tokens_used = _truncate_json_content(content, max_tokens)
        
        return {
            "tool_name": tool_name,
            "level": level,
            "content": truncated_content,
            "tokens_used": tokens_used
        }
    
    except FileNotFoundError:
        return {
            "status": "error",
            "error_type": "FILE_NOT_FOUND",
            "message": f"Tool contracts file not found: {contracts_path}"
        }
    except json.JSONDecodeError as e:
        return {
            "status": "error",
            "error_type": "JSON_DECODE_ERROR",
            "message": f"Failed to parse tool contracts file: {e}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error_type": "INTERNAL_EXCEPTION",
            "message": f"Unexpected error: {e}"
        }
