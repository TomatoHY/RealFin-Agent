import json

from .base import BaseNode
from ..state import AgentState
from tools import tool_library


def init_tools(tool_desc):
    tool_funcs = {}
    for tool_name, tool_info in tool_desc.items():
        tool_funcs[tool_name] = getattr(tool_library, tool_name)
    return tool_funcs


class ToolRunnerNode(BaseNode):
    def __init__(
        self,
        tool_desc_json_path: str=""
    ):
        super().__init__(name="ToolRunner")
        with open(tool_desc_json_path, "r") as f:
            self.tool_desc = json.load(f)
        self.tool_funcs = init_tools(self.tool_desc)

    def __call__(self, state: AgentState):
        tool_calls = state["tool_calls"]
        tool_results = []
        for tool_call in tool_calls:
            tool_name = tool_call["name"]
            tool_args = json.loads(tool_call["arguments"])
            tool_result = self.tool_funcs[tool_name](**tool_args)
            tool_results.append(tool_result)
        state["tool_results"] = tool_results
        pass
