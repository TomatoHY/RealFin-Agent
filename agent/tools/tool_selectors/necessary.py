from typing import Dict
from .base import BaseToolSelector


class NecessaryToolSelector(BaseToolSelector):
    def __init__(self) -> None:
        super().__init__("NecessaryToolSelector")

    def select_tools(self, user_input: str, tool_desc: Dict[str, dict], metadata: dict) -> Dict[str, dict]:
        """get selected tool descriptions by user_input or metadata"""
        pass
