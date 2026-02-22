from functools import wraps
from typing import Callable

import numpy as np

from kira.core.kcontext import KContext
from kira.core.kobject import KTypeInfo
from kira.kdata.karray import KArray
from kira.kdata.kdata import KData
from kira.kdata.kliteral import KLiteral
from kira.knodes.kfunction import kfunction


def numpy_to_kfunction(
        np_func: Callable,
        inputs: list[tuple[str, KTypeInfo] | str],
        outputs: list[tuple[str, KTypeInfo] | str],
        name: str = None
):
    """
    Wraps a NumPy function and ensures the output is boxed
    into KArray or KLiteral based on the return type.
    It also handles unboxing of KLiteral and KArray inputs.
    """

    @kfunction(
        inputs=inputs,
        outputs=outputs,
        name=name or np_func.__name__,
        use_values=True,
        use_context=False
    )
    def wrapper(*args):
        # args are KDataValue objects because use_values=True
        unboxed_args = [arg.value for arg in args]
        result = np_func(*unboxed_args)

        # Determine if the result should be KArray or KLiteral
        if isinstance(result, (np.ndarray, list)):
            return [KArray(np.asarray(result))]
        # Handle cases where NumPy returns a scalar (np.float64, etc.)
        return [KLiteral(result)]

    return wrapper


def k_compare_wrapper(np_num_func: Callable, np_str_func: Callable):
    """
    Wraps a numeric and a string comparison function to handle both types.
    """

    def wrapper(x1, x2):
        is_x1_str = isinstance(x1, (str, bytes)) or (isinstance(x1, np.ndarray) and x1.dtype.kind in 'SU')
        is_x2_str = isinstance(x2, (str, bytes)) or (isinstance(x2, np.ndarray) and x2.dtype.kind in 'SU')
        if is_x1_str or is_x2_str:
            return np_str_func(x1, x2)
        return np_num_func(x1, x2)

    return wrapper
