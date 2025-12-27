from __future__ import annotations

from typing import Iterable

from kira.core.kobject import KObject, KObjectType
from kira.kdata.kdata import KData
from kira.kexpections.missing_result import KMissingResult


class KResult(KObject):
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
    def results(self) -> list[KData]:
        return self._options

    def __bool__(self) -> bool:
        return all(self._options)


    @property
    def object_type(self) -> KObjectType:
        return KObjectType.KRESULT
