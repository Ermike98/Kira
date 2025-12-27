from kira.kdata.kdata import KDataValue, KTypeInfo, KDataType
from kira.kexpections.kexception import KException


class KErrorValue(KDataValue):
    def __init__(self, error: KException):
        self._error = error

    @property
    def value(self):
        return self._error

    @property
    def type(self) -> KTypeInfo:
        return KTypeInfo(KDataType.ERROR)
