from typing import TypedDict


class AgentConfig(TypedDict):
    model: str
    model_kwargs: dict
    max_tool_call: int = 5
    tool_filter_strategy: str = "necessary"
