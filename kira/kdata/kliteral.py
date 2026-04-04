import datetime
import enum
import numpy as np

from kira.kdata.kdata import KDataValue, KData
from kira.core.kobject import KTypeInfo, KObject


class KLiteralType(enum.Enum):
    ANY = 0
    INTEGER = 1
    NUMBER = 2
    STRING = 3
    BOOLEAN = 4
    DATE = 5
    DATETIME = 6


class KLiteralTypeInfo(KTypeInfo):
    def __init__(self, lit_type: KLiteralType):
        self._lit_type = lit_type

    def match(self, value: KObject) -> bool:
        return (isinstance(value, KData) and
                bool(value) and
                isinstance(value.value, KLiteral) and
                ((self._lit_type == KLiteralType.ANY) or (self._lit_type == value.value.lit_type))
                )

    def __repr__(self) -> str:
        return f"KLiteralTypeInfo({self._lit_type.name})"


K_LITERAL_TYPE = KLiteralTypeInfo(KLiteralType.ANY)
K_INTEGER_TYPE = KLiteralTypeInfo(KLiteralType.INTEGER)
K_NUMBER_TYPE = KLiteralTypeInfo(KLiteralType.NUMBER)
K_STRING_TYPE = KLiteralTypeInfo(KLiteralType.STRING)
K_BOOLEAN_TYPE = KLiteralTypeInfo(KLiteralType.BOOLEAN)
K_DATE_TYPE = KLiteralTypeInfo(KLiteralType.DATE)
K_DATETIME_TYPE = KLiteralTypeInfo(KLiteralType.DATETIME)


class KLiteral(KDataValue):
    def __init__(self, value, lit_type: KLiteralType = None):
        inferred_type = self.infer_type(value)

        if ((lit_type is not None) and
            (lit_type != KLiteralType.ANY) and
            (lit_type != inferred_type)
            ):
            raise ValueError(
                f"Invalid value type: {lit_type} for KLiteral: {repr(value)}, suggested type: {inferred_type}")

        self._type = lit_type if lit_type is not None else inferred_type

        # Convert to numpy types to standardize
        if inferred_type == KLiteralType.BOOLEAN:
            self._value = np.bool_(value)
        elif inferred_type == KLiteralType.INTEGER:
            self._value = np.int64(value)
        elif inferred_type == KLiteralType.NUMBER:
            self._value = np.float64(value)
        elif inferred_type == KLiteralType.STRING:
            self._value = np.str_(value)
        elif inferred_type == KLiteralType.DATETIME:
            self._value = value if isinstance(value, np.datetime64) else np.datetime64(value)
        elif inferred_type == KLiteralType.DATE:
            self._value = value if isinstance(value, np.datetime64) else np.datetime64(value, 'D')
        else:
            self._value = value

    @staticmethod
    def infer_type(value) -> KLiteralType:
        if isinstance(value, (bool, np.bool_)):
            return KLiteralType.BOOLEAN
        if isinstance(value, (int, np.integer)):
            return KLiteralType.INTEGER
        if isinstance(value, (float, np.floating)):
            return KLiteralType.NUMBER
        if isinstance(value, (str, np.str_)):
            return KLiteralType.STRING
        if isinstance(value, datetime.datetime):
            return KLiteralType.DATETIME
        if isinstance(value, datetime.date):
            return KLiteralType.DATE
        if isinstance(value, np.datetime64):
            if np.datetime_data(value)[0] == 'D':
                return KLiteralType.DATE
            return KLiteralType.DATETIME
        return KLiteralType.ANY

    @property
    def value(self):
        return self._value

    @property
    def lit_type(self) -> KLiteralType:
        return self._type

    @property
    def type(self) -> KTypeInfo:
        return KLiteralTypeInfo(self._type)

    def __repr__(self):
        return f"KLiteral({repr(self._value)}, KLiteralType.{self._type.name})"
