from abc import ABC, abstractmethod
import logging

from ..state import AgentState


class BaseNode(ABC):
    def __init__(self, name: str):
        super().__init__()
        self.name = name
        self.logger = logging.getLogger(f"AgentNode({name})")

    @abstractmethod
    def run(self, state: AgentState) -> AgentState:
        pass

    def __call__(self, state: AgentState) -> AgentState:
        self.logger.debug("Start")
        try:
            state_update = self.run(state)
        except Exception as e:
            self.logger.error(f"{e.__class__.__name__}: {str(e)}")
            raise e
        self.logger.debug("End")
        return state_update
