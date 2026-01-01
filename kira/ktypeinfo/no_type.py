from kira.core.kobject import KTypeInfo


class KNoTypeInfo(KTypeInfo):
    def match(self, value) -> bool:
        return True