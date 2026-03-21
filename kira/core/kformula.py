from __future__ import annotations

from kira.core.kcontext import KContext
from kira.core.kobject import KObject, KTypeInfo


class KFormula(KObject):
    """
    KFormula wraps an unevaluated expression.
    When a formula is evaluated during node input resolution, it immediately 
    evaluates its inner expression using the provided context.
    
    This allows pipelines to pass deferred logic where 
    dependencies are resolved locally.
    """
    def __init__(self, name: str, inner: KObject):
        super().__init__(name)
        self._inner_object = inner

    @property
    def type(self) -> KTypeInfo:
        return self._inner_object.type

    def eval(self, context: KContext) -> KObject:
        return self._inner_object.eval(context)
