from __future__ import annotations

from kira.core.kobject import KObject, KTypeInfo
from kira.kdata.kdata import KData
from kira.kdata.karray import KArray, KArrayTypeInfo
from kira.ktypeinfo.any_type import KAnyTypeInfo


class KVariadicTypeInfo(KTypeInfo):
    """
    Type info for variadic arguments.

    The variadic argument is received by the node as a KData wrapping a KArray
    whose elements are KDataValue objects.

    KVariadicTypeInfo takes a single KTypeInfo that is checked against every
    element in the KArray. For multi-variadic arguments (e.g. [name, values]...),
    use KCollectionTypeInfo as the element_type — the KNodeInstance will group
    arguments into KCollection objects before packing them into the KArray.

    Constructor accepts:
      - A KTypeInfo to validate each element
    """

    def __init__(self, element_type: KTypeInfo | None = None):
        self._element_type = element_type or KAnyTypeInfo()
        self._array_type = KArrayTypeInfo(self._element_type)

    @property
    def element_type(self) -> KTypeInfo:
        return self._element_type

    def match(self, value: KObject) -> bool:
        # Delegate per-element checking to KArrayTypeInfo
        return self._array_type.match(value)

    def __repr__(self) -> str:
        return f"KVariadicTypeInfo({repr(self._element_type)})"
