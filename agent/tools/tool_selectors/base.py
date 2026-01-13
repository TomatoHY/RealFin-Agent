from abc import ABC, abstractmethod
import logging
from typing import Dict


class BaseToolSelector(ABC):
    def __init__(self, name: str) -> None:
        super().__init__()
        self.name = name
        self.logger = logging.getLogger(name)

    @abstractmethod
    def select_tools(self, user_input: str, tool_desc: Dict[str, dict], metadata: dict) -> Dict[str, dict]:
        """get selected tool descriptions by user_input or metadata"""
        pass

    def __call__(self, user_input: str, tool_desc: Dict[str, dict], metadata: dict) -> Dict[str, dict]:
        selected_tool_desc = self.select_tools(user_input, tool_desc, metadata)
        original_tool_count = len(tool_desc)
        selected_tool_count = len(selected_tool_desc)
        self.logger.info(f"selected {selected_tool_count} tools out of {original_tool_count}: {selected_tool_desc.keys()}")
        return selected_tool_desc
