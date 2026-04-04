from functools import wraps
from typing import Callable

import numpy as np
import pandas as pd
import pandas.api.types as ptypes

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
        # We avoid explicit np.ndarray check where possible, but we need to know if it's an array.
        if isinstance(result, (pd.Series, list)) or (isinstance(result, np.ndarray) and result.ndim > 0):
            return [KArray(result)]
        
        # Handle cases where NumPy returns a scalar (np.float64, etc.) or 0-d array
        if isinstance(result, np.ndarray) and result.ndim == 0:
            result = result[()]
        return [KLiteral(result)]

    return wrapper


def k_compare_wrapper(np_num_func: Callable, np_str_func: Callable):
    """
    Wraps a numeric and a string comparison function to handle both types.
    """

    def wrapper(x1, x2):
        is_x1_str = isinstance(x1, (str, bytes, np.str_)) or (isinstance(x1, pd.Series) and ptypes.is_string_dtype(x1.dtype))
        is_x2_str = isinstance(x2, (str, bytes, np.str_)) or (isinstance(x2, pd.Series) and ptypes.is_string_dtype(x2.dtype))
        if is_x1_str or is_x2_str:
            return np_str_func(x1, x2)
        return np_num_func(x1, x2)

    return wrapper
