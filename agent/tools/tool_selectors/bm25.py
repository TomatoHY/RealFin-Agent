from typing import Dict

from .base import BaseToolSelector
from .utils import _get_bm25_tools


class BM25ToolSelector(BaseToolSelector):
    def __init__(self, top_k: int = 20) -> None:
        super().__init__("BM25ToolSelector")
        self.top_k = top_k

    def select_tools(self, user_input: str, tool_desc: Dict[str, dict], metadata: dict) -> Dict[str, dict]:
        return _get_bm25_tools(user_input, tool_desc, self.top_k)
