from kira.kdata.kdata import KDataType, KDataValue, KData
from kira.core.kobject import KTypeInfo, KObject
from kira.kdata.kliteral import KLiteralType, KLiteralTypeInfo
from kira.kdata.kcollection import KCollection
from kira.kdata.kerrorvalue import KErrorValue
from kira.ktypeinfo.any_type import KAnyTypeInfo

import numpy as np
import pandas as pd
import pandas.api.types as ptypes


class KArrayTypeInfo(KTypeInfo):
    def __init__(self, element_type: KTypeInfo):
        self._element_type = element_type

    @property
    def element_type(self) -> KTypeInfo:
        return self._element_type

    def match(self, value: KObject) -> bool:
        if not (isinstance(value, KData) and bool(value) and isinstance(value.value, KArray)):
            return False

        arr = value.value

        if isinstance(self._element_type, KAnyTypeInfo):
            return True

        if isinstance(self._element_type, KLiteralTypeInfo):
            return self._element_type._lit_type == KLiteralType.ANY or self._element_type._lit_type == arr.lit_type

        # Generic element type check (e.g. KCollectionTypeInfo): validate every element
        for i, el in enumerate(arr.value):
            wrapped = KData(f"_el_{i}", el) if not isinstance(el, KData) else el
            if not self._element_type.match(wrapped):
                return False
        return True

    def __repr__(self) -> str:
        return f"KArrayTypeInfo({self._element_type!r})"

K_ARRAY_TYPE = KArrayTypeInfo(KAnyTypeInfo())
K_ARRAY_INTEGER_TYPE = KArrayTypeInfo(KLiteralTypeInfo(KLiteralType.INTEGER))
K_ARRAY_NUMBER_TYPE = KArrayTypeInfo(KLiteralTypeInfo(KLiteralType.NUMBER))
K_ARRAY_STRING_TYPE = KArrayTypeInfo(KLiteralTypeInfo(KLiteralType.STRING))
K_ARRAY_BOOLEAN_TYPE = KArrayTypeInfo(KLiteralTypeInfo(KLiteralType.BOOLEAN))
K_ARRAY_DATE_TYPE = KArrayTypeInfo(KLiteralTypeInfo(KLiteralType.DATE))
K_ARRAY_DATETIME_TYPE = KArrayTypeInfo(KLiteralTypeInfo(KLiteralType.DATETIME))

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
        if ptypes.is_datetime64_any_dtype(data.dtype):
            # Distinguish DATE vs DATETIME heuristically if needed, or default to DATETIME
            # For simplicity, if all times are midnight we could call it DATE,
            # but usually type is explicit or defaults to DATETIME.
            if hasattr(data.dt, "time") and (data.dropna().dt.time == pd.Timestamp("00:00:00").time()).all() and len(data.dropna()) > 0:
                return KLiteralType.DATE
            return KLiteralType.DATETIME
        if ptypes.is_object_dtype(data.dtype):
            # Check if elements are KDataValue objects (e.g. KCollection, KErrorValue)
            if len(data) > 0:
                if isinstance(data.iloc[0], KErrorValue):
                    return KLiteralType.ERROR
                if isinstance(data.iloc[0], KCollection):
                    return KLiteralType.COLLECTION
            return KLiteralType.STRING
        if ptypes.is_string_dtype(data.dtype):
            return KLiteralType.STRING
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
