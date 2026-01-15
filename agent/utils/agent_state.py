import json
import operator
from typing import Annotated, Any, Dict, List, TypedDict, Union

from langchain.messages import AIMessage, HumanMessage
from langchain_core.messages import messages_to_dict


class AgentState(TypedDict):
    messages: Annotated[List[Union[HumanMessage, AIMessage]], operator.add]  # 对话记录
    question_metadata: Dict[str, Any]  # 测试数据的元数据，包含参考代码等信息
    iters: int  # 迭代次数


def serialize_agent_state(state: AgentState) -> str:
    serializable_state = {
        "messages": messages_to_dict(state["messages"]),
        "question_metadata": state["question_metadata"],
        "iters": state["iters"]
    }
    return serializable_state
