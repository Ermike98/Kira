from kira.kdata.kdata import KDataType, KTypeInfo, KDataValue
from kira.kdata.kliteral import KLiteral
from kira.kdata.ktable import KTable


def validate_type(value: KDataValue, type_info: KTypeInfo) -> bool:
    match value, type_info.type:
        case KLiteral(), KDataType.LITERAL:
            return value.lit_type == type_info.metadata["lit_type"]
        case KTable(), KDataType.TABLE:
            return True
        case _, KDataType.ANY:
            return True

    return False
