#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RealFin Tool Descriptor Package.

This package contains 85 individual tool implementations, each in its own folder.
Each tool folder contains:
- code.py: Tool implementation
- tool_desc.json: Tool metadata and description

The utils module contains shared helper functions used across tools.
"""

import importlib
import json
from pathlib import Path
from typing import Dict, List
 
from . import utils
 
_TOOL_LIB_DIR = Path(__file__).parent
 
 
def read_tool_desc() -> Dict[str, dict]:
    """从tool_library目录加载所有工具的描述schema"""
    tool_desc = {}
    for tool_desc_file in _TOOL_LIB_DIR.glob("*/tool_desc.json"):
        schema = json.load(open(tool_desc_file, encoding='utf-8'))
        tool_name = schema.get("tool_name", tool_desc_file.parent.name)
        tool_desc[tool_name] = schema
    return tool_desc
 
 
def register_tools(tool_names: List[str]) -> Dict[str, callable]:
    """按需懒加载工具执行函数"""
    tools = {}
    for tool_name in tool_names:
        try:
            module = importlib.import_module(f".{tool_name}.code", package=__package__)
            if hasattr(module, tool_name):
                tools[tool_name] = getattr(module, tool_name)
        except ModuleNotFoundError:
            pass
    return tools

__all__ = ['utils', 'read_tool_desc', 'register_tools']
