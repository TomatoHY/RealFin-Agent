from langchain_core.messages import AIMessage

from .base import BaseNode
from ..models import create_chat_model
from ..utils import AgentState


class ChatNode(BaseNode):
    def __init__(self, model: str, model_kwargs: dict, location: str = "realfin"):
        super().__init__("Chat")
        self.llm = create_chat_model(model, location=location, **model_kwargs)

    def run(self, state: AgentState):
        response: AIMessage = self.llm.invoke(state["messages"])
        state_update = {
            "messages": [response],
        }
        return state_update
