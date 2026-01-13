import json
import os
from typing import Dict

from . import tool_library


def read_tool_desc(tool_desc_path: str = os.path.join(os.path.dirname(__file__), "tool_desc.json")) -> Dict[str, dict]:
    with open(tool_desc_path, "r") as f:
        tool_desc = json.load(f)
    return tool_desc


def register_tools(tool_desc: Dict[str, dict]) -> Dict[str, callable]:
    tool_desc = read_tool_desc()
    tools = {}
    for tool_name, tool_info in tool_desc.items():
        tools[tool_name] = getattr(tool_library, tool_name)
    return tools
