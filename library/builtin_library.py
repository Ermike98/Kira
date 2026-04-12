from functools import wraps
from typing import Callable

import numpy as np
import pandas as pd
import pandas.api.types as ptypes

from kira.core.kcontext import KContext
from kira.core.kobject import KTypeInfo
from kira.kdata.karray import K_ARRAY_INTEGER_TYPE, K_ARRAY_NUMBER_TYPE, K_ARRAY_BOOLEAN_TYPE, K_ARRAY_STRING_TYPE, \
    KArray, KArrayTypeInfo, K_ARRAY_TYPE
from kira.kdata.kdata import KData, KDataValue
from kira.kdata.kliteral import K_BOOLEAN_TYPE, K_INTEGER_TYPE, K_NUMBER_TYPE, K_STRING_TYPE, KLiteral, KLiteralType
from kira.kdata.kerrorvalue import KErrorValue
from kira.kdata.ktable import KTable, KTableTypeInfo
from kira.kexpections.kgenericexception import KGenericException
from kira.knodes.kfunction import KFunction, kfunction
from kira.ktypeinfo.any_type import KAnyTypeInfo
from kira.ktypeinfo.union_type import KUnionTypeInfo
from kira.library.node_library import KLibrary

# Create a library of basic math functions wrapping Numpy functions

K_NP_MATH_TYPE = KUnionTypeInfo([
    K_INTEGER_TYPE, K_NUMBER_TYPE, K_BOOLEAN_TYPE,
    K_ARRAY_INTEGER_TYPE, K_ARRAY_NUMBER_TYPE, K_ARRAY_BOOLEAN_TYPE
])

K_ADD_TYPE = KUnionTypeInfo([
    K_NP_MATH_TYPE, K_STRING_TYPE, K_ARRAY_STRING_TYPE
])

K_MULT_TYPE = KUnionTypeInfo([
    K_NP_MATH_TYPE, K_STRING_TYPE, K_ARRAY_STRING_TYPE
])

k_builtin_library = KLibrary("Builtin")


from kira.library.library_utils import numpy_to_kfunction, k_compare_wrapper


# Arithmetic Functions

# Addition 

def _k_add_impl(val1_obj, val2_obj):
    val1 = val1_obj.value
    val2 = val2_obj.value
    # Logic
    is_val1_str = isinstance(val1, (str, bytes, np.str_)) or (isinstance(val1, pd.Series) and ptypes.is_string_dtype(val1.dtype))
    is_val2_str = isinstance(val2, (str, bytes, np.str_)) or (isinstance(val2, pd.Series) and ptypes.is_string_dtype(val2.dtype))

    if is_val1_str and is_val2_str:
        if not isinstance(val1, pd.Series) and not isinstance(val2, pd.Series):
            return [KLiteral(np.char.add(val1, val2)[()], KLiteralType.STRING)]
        result = np.char.add(val1, val2)
        return [KArray(result)]
    elif not is_val1_str and not is_val2_str:
        # Both numeric (or boolean)
        result = np.add(val1, val2)
        if isinstance(result, (pd.Series, list)) or (isinstance(result, np.ndarray) and result.ndim > 0):
            return [KArray(result)]
        
        if isinstance(result, np.ndarray) and result.ndim == 0:
            result = result[()]
        return [KLiteral(result)]
    else:
        # Mixed numeric and string
        return [KErrorValue(
            KGenericException(f"Type mismatch: cannot add {type(val1).__name__} and {type(val2).__name__}"))]


k_builtin_library.register(kfunction(
    inputs=[("x1", K_ADD_TYPE), ("x2", K_ADD_TYPE)], outputs=[("y", KAnyTypeInfo())],
    name="+", use_values=True, use_context=False
)(_k_add_impl))
k_builtin_library.register(kfunction(
    inputs=[("x1", K_ADD_TYPE), ("x2", K_ADD_TYPE)], outputs=[("y", KAnyTypeInfo())],
    name="add", use_values=True, use_context=False
)(_k_add_impl))

# Subtraction
k_builtin_library.register(numpy_to_kfunction(
    np.subtract,
    [("x1", K_NP_MATH_TYPE), ("x2", K_NP_MATH_TYPE)],
    [("y", KAnyTypeInfo())],
    name="-"
))
k_builtin_library.register(numpy_to_kfunction(
    np.subtract,
    [("x1", K_NP_MATH_TYPE), ("x2", K_NP_MATH_TYPE)],
    [("y", KAnyTypeInfo())],
    name="subtract"
))


# Multiplication

def _k_multiply_impl(val1_obj, val2_obj):
    val1 = val1_obj.value
    val2 = val2_obj.value
    is_val1_str = isinstance(val1, (str, bytes, np.str_)) or (isinstance(val1, pd.Series) and ptypes.is_string_dtype(val1.dtype))
    is_val2_str = isinstance(val2, (str, bytes, np.str_)) or (isinstance(val2, pd.Series) and ptypes.is_string_dtype(val2.dtype))

    if is_val1_str and is_val2_str:
        return [KErrorValue(KGenericException("Type mismatch: cannot multiply string by string"))]

    if is_val1_str or is_val2_str:
        # One is string, one must be integer (or array of integers)
        string_val = val1 if is_val1_str else val2
        int_val = val2 if is_val1_str else val1

        # Check for scalar multiplication
        if not isinstance(string_val, pd.Series) and not isinstance(int_val, pd.Series):
            if isinstance(int_val, (int, np.integer)):
                result = np.char.multiply(string_val, int_val)[()]
                return [KLiteral(result)]
            else:
                return [
                    KErrorValue(KGenericException(f"Type mismatch: cannot multiply string by {type(int_val).__name__}"))]
        
        # Vectorized multiplication
        result = np.char.multiply(string_val, int_val)
        return [KArray(result)]

    # Both numeric
    result = np.multiply(val1, val2)
    if isinstance(result, (pd.Series, list)) or (isinstance(result, np.ndarray) and result.ndim > 0):
        return [KArray(result)]
    
    if isinstance(result, np.ndarray) and result.ndim == 0:
        result = result[()]
    return [KLiteral(result)]


k_builtin_library.register(
    kfunction(
        inputs=[("x1", K_MULT_TYPE), ("x2", K_MULT_TYPE)], outputs=[("y", KAnyTypeInfo())],
        name="*", use_values=True, use_context=False
    )(_k_multiply_impl)
)
k_builtin_library.register(
    kfunction(
        inputs=[("x1", K_MULT_TYPE), ("x2", K_MULT_TYPE)], outputs=[("y", KAnyTypeInfo())],
        name="multiply", use_values=True, use_context=False
    )(_k_multiply_impl)
)

# Division
k_builtin_library.register(numpy_to_kfunction(
    np.divide,
    [("x1", K_NP_MATH_TYPE), ("x2", K_NP_MATH_TYPE)],
    [("y", KAnyTypeInfo())],
    name="/"
))
k_builtin_library.register(numpy_to_kfunction(
    np.divide,
    [("x1", K_NP_MATH_TYPE), ("x2", K_NP_MATH_TYPE)],
    [("y", KAnyTypeInfo())],
    name="divide"
))

# Power
k_builtin_library.register(numpy_to_kfunction(
    np.power,
    [("base", K_NP_MATH_TYPE), ("exponent", K_NP_MATH_TYPE)],
    [("y", KAnyTypeInfo())],
    name="^"
))
k_builtin_library.register(numpy_to_kfunction(
    np.power,
    [("base", K_NP_MATH_TYPE), ("exponent", K_NP_MATH_TYPE)],
    [("y", KAnyTypeInfo())],
    name="power"
))

# Unary Negation
k_builtin_library.register(numpy_to_kfunction(
    np.negative,
    [("x", K_NP_MATH_TYPE)],
    [("y", KAnyTypeInfo())],
    name="unary_-"
))
k_builtin_library.register(numpy_to_kfunction(
    np.negative,
    [("x", K_NP_MATH_TYPE)],
    [("y", KAnyTypeInfo())],
    name="negative"
))

# Comparison Operators

# Equals
k_builtin_library.register(numpy_to_kfunction(
    k_compare_wrapper(np.equal, np.char.equal),
    [("left", K_ADD_TYPE), ("right", K_ADD_TYPE)],
    [("y", KAnyTypeInfo())],
    name="=="
))
k_builtin_library.register(numpy_to_kfunction(
    k_compare_wrapper(np.equal, np.char.equal),
    [("left", K_ADD_TYPE), ("right", K_ADD_TYPE)],
    [("y", KAnyTypeInfo())],
    name="equals"
))

# Not Equals
k_builtin_library.register(numpy_to_kfunction(
    k_compare_wrapper(np.not_equal, np.char.not_equal),
    [("left", K_ADD_TYPE), ("right", K_ADD_TYPE)],
    [("y", KAnyTypeInfo())],
    name="!="
))
k_builtin_library.register(numpy_to_kfunction(
    k_compare_wrapper(np.not_equal, np.char.not_equal),
    [("left", K_ADD_TYPE), ("right", K_ADD_TYPE)],
    [("y", KAnyTypeInfo())],
    name="not_equals"
))

# Greater Than
k_builtin_library.register(numpy_to_kfunction(
    k_compare_wrapper(np.greater, np.char.greater),
    [("left", K_ADD_TYPE), ("right", K_ADD_TYPE)],
    [("y", KAnyTypeInfo())],
    name=">"
))
k_builtin_library.register(numpy_to_kfunction(
    k_compare_wrapper(np.greater, np.char.greater),
    [("left", K_ADD_TYPE), ("right", K_ADD_TYPE)],
    [("y", KAnyTypeInfo())],
    name="greater"
))

# Less Than
k_builtin_library.register(numpy_to_kfunction(
    k_compare_wrapper(np.less, np.char.less),
    [("left", K_ADD_TYPE), ("right", K_ADD_TYPE)],
    [("y", KAnyTypeInfo())],
    name="<"
))
k_builtin_library.register(numpy_to_kfunction(
    k_compare_wrapper(np.less, np.char.less),
    [("left", K_ADD_TYPE), ("right", K_ADD_TYPE)],
    [("y", KAnyTypeInfo())],
    name="less"
))

# Greater Than or Equal
k_builtin_library.register(numpy_to_kfunction(
    k_compare_wrapper(np.greater_equal, np.char.greater_equal),
    [("left", K_ADD_TYPE), ("right", K_ADD_TYPE)],
    [("y", KAnyTypeInfo())],
    name=">="
))
k_builtin_library.register(numpy_to_kfunction(
    k_compare_wrapper(np.greater_equal, np.char.greater_equal),
    [("left", K_ADD_TYPE), ("right", K_ADD_TYPE)],
    [("y", KAnyTypeInfo())],
    name="greater_equal"
))

# Less Than or Equal
k_builtin_library.register(numpy_to_kfunction(
    k_compare_wrapper(np.less_equal, np.char.less_equal),
    [("left", K_ADD_TYPE), ("right", K_ADD_TYPE)],
    [("y", KAnyTypeInfo())],
    name="<="
))
k_builtin_library.register(numpy_to_kfunction(
    k_compare_wrapper(np.less_equal, np.char.less_equal),
    [("left", K_ADD_TYPE), ("right", K_ADD_TYPE)],
    [("y", KAnyTypeInfo())],
    name="less_equal"
))

# Logical Operators

# Logical Not
k_builtin_library.register(numpy_to_kfunction(
    np.logical_not,
    [("x", K_NP_MATH_TYPE)],
    [("y", KAnyTypeInfo())],
    name="unary_!"
))
k_builtin_library.register(numpy_to_kfunction(
    np.logical_not,
    [("x", K_NP_MATH_TYPE)],
    [("y", KAnyTypeInfo())],
    name="not"
))

# Logical And
k_builtin_library.register(numpy_to_kfunction(
    np.logical_and,
    [("left", K_NP_MATH_TYPE), ("right", K_NP_MATH_TYPE)],
    [("y", KAnyTypeInfo())],
    name="and"
))

# Logical Or
k_builtin_library.register(numpy_to_kfunction(
    np.logical_or,
    [("left", K_NP_MATH_TYPE), ("right", K_NP_MATH_TYPE)],
    [("y", KAnyTypeInfo())],
    name="or"
))

# Get Item

@kfunction(
    inputs=[("x", KUnionTypeInfo([K_ARRAY_TYPE, KTableTypeInfo()])), ("indices", K_ARRAY_TYPE)],
    outputs=[("y", KAnyTypeInfo())],
    name="getitem",
    use_values=True
)
def k_getitem(x_obj, indices_obj):
    x = x_obj.value
    is_x_array = isinstance(x, pd.Series)

    indices = indices_obj.value
    n_indices = indices.size

    if is_x_array and n_indices == 1:
        # Filter array
        result = x[indices[0]]
        return [KArray(result)]
    elif not is_x_array and n_indices == 2:
        # Select rows and columns
        result = x.iloc[indices[0], indices[1]]

        if isinstance(result, pd.Series):
            return [KArray(result.values)]
        
        return [KTable(result)]
    elif not is_x_array and n_indices == 1:
        # Select rows
        result = x.iloc[indices[0]]
        return [KTable(result)]
    else:
        return [KErrorValue(
            KGenericException(f"Invalid arguments for getitem: {x_obj.type_info}, {n_indices} indices provided"))]


k_builtin_library.register(k_getitem)