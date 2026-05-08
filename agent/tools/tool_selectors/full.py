from typing import Dict
from .base import BaseToolSelector


class AllToolSelector(BaseToolSelector):
    def __init__(self) -> None:
        super().__init__("AllToolSelector")

    def select_tools(self, user_input: str, tool_desc: Dict[str, dict], metadata: dict) -> Dict[str, dict]:
        return tool_desc