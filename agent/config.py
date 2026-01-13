from typing import TypedDict


class AgentConfig(TypedDict):
    model: str
    model_kwargs: dict
    max_tool_call: int
    tool_select_strategy: str

    def __init__(
        self,
        model: str,
        model_kwargs: dict,
        max_tool_call: int = 5,
        tool_filter_strategy: str = "necessary"
    ):
        self.model = model
        self.model_kwargs = model_kwargs
        self.max_tool_call = max_tool_call
        self.tool_filter_strategy = tool_filter_strategy
