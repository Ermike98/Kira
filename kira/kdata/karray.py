from kira.kdata.kdata import KDataType, KDataValue, KData
from kira.core.kobject import KTypeInfo, KObject
from kira.kdata.kliteral import KLiteralType

import numpy as np


class KArrayTypeInfo(KTypeInfo):
    def __init__(self, lit_type: KLiteralType):
        self._lit_type = lit_type

    def match(self, value: KObject) -> bool:
        return (isinstance(value, KData) and
                value and
                isinstance(value.value, KArray) # and
                # ((self._lit_type == KLiteralType.ANY) or (self._lit_type == value.value.lit_type))
                )

    def __repr__(self) -> str:
        return f"KArrayTypeInfo({self._lit_type.name})"

K_ARRAY_TYPE = KArrayTypeInfo(KLiteralType.ANY)
K_ARRAY_INTEGER_TYPE = KArrayTypeInfo(KLiteralType.INTEGER)
K_ARRAY_NUMBER_TYPE = KArrayTypeInfo(KLiteralType.NUMBER)
K_ARRAY_STRING_TYPE = KArrayTypeInfo(KLiteralType.STRING)
K_ARRAY_BOOLEAN_TYPE = KArrayTypeInfo(KLiteralType.BOOLEAN)
K_ARRAY_DATE_TYPE = KArrayTypeInfo(KLiteralType.DATE)
K_ARRAY_DATETIME_TYPE = KArrayTypeInfo(KLiteralType.DATETIME)

class KArray(KDataValue):
    def __init__(self, data: np.ndarray):
        assert isinstance(data, np.ndarray), "Data in the KArray must be a numpy array"
        self._data = data

    @property
    def value(self):
        return self._data

    @property
    def type(self) -> KTypeInfo:
        # TODO Fix default el_type
        return KArrayTypeInfo(KLiteralType.ANY)
