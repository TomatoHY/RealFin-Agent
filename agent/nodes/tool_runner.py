import json
import re
from typing import Callable, Dict, List

from langchain_core.messages import HumanMessage

from .base import BaseNode
from ..prompts import TOOL_RESULTS_PROMPT
from ..tools import register_tools
from ..utils import AgentState


class ToolRunnerNode(BaseNode):
    def __init__(self):
        super().__init__(name="ToolRunner")
        self.tool_funcs: Dict[str, Callable] = {}

    def _register_tools(self, tool_names: List[str]):
        unregistered_tools = []
        for tool_name in tool_names:
            if tool_name not in self.tool_funcs:
                unregistered_tools.append(tool_name)
        self.tool_funcs.update(register_tools(unregistered_tools))

    def _extract_tool_calls(self, resp: str):
        pattern = r"<tool_use>\s*(.*?)\s*</tool_use>"
        match = re.search(pattern, resp, re.DOTALL)
        if not match:
            return None
        content = match.group(1).strip()
        try:
            data = json.loads(content)
            if isinstance(data, list):
                return data
            else:
                return [data]
        except json.JSONDecodeError:
            self.logger.warning(f"Failed to parse tool call JSON: {content}")
            return None

    def run(self, state: AgentState):
        tool_calls = self._extract_tool_calls(state["messages"][-1].content)
        tool_results = {}
        if tool_calls is None:
            tool_results = {"Error": "Invalid tool call format."}
        else:
            self._register_tools([tool_call.get("function") or tool_call.get("name") for tool_call in tool_calls])
            for tool_call in tool_calls:
                tool_name = tool_call.get("function") or tool_call.get("name")
                if "arguments" not in tool_call:
                    self.logger.warning(f"Tool call missing 'arguments' key: {tool_call}")
                    tool_results[str(tool_name)] = "Error: malformed tool call, 'arguments' key missing."
                    continue
                tool_args = tool_call["arguments"]
                if tool_name not in self.tool_funcs:
                    tool_results[tool_name] = f"Error: tool `{tool_name}` not found."
                    continue
                try:
                    tool_result = self.tool_funcs[tool_name](**tool_args)
                except Exception as e:
                    tool_result = f"{type(e).__name__}: {str(e)}"
                def _fmt(k, v):
                    return f"{k}='{v}'" if isinstance(v, str) else f"{k}={v}"
                function_call_str = f"{tool_name}({', '.join(_fmt(k, v) for k, v in tool_args.items())})"
                self.logger.debug(f"Tool call: {function_call_str} = {tool_result}")
                tool_results[function_call_str] = str(tool_result)

        content = TOOL_RESULTS_PROMPT.format(tool_results_json=json.dumps(tool_results, ensure_ascii=False))
        state_update = {
            "messages": [HumanMessage(content=content)],
            "iters": state["iters"] + 1,
        }
        return state_update
