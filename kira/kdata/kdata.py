from abc import abstractmethod, ABC
from typing import NamedTuple, Any

from kira.core.kobject import KObject, KObjectType

import enum

from kira.kexpections.kexception import KException


class KDataType(enum.Enum):
    ANY = 0
    TABLE = 1
    LITERAL = 2
    ARRAY = 3
    ERROR = 4


class KTypeInfo(NamedTuple):
    type: KDataType
    metadata: dict[str, Any] = None


class KDataValue(ABC):

    @property
    @abstractmethod
    def value(self):
        pass

    @property
    @abstractmethod
    def type(self) -> KTypeInfo:
        pass


class KData(KObject):
    """
        Container for a single optional result value:

        - value != None, error is None -> success
        - value is None, error != None -> error
        - value != None, error != None -> success with warning (error treated as warning)
    """

    def __init__(self, name: str, value: KDataValue | None, error: KException = None):
        super().__init__(name=name)

        assert value is not None or error is not None, "Either a value or an error must be provided!"

        self._value = value
        self._error = error

    @property
    def value(self):
        return self._value

    @property
    def error(self):
        return self._error

    @property
    def type(self) -> KTypeInfo:
        return self._value.type if self._value is not None else KTypeInfo(KDataType.ERROR)

    @property
    def object_type(self) -> KObjectType:
        return KObjectType.KDATA

    def __repr__(self):
        return f"{self.name}[{self.type.type}]: {self.value}"

    def __bool__(self) -> bool:
        return self.value is not None