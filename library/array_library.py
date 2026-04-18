import numpy as np

from kira.kdata.karray import (K_ARRAY_INTEGER_TYPE, K_ARRAY_NUMBER_TYPE, K_ARRAY_BOOLEAN_TYPE, K_ARRAY_STRING_TYPE,
    KArray, KArrayTypeInfo, K_ARRAY_TYPE)
from kira.kdata.kliteral import (K_BOOLEAN_TYPE, K_INTEGER_TYPE, K_NUMBER_TYPE, K_STRING_TYPE, K_LITERAL_TYPE, KLiteral,
                                 KLiteralType)
from kira.knodes.kfunction import KFunction, kfunction
from kira.library.node_library import KLibrary

import pandas as pd

k_array_library = KLibrary("Array")

# Array Functions

# len(x: array) -> int
@kfunction(
    inputs=[("x", K_ARRAY_TYPE)],
    outputs=[("n", K_INTEGER_TYPE)],
    name="len",
    use_values=True,
    use_context=False
)
def k_array_len(x_obj):
    x = x_obj.value
    return [KLiteral(len(x), K_INTEGER_TYPE)]

k_array_library.register(k_array_len)

# range(start, stop, step=1) -> array
@kfunction(
    inputs=[("start", K_LITERAL_TYPE), ("stop", K_LITERAL_TYPE), ("step", K_LITERAL_TYPE)],
    outputs=[("y", K_ARRAY_TYPE)],
    name="range",
    use_values=True,
    use_context=False,
    default_inputs={"step": KLiteral(1, KLiteralType.INTEGER)}
)
def k_array_range(start_: KLiteral, stop_: KLiteral, step_: KLiteral):
    return [KArray(pd.Series(np.arange(start_.value, stop_.value, step_.value)))]

k_array_library.register(k_array_range)

# sort(x: array, ascending=True) -> array
@kfunction(
    inputs=[("x", K_ARRAY_TYPE), ("ascending", K_BOOLEAN_TYPE)],
    outputs=[("y", K_ARRAY_TYPE)],
    name="sort",
    use_values=True,
    use_context=False,
    default_inputs={"ascending": KLiteral(True, KLiteralType.BOOLEAN)}
)
def k_array_sort(x_obj: KArray, ascending_: KLiteral):
    return [KArray(x_obj.value.sort_value(ascending=ascending_.value), x_obj.lit_type)]

k_array_library.register(k_array_sort)

# argsort(x: array, ascending=True) -> array
@kfunction(
    inputs=[("x", K_ARRAY_TYPE), ("ascending", K_BOOLEAN_TYPE)],
    outputs=[("y", K_ARRAY_TYPE)],
    name="sort_index",
    use_values=True,
    use_context=False,
    default_inputs={"ascending": KLiteral(True, KLiteralType.BOOLEAN)}
)
def k_array_sort_index(x_obj: KArray, ascending_: KLiteral):
    idx = x_obj.value.argsort()
    if ascending_.value:
        return [KArray(idx, K_ARRAY_INTEGER_TYPE)]

    return [KArray(len(x_obj.value) - 1 - idx, K_ARRAY_INTEGER_TYPE)]

k_array_library.register(k_array_sort_index)

# reverse(x: array) -> array
@kfunction(
    inputs=[("x", K_ARRAY_TYPE)],
    outputs=[("y", K_ARRAY_TYPE)],
    name="reverse",
    use_values=True,
    use_context=False
)
def k_array_reverse(x_obj: KArray):
    return [KArray(x_obj.value.iloc[::-1].reset_index(drop=True), x_obj.lit_type)]

k_array_library.register(k_array_reverse)

# unique(x: array) -> array
@kfunction(
    inputs=[("x", K_ARRAY_TYPE)],
    outputs=[("y", K_ARRAY_TYPE)],
    name="unique",
    use_values=True,
    use_context=False
)
def k_array_unique(x_obj: KArray):
    return [KArray(pd.Series(x_obj.value.unique()), x_obj.lit_type)]

k_array_library.register(k_array_unique)