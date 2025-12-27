from collections.abc import Callable

from kira.kdata.kdata import KData, KTypeInfo, KDataValue
from kira.knodes.knode import KNode, KNodeType

import inspect
from functools import wraps

class KFunction(KNode):

    def __init__(self,
                 name: str,
                 func: Callable[[list[KDataValue]], list[KDataValue]],
                 inputs: list[tuple[str, KTypeInfo] | str],
                 outputs: list[tuple[str, KTypeInfo] | str]
                 ):
        super().__init__(name, inputs, outputs)
        self._func = func

    def call(self, inputs: list[KData]) -> list[KDataValue]:
        input_vals = [i.value for i in inputs]
        return self._func(input_vals)

    @property
    def type(self) -> KNodeType:
        return KNodeType.FUNCTION


def kfunction(
        inputs: list[tuple[str, KTypeInfo] | str],
        outputs: list[tuple[str, KTypeInfo] | str],
        name: str = None
):
    def decorator(func: Callable):
        # 1. Validate the function signature for variadic arguments
        sig = inspect.signature(func)
        for param in sig.parameters.values():
            if param.kind == inspect.Parameter.VAR_POSITIONAL or param.kind ==  inspect.Parameter.VAR_KEYWORD:
                raise TypeError(
                    f"KFunction '{name or func.__name__}' cannot use variadic arguments (*args, **kwargs)."
                )

        # 2. Check that the number of inputs matches the function signature
        # This prevents runtime errors when unpacking
        if len(inputs) != len(sig.parameters):
            raise ValueError(
                f"KFunction '{func.__name__}' expects {len(sig.parameters)} arguments, "
                f"but {len(inputs)} inputs were defined in the decorator."
            )

        # 3. Create the wrapper to unpack the list into individual arguments
        @wraps(func)
        def wrapper(values: list[KDataValue]) -> list[KDataValue]:
            return func(*values)

        # 4. Return the KFunction instance
        return KFunction(
            name=name or func.__name__,
            func=wrapper,
            inputs=inputs,
            outputs=outputs
        )

    return decorator