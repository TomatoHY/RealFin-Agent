from typing import Any, Dict, List, TypedDict


class AgentState(TypedDict):
    messages: List[Dict[str, str]]
    tool_calls: List[Dict[str, str]]
    tool_results: List[Any]
