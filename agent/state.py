from typing import TypedDict, List, Dict


class AgentState(TypedDict):
    messages: List[Dict[str, str]]
    tool_calls: List[Dict[str, str]]
    tool_results: List[Dict[str, str]]
