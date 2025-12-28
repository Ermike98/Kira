from kira.kdata.kdata import KDataType, KTypeInfo, KDataValue
from kira.kdata.kliteral import KLiteralType

import numpy as np

K_ARRAY_TYPE = KTypeInfo(KDataType.TABLE, {"el_type": KLiteralType.ANY})
K_ARRAY_INTEGER_TYPE = KTypeInfo(KDataType.TABLE, {"el_type": KLiteralType.INTEGER})
K_ARRAY_NUMBER_TYPE = KTypeInfo(KDataType.TABLE, {"el_type": KLiteralType.NUMBER})
K_ARRAY_STRING_TYPE = KTypeInfo(KDataType.TABLE, {"el_type": KLiteralType.STRING})
K_ARRAY_BOOLEAN_TYPE = KTypeInfo(KDataType.TABLE, {"el_type": KLiteralType.BOOLEAN})
K_ARRAY_DATE_TYPE = KTypeInfo(KDataType.TABLE, {"el_type": KLiteralType.DATE})
K_ARRAY_DATETIME_TYPE = KTypeInfo(KDataType.TABLE, {"el_type": KLiteralType.DATETIME})

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
        return KTypeInfo(KDataType.ARRAY, {"el_type": KLiteralType.ANY})
