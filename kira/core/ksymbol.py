from __future__ import annotations

from kira.core.kcontext import KContext
from kira.core.kobject import KObject, KTypeInfo
from kira.ktypeinfo.no_type import KNoTypeInfo


class KSymbol(KObject):

    def __init__(self, name: str):
        super().__init__(name)

    def eval(self, ctx: KContext) -> KObject:
        return ctx.get_object(self.name)

    @property
    def type(self) -> KTypeInfo:
        return KNoTypeInfo()
