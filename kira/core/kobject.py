from __future__ import annotations
import enum
from abc import ABC, abstractmethod

class KObjectType(enum.Enum):
    KDATA = 1
    KNODE = 2
    KRESULT = 3
    KEXCEPTION = 4


class KTypeInfo(ABC):
    @abstractmethod
    def match(self, value: KObject) -> bool:
        pass

class KObject(ABC):

    def __init__(self, name: str = None):
        self.__name = name if name is not None else self.__class__.__name__

    @property
    @abstractmethod
    def type(self) -> KTypeInfo:
        pass

    @property
    def name(self):
        return self.__name

    def __hash__(self):
        return hash(self.__name)

    def __eq__(self, other):
        if not isinstance(other, KObject):
            return NotImplemented
        return self.__name == other.name