from typing import Dict

from .base import BaseToolSelector
from .utils import _get_necessary_tools, _get_alternative_tools, _get_distractor_tools


class OracKToolSelector(BaseToolSelector):
    def __init__(self, k: int = 5) -> None:
        super().__init__("OracKToolSelector")
        self.k = k

    def select_tools(self, user_input: str, tool_desc: Dict[str, dict], metadata: dict) -> Dict[str, dict]:
        oracle_tools = _get_necessary_tools(tool_desc, metadata["code"])
        alternative_tools = _get_alternative_tools(oracle_tools, tool_desc)
        used_tool_names = set(oracle_tools.keys()) | set(alternative_tools.keys())
        distractor_tools = _get_distractor_tools(tool_desc, used_tool_names, sample_count=self.k)
        return {**oracle_tools, **alternative_tools, **distractor_tools}
