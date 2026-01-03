from __future__ import annotations

from kira.core.kobject import KTypeInfo, KObject


class KNoTypeInfo(KTypeInfo):

    def match(self, value: KObject) -> bool:
        return False

    def __repr__(self) -> str:
        return "KNoTypeInfo()"
