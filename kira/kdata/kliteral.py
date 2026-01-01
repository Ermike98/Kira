import datetime
import enum

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
                value and
                isinstance(value.value, KLiteral) and
                ((self._lit_type == KLiteralType.ANY) or (self._lit_type == value.value.lit_type))
                )


K_LITERAL_TYPE = KLiteralTypeInfo(KLiteralType.ANY)
K_INTEGER_TYPE = KLiteralTypeInfo(KLiteralType.INTEGER)
K_NUMBER_TYPE = KLiteralTypeInfo(KLiteralType.NUMBER)
K_STRING_TYPE = KLiteralTypeInfo(KLiteralType.STRING)
K_BOOLEAN_TYPE = KLiteralTypeInfo(KLiteralType.BOOLEAN)
K_DATE_TYPE = KLiteralTypeInfo(KLiteralType.DATE)
K_DATETIME_TYPE = KLiteralTypeInfo(KLiteralType.DATETIME)


class KLiteral(KDataValue):
    def __init__(self, value, lit_type: KLiteralType = None):
        if lit_type is not None and not self.validate_type(value, lit_type):
            raise ValueError(
                f"Invalid value type: {lit_type} for KLiteral: {repr(value)}, suggested type: {self.infer_type(value)}")

        self._value = value
        self._type = lit_type if lit_type is not None else self.infer_type(value)

    @staticmethod
    def infer_type(value) -> KLiteralType:
        match value:
            case int():
                return KLiteralType.INTEGER
            case float():
                return KLiteralType.NUMBER
            case str():
                return KLiteralType.STRING
            case bool():
                return KLiteralType.BOOLEAN
            case datetime.date():
                return KLiteralType.DATE
            case datetime.datetime():
                return KLiteralType.DATETIME
            case _:
                return KLiteralType.ANY

    @staticmethod
    def validate_type(value, lit_type: KLiteralType):
        match value, lit_type:
            case int(), KLiteralType.INTEGER:
                return True
            case float(), KLiteralType.NUMBER:
                return True
            case str(), KLiteralType.STRING:
                return True
            case bool(), KLiteralType.BOOLEAN:
                return True
            case datetime.date(), KLiteralType.DATE:
                return True
            case datetime.datetime(), KLiteralType.DATETIME:
                return True
            case _, KLiteralType.ANY:
                return True

        return False

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
        return f"<{self.type}: {self.value}>"
