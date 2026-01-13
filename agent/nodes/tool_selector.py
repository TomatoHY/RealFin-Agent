from .base import BaseNode
from ..state import AgentState
from ..tools import read_tool_desc, tool_selection_funcs


class ToolSelectorNode(BaseNode):
    def __init__(
        self,
        strategy: ["necessary", ""] = "necessary",
    ):
        super().__init__("ToolSelector")
        self.strategy = strategy
        self.tool_desc = read_tool_desc()
        self.logger.info(f"Initialized {len(self.tool_desc)} tools.")

    def run(self, state: AgentState):
        state["tool_calls"] = tool_selection_funcs[self.strategy](state)
        return state
