from __future__ import annotations

from typing import List

from kira.core.kcontext import KContext
from kira.core.kobject import KObject, KTypeInfo
from kira.ktypeinfo.no_type import KNoTypeInfo


class KProgram(KObject):

    def __init__(self, statements: List[KObject]):
        super().__init__("Program")
        self._statements = statements

    def eval(self, ctx: KContext) -> KObject:
        last_result = None
        for stmt in self._statements:
            last_result = stmt.eval(ctx)
        return last_result

    @property
    def type(self) -> KTypeInfo:
        return KNoTypeInfo()
