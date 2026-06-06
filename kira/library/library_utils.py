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
from kira.kdata.kerrorvalue import KErrorValue
from kira.kexpections.kgenericexception import KGenericException
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

        # Check if there are multiple pd.Series in the arguments, and if so, verify they have the same length
        series_lengths = [len(arg) for arg in unboxed_args if isinstance(arg, pd.Series)]
        if len(series_lengths) > 1 and len(set(series_lengths)) > 1:
            return [KErrorValue(KGenericException(f"Cannot perform operation on arrays of different lengths: {', '.join(map(str, series_lengths))}"))]

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
            a1 = np.asarray(x1, dtype=str) if (isinstance(x1, pd.Series) and is_x1_str) else x1
            a2 = np.asarray(x2, dtype=str) if (isinstance(x2, pd.Series) and is_x2_str) else x2
            return np_str_func(a1, a2)
        return np_num_func(x1, x2)

    return wrapper
