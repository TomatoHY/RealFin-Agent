

from .base import BaseNode
from ..state import AgentState


def select_necessary_tools(state: AgentState):
    pass


def select_optional_tools(state: AgentState):
    pass


def select_tools(strategy: str, state: AgentState):
    select_func_dict = {
        "necessary": select_necessary_tools,
        "optional": select_optional_tools,
    }
    return select_func_dict[strategy](state)


class ToolSelectorNode(BaseNode):
    def __init__(
        self,
        strategy: ["necessary", ""] = "necessary",
    ):
        super().__init__("ToolSelector")
        self.strategy = strategy
        self.tools = {}

    def __call__(self, state: AgentState):
        state["tool_calls"] = select_tools(self.strategy, state)
        pass