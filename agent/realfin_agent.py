import json
import re
from typing import Any, Dict

from langchain.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END

from .nodes import ChatNode, ToolSelectorNode, ToolRunnerNode
from .prompts import SYSTEM_PROMPT
from .utils import AgentConfig, AgentState, serialize_agent_state


def build_graph(config: AgentConfig):
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("tool_selector", ToolSelectorNode(strategy=config.tool_filter_strategy))
    workflow.add_node("chat", ChatNode(model=config.model, model_kwargs=config.model_kwargs))
    workflow.add_node("tool_runner", ToolRunnerNode())

    # Add edges
    workflow.add_edge(START, "tool_selector")
    workflow.add_edge("tool_selector", "chat")

    def _decide_next_node(state: AgentState):
        if state["iters"] >= config.max_iters:
            return END
        last_message_content = state["messages"][-1].content
        resp = last_message_content[last_message_content.find("</think>"):]
        box_pattern = r"\\boxed{(.*?)}"
        match = re.search(box_pattern, resp)
        if match:
            return END
        tool_use_pattern = r"<tool_use>(.*?)</tool_use>"
        match = re.search(tool_use_pattern, resp)
        if match:
            try:
                tool_call = json.loads(match.group(1))
                if not tool_call:
                    return END
            except json.JSONDecodeError:
                return "tool_runner"
        return "tool_runner"

    workflow.add_conditional_edges(
        "chat", _decide_next_node,
    )

    workflow.add_edge("tool_runner", "chat")

    graph = workflow.compile()
    return graph


class RealFinAgent:
    def __init__(self, config: AgentConfig):
        self.graph = build_graph(config)

    def run(self, user_input: str, question_metadata: Dict[str, Any] = None):
        init_state = AgentState(
            messages=[
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=user_input),
                AIMessage(content="收到，我会基于您提供的工具调用尽力回答你的问题，现在能否为我提供可能需要的工具调用？"),
            ],
            question_metadata=question_metadata or {},
            iters=0,
        )
        final_state = self.graph.invoke(init_state)
        return serialize_agent_state(final_state)
