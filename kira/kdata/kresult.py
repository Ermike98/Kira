from __future__ import annotations

from typing import Iterable

from kira.core.kobject import KObject, KTypeInfo
from kira.kdata.kdata import KData, KDataValue
from kira.kexpections.missing_result import KMissingResult


class KResultTypeInfo(KTypeInfo):
    def __init__(self, fields: dict[str, KTypeInfo] | None = None):
        self._fields = fields


    def match(self, value: KObject) -> bool:
        valid_value = (isinstance(value, KData) and
                       value and
                       isinstance(value.value, KResult)
                       )

        if self._fields is None:
            return valid_value

        res = value.value

        assert isinstance(res, KResult)

        return valid_value and all([type_info.match(res.get(key)) for key, type_info in self._fields.items()])

    def __repr__(self) -> str:
        return "KResultTypeInfo()"

class KResult(KDataValue):
    """
    Container for an operation result that can hold multiple potential objects (options).
    """

    def __init__(self, options: Iterable[KData] | KData | None = None):
        if options is not None and not isinstance(options, Iterable):
            options = [options]

        self._options: list[KData] = list(options) if options is not None else []


    def get(self, name: str) -> KData:
        for option in self._options:
            if option.name == name:
                return option

        return KData(name, None, KMissingResult(name, f"Missing result '{name}' in KResult '{self.name}'"))

    @property
    def value(self):
        return self._options

    def __bool__(self) -> bool:
        return all(self._options)

    @property
    def type(self) -> KTypeInfo:
        return KResultTypeInfo({option.name: option.type for option in self._options})
