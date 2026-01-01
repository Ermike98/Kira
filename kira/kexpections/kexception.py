from kira.core.kobject import KObject, KTypeInfo, KObjectType


class KExceptionTypeInfo(KTypeInfo):

    @property
    def object_type(self) -> KObjectType:
        return KObjectType.KEXCEPTION

    def match(self, value) -> bool:
        return isinstance(value, KException)


class KException(KObject):

    @property
    def type(self) -> KTypeInfo:
        return KExceptionTypeInfo()
