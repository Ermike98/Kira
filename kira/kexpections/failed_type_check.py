from typing import Iterable

from kira.kdata.kdata import KData, KTypeInfo
from kira.kexpections.kexception import KException


class KFailedTypeChecks(KException):
    def __init__(self, failed_checks: Iterable[tuple[KData, KTypeInfo]]):
        self._failed_checks = failed_checks