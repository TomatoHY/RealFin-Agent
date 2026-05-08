import random
import re
from typing import Any, Dict, List, Set

from rank_bm25 import BM25Okapi


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


def _get_alternative_tools(necessary_tools: Dict[str, Dict[str, Any]], tool_desc: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """获取可替代工具"""
    selected_tools = {}
    alternative_tools = set()
    for tool_name, tool_info in necessary_tools.items():
        for alternative_tool_name in tool_info["tool_alternative"]:
            alternative_tools.add(alternative_tool_name)
    for tool_name in alternative_tools:
        selected_tools[tool_name] = tool_desc[tool_name]
    return selected_tools


def _get_bm25_tools(query: str, tool_desc: Dict[str, Dict[str, Any]], top_k: int = 20) -> Dict[str, Dict[str, Any]]:
    """用BM25算法计算工具与query的相似度，返回排名前top_k的工具"""
    tool_names: List[str] = list(tool_desc.keys())
    def _tool_corpus(schema: dict) -> List[str]:
        text = " ".join(filter(None, [
            schema.get("tool_name", ""),
            schema.get("description", ""),
        ]))
        return text.split()
    corpus = [_tool_corpus(tool_desc[name]) for name in tool_names]
    bm25 = BM25Okapi(corpus)
    scores = bm25.get_scores(query.split())
    ranked = sorted(zip(tool_names, scores), key=lambda x: x[1], reverse=True)
    return {name: tool_desc[name] for name, _ in ranked[:top_k]}


def _get_distractor_tools(tool_desc: Dict[str, Dict[str, Any]], used_tools: Set[str], sample_count: int = 5) -> Dict[str, Dict[str, Any]]:
    """从未使用的工具中随机采样一定数量的工具"""
    selected_tools = {}
    unused_tools = set(tool_desc.keys()) - used_tools
    sampled_tools = random.sample(unused_tools, min(sample_count, len(unused_tools)))
    for tool_name in sampled_tools:
        selected_tools[tool_name] = tool_desc[tool_name]
    return selected_tools
