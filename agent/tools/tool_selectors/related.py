from typing import Dict

from .base import BaseToolSelector
from .utils import _get_related_tools


class RelatedToolSelector(BaseToolSelector):
    def __init__(self) -> None:
        super().__init__("RelatedToolSelector")
        self.necessary_tool_selector = NecessaryToolSelector()

    def select_tools(self, user_input: str, tool_desc: Dict[str, dict], metadata: dict) -> Dict[str, dict]:
        return _get_related_tools(tool_desc, metadata["code"])
