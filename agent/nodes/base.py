from abc import ABC, abstractmethod


class BaseNode(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def __call__(self, state):
        raise NotImplementedError
