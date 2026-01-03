from __future__ import annotations
import enum
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kira.core.kcontext import KContext


class KObjectType(enum.Enum):
    KDATA = 1
    KNODE = 2
    KEXCEPTION = 3

class KTypeInfo(ABC):
    @abstractmethod
    def match(self, value: KObject) -> bool:
        pass

    @abstractmethod
    def __repr__(self) -> str:
        pass

    def __hash__(self):
        return hash(repr(self))

class KObject(ABC):

    def __init__(self, name: str = None):
        self.__name = name if name is not None else self.__class__.__name__

    @property
    @abstractmethod
    def type(self) -> KTypeInfo:
        pass

    @abstractmethod
    def eval(self, context: KContext) -> KObject:
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
