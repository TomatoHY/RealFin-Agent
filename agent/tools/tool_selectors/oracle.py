from typing import Dict

from .base import BaseToolSelector
from .utils import _get_necessary_tools


class OracleToolSelector(BaseToolSelector):
    def __init__(self) -> None:
        super().__init__("OracleToolSelector")

    def select_tools(self, user_input: str, tool_desc: Dict[str, dict], metadata: dict) -> Dict[str, dict]:
        return _get_necessary_tools(tool_desc, metadata["code"])
