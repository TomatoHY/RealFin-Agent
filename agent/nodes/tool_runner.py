import json

from .base import BaseNode
from ..state import AgentState
from tools import register_tools


class ToolRunnerNode(BaseNode):
    def __init__(
        self
    ):
        super().__init__(name="ToolRunner")
        self.tool_funcs = register_tools()

    def run(self, state: AgentState):
        tool_calls = state["tool_calls"]
        tool_results = []
        for tool_call in tool_calls:
            tool_name = tool_call["name"]
            tool_args = json.loads(tool_call["arguments"])
            tool_result = self.tool_funcs[tool_name](**tool_args)
            tool_results.append(tool_result)
        state["tool_results"] = tool_results
        pass
