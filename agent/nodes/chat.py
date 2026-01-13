from .base import BaseNode
from ..prompts import CHAT_PROMPT
from ..state import AgentState


class ChatNode(BaseNode):
    def __init__(self, model: str, model_kwargs: dict):
        super().__init__("Chat")
        self.model = model
        self.model_kwargs = model_kwargs

    def __call__(self, state: AgentState):
        messages = state["messages"]
        # 带重试的调用LLM API
        pass