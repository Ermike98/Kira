from kira.core.kobject import KTypeInfo


class KUnionTypeInfo(KTypeInfo):
    def __init__(self, types: list[KTypeInfo]):
        self._types = types

    def match(self, value) -> bool:
        for t in self._types:
            if t.match(value):
                return True

        return False

    def __repr__(self) -> str:
        return f"KUnionTypeInfo({repr(self._types)})"