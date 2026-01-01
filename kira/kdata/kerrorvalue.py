from kira.kdata.kdata import KDataValue
from kira.core.kobject import KTypeInfo
from kira.kexpections.kexception import KException, KExceptionTypeInfo


class KErrorValue(KDataValue):
    def __init__(self, error: KException):
        self._error = error

    @property
    def value(self):
        return self._error

    @property
    def type(self) -> KTypeInfo:
        return KExceptionTypeInfo()
