import random
import re
from typing import Any, Dict, Set


def _get_necessary_tools(tool_desc: Dict[str, dict], code: str) -> Dict[str, dict]:
    """匹配所有code中的函数名称"""
    selected_tools = {}
    func_pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
    matches = re.findall(func_pattern, code)
    matched_tool_names = set()
    for match in matches:
        if match in tool_desc:
            matched_tool_names.add(match)
    for tool_name in matched_tool_names:
        selected_tools[tool_name] = tool_desc[tool_name]
    return selected_tools


def _get_related_tools(necessary_tools: Dict[str, Dict[str, Any]], tool_desc: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """根据"""
    selected_tools = {}
    related_tools = set()
    for tool_name, tool_info in necessary_tools.items():
        for related_tool_name in tool_info["related_tools"]:
            related_tools.add(related_tool_name)
    for tool_name in related_tools:
        selected_tools[tool_name] = tool_desc[tool_name]
    return selected_tools


def _get_distractor_tools(tool_desc: Dict[str, Dict[str, Any]], used_tools: Set[str], sample_count: int = 5) -> Dict[str, Dict[str, Any]]:
    """从未使用的工具中随机采样一定数量的工具"""
    selected_tools = {}
    unused_tools = set(tool_desc.keys()) - used_tools
    sampled_tools = random.sample(unused_tools, min(sample_count, len(unused_tools)))
    for tool_name in sampled_tools:
        selected_tools[tool_name] = tool_desc[tool_name]
    return selected_tools
