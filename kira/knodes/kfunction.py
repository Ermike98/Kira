from collections.abc import Callable

from kira.core.kcontext import KContext
from kira.kdata.kdata import KData, KDataValue
from kira.core.kobject import KTypeInfo
from kira.knodes.knode import KNode, KNodeType

import inspect
from functools import wraps

class KFunction(KNode):

    def __init__(self,
                 name: str,
                 func: Callable[[list[KData], KContext], list[KDataValue]],
                 inputs: list[tuple[str, KTypeInfo] | str],
                 outputs: list[tuple[str, KTypeInfo] | str]
                 ):
        super().__init__(name, inputs, outputs)
        self._func = func

    def call(self, inputs: list[KData], context: KContext) -> list[KDataValue]:
        return self._func(inputs, context)

    # @property
    # def type(self) -> KNodeType:
    #     return KNodeType.FUNCTION


def kfunction(
        inputs: list[tuple[str, KTypeInfo] | str],
        outputs: list[tuple[str, KTypeInfo] | str],
        name: str = None,
        use_context: bool = False,
        use_values: bool = True
):
    def decorator(func: Callable):
        sig = inspect.signature(func)
        params = list(sig.parameters.values())

        # 1. Validate: No **kwargs allowed
        if any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params):
            raise TypeError(f"KFunction '{name or func.__name__}' cannot use **kwargs.")

        # 2. Check input count vs signature
        # We allow len(inputs) to be flexible if the function has *args
        has_var_args = any(p.kind == inspect.Parameter.VAR_POSITIONAL for p in params)
        min_expected = len(params) - use_context - (1 if has_var_args else 0)

        if not has_var_args and len(inputs) != min_expected:
            raise ValueError(
                f"KFunction '{func.__name__}' expects {min_expected} arguments, "
                f"but {len(inputs)} inputs were defined."
            )
        elif has_var_args and len(inputs) < min_expected:
            raise ValueError(f"KFunction '{func.__name__}' requires at least {min_expected} inputs.")

        @wraps(func)
        def wrapper(values: list[KData], context: KContext) -> list[KDataValue]:
            if use_values:
                values = [i.value for i in values]

            return func(*values, context=context) if use_context else func(*values)

        return KFunction(
            name=name or func.__name__,
            func=wrapper,
            inputs=inputs,
            outputs=outputs
        )

    return decorator
