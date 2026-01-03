from kira.core.kobject import KTypeInfo


class KAnyTypeInfo(KTypeInfo):
    def match(self, value) -> bool:
        return True

    def __repr__(self) -> str:
        return "KAnyTypeInfo()"