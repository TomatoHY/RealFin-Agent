import re

from langgraph.graph import StateGraph, START, END

from .config import AgentConfig
from .nodes import ChatNode, ToolSelectorNode, ToolRunnerNode
from .state import AgentState


def build_graph(config: AgentConfig):
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("tool_selector", ToolSelectorNode(strategy=config.tool_filter_strategy))
    workflow.add_node("chat", ChatNode(model=config.model, model_kwargs=config.model_kwargs))
    workflow.add_node("tool_runner", ToolRunnerNode())

    # Add edges
    workflow.add_edge(START, "tool_selector")
    workflow.add_edge("tool_selector", "chat")
    
    def decide_next_node(state: AgentState):
        if len(state.tool_results) >= config.max_tool_call:
            return END
        messages = state.messages
        if not messages:
            return "tool_runner"
        last_message_content = messages[-1].get("content", "")
        boxed_pattern = r"\\boxed\{.*?\}"
        has_boxed = re.search(boxed_pattern, last_message_content, re.DOTALL)
        if has_boxed:
            return END
        else:
            return "tool_runner"

    workflow.add_conditional_edges(
        source="chat",
        path_builder=decide_next_node,
    )

    workflow.add_edge("tool_runner", "chat")

    graph = workflow.compile()
    return graph


class RealFinAgent:
    def __init__(self, config: AgentConfig):
        self.graph = build_graph(config)

    def run(self, user_input: str):
        init_state = AgentState(
            messages=[{"role": "user", "content": user_input}],
            tool_calls=[],
            tool_results=[],
        )
        for state in self.graph.stream(init_state):
            pass
        return state
