import json

from langchain_core.messages import HumanMessage

from .base import BaseNode
from ..prompts import TOOL_PROMPT
from ..tools import read_tool_desc, tool_selection_funcs
from ..utils import AgentState


class ToolSelectorNode(BaseNode):
    def __init__(
        self,
        strategy: ["necessary", "bm25", "base"] = "necessary",
    ):
        super().__init__("ToolSelector")
        self.strategy = strategy
        self.tool_desc = read_tool_desc()
        self.logger.info(f"Initialized {len(self.tool_desc)} tools.")

    def run(self, state: AgentState):
        messages = state["messages"]
        user_input = ""
        for message in messages:
            if isinstance(message, HumanMessage):
                user_input = message.content
                break
        selected_tools = tool_selection_funcs[self.strategy](user_input, self.tool_desc, state["question_metadata"])
        formatted_tool_desc = self._format_tool_desc(selected_tools)
        formatted_tool_json = json.dumps(formatted_tool_desc, ensure_ascii=False)
        state_update = {
            "messages": [HumanMessage(content=TOOL_PROMPT.format(tools_json=formatted_tool_json))],
        }
        return state_update

    def _format_tool_desc(self, tool_desc: dict):
        formatted_tool_desc = []
        for tool_name, tool_info in tool_desc.items():
            formatted_tool_desc.append({
                "function": tool_name,
                "description": tool_info.get("description", ""),
                "arguments": tool_info.get("input_semantics", []),
            })
        return formatted_tool_desc

