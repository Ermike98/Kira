from abc import ABC, abstractmethod


class KObject(ABC):

    @abstractmethod
    def __init__(self, name: str = None):
        self.__name = name if name is not None else self.__class__.__name__

    @property
    def name(self):
        return self.__name