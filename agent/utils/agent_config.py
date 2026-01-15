from pydantic import BaseModel


class AgentConfig(BaseModel):
    model: str
    model_kwargs: dict = {
        "temperature": 0.7,
        "max_tokens": 1024,
    }
    max_tool_call: int = 10
    max_iters: int = 10
    tool_filter_strategy: str = "necessary"
    tool_timeout: int = 600
