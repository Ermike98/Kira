from kira.kdata.kdata import KData, KDataValue
from kira.core.kobject import KTypeInfo, KObject

import pandas as pd


class KTableTypeInfo(KTypeInfo):

    def match(self, value: KObject) -> bool:
        return (isinstance(value, KData) and
                value and
                isinstance(value.value, KTable)
                )

K_TABLE_TYPE = KTableTypeInfo()

class KTable(KDataValue):
    def __init__(self, data: pd.DataFrame):
        assert isinstance(data, pd.DataFrame), "Data in the KTable must be a pandas DataFrame"
        self._data = data

    @property
    def value(self):
        return self._data

    @property
    def type(self) -> KTypeInfo:
        return KTableTypeInfo()
