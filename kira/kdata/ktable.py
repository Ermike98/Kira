from kira.kdata.kdata import KData, KDataType, KTypeInfo, KDataValue

import pandas as pd


class KTable(KDataValue):
    def __init__(self, data: pd.DataFrame):
        assert isinstance(data, pd.DataFrame), "Data in the KTable must be a pandas DataFrame"
        self._data = data

    @property
    def value(self):
        return self._data

    @property
    def type(self) -> KTypeInfo:
        return KTypeInfo(KDataType.TABLE)
