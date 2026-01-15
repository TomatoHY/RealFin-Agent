import json
import logging
import os
from importlib import import_module
from pkgutil import iter_modules
from typing import Any, Callable, Dict, List


def read_tool_desc() -> Dict[str, Dict[str, Any]]:
    """读取所有工具的描述"""
    package_path = os.path.dirname(__file__)
    tool_desc = {}
    for _, module_name, is_pkg in iter_modules([package_path]):
        if is_pkg:
            json_path = os.path.join(package_path, module_name, "tool_desc.json")
            if os.path.exists(json_path):
                try:
                    with open(json_path, "r", encoding="utf-8") as f:
                        tool_desc[module_name] = json.load(f)
                except (json.JSONDecodeError, OSError) as e:
                    logging.error(f"Could not read tool description for {module_name}: {type(e).__name}-{str(e)}.")
    return tool_desc


def register_tools(tool_names: List[str]) -> Dict[str, Callable]:
    """注册所有工具，得到 {tool_name: tool_func}"""
    tools = {}
    tool_names = set(tool_names)
    package_path = os.path.dirname(__file__)
    for loader, module_name, is_pkg in iter_modules([package_path]):
        if is_pkg and module_name in tool_names:
            full_module_name = f"{__name__}.{module_name}"
            try:
                module = import_module(full_module_name)
                func = getattr(module, module_name, None)
                if func:
                    tools[module_name] = func
                else:
                    raise NotImplementedError
            except Exception as e:
                logging.error(f"Could not import tool {module_name}: {type(e).__name}-{str(e)}.")
    return tools
