from kira.kdata.kdata import KDataType, KDataValue, KData
from kira.core.kobject import KTypeInfo, KObject
from kira.kdata.kliteral import KLiteralType

import numpy as np
import pandas as pd
import pandas.api.types as ptypes


class KArrayTypeInfo(KTypeInfo):
    def __init__(self, lit_type: KLiteralType):
        self._lit_type = lit_type

    def match(self, value: KObject) -> bool:
        return (isinstance(value, KData) and
                bool(value) and
                isinstance(value.value, KArray) and
                ((self._lit_type == KLiteralType.ANY) or (self._lit_type == value.value.lit_type))
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
    def __init__(self, data, lit_type: KLiteralType = None):
        if not isinstance(data, pd.Series):
            data = pd.Series(data)

        inferred_type = self.infer_type(data)

        if lit_type is not None and not self.validate_type(data, lit_type):
            raise ValueError(
                f"Invalid array type: {lit_type} for KArray, suggested type: {inferred_type}")

        self._type = lit_type if lit_type is not None else inferred_type

        # Standardize the data to specific pandas extension dtypes
        if self._type == KLiteralType.BOOLEAN:
            self._data = data.astype("boolean")
        elif self._type == KLiteralType.INTEGER:
            self._data = data.astype("Int64")
        elif self._type == KLiteralType.NUMBER:
            self._data = data.astype("Float64")
        elif self._type == KLiteralType.STRING:
            self._data = data.astype("string")
        elif self._type == KLiteralType.DATETIME:
            self._data = pd.to_datetime(data)
        elif self._type == KLiteralType.DATE:
            # Pandas does not have a native "Date-only" Series type, datetimes are used.
            # We normalize to datetime, normalizing the time component.
            self._data = pd.to_datetime(data).dt.normalize()
        else:
            self._data = data

    @staticmethod
    def infer_type(data: pd.Series) -> KLiteralType:
        if ptypes.is_bool_dtype(data.dtype):
            return KLiteralType.BOOLEAN
        if ptypes.is_integer_dtype(data.dtype):
            return KLiteralType.INTEGER
        if ptypes.is_float_dtype(data.dtype) or ptypes.is_numeric_dtype(data.dtype):
            return KLiteralType.NUMBER
        if ptypes.is_string_dtype(data.dtype) or ptypes.is_object_dtype(data.dtype):
            return KLiteralType.STRING
        if ptypes.is_datetime64_any_dtype(data.dtype):
            # Distinguish DATE vs DATETIME heuristically if needed, or default to DATETIME
            # For simplicity, if all times are midnight we could call it DATE,
            # but usually type is explicit or defaults to DATETIME.
            if hasattr(data.dt, "time") and (data.dropna().dt.time == pd.Timestamp("00:00:00").time()).all() and len(data.dropna()) > 0:
                return KLiteralType.DATE
            return KLiteralType.DATETIME
        return KLiteralType.ANY

    @staticmethod
    def validate_type(data: pd.Series, lit_type: KLiteralType):
        if lit_type == KLiteralType.ANY:
            return True
        return KArray.infer_type(data) == lit_type

    @property
    def value(self) -> pd.Series:
        return self._data

    @property
    def lit_type(self) -> KLiteralType:
        return self._type

    @property
    def type(self) -> KTypeInfo:
        return KArrayTypeInfo(self._type)

    def __repr__(self):
        return f"KArray(\n{repr(self.value)}, \na \tKLiteralType.{self._type.name})"
        # return f"KArray(size={self._data.size}, KLiteralType.{self._type.name})"
