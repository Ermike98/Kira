from functools import wraps
from typing import Callable

import numpy as np

from kira.core.kcontext import KContext
from kira.core.kobject import KTypeInfo
from kira.kdata.karray import K_ARRAY_INTEGER_TYPE, K_ARRAY_NUMBER_TYPE, K_ARRAY_BOOLEAN_TYPE, K_ARRAY_STRING_TYPE, \
    KArray
from kira.kdata.kdata import KData, KDataValue
from kira.kdata.kliteral import K_BOOLEAN_TYPE, K_INTEGER_TYPE, K_NUMBER_TYPE, K_STRING_TYPE, KLiteral, K_LITERAL_TYPE
from kira.kdata.kerrorvalue import KErrorValue
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

# Arithmetic Functions

@kfunction(
    inputs=[("x1", K_ADD_TYPE), ("x2", K_ADD_TYPE)],
    outputs=[("y", KAnyTypeInfo())],
    name="+",
    use_values=True,
    use_context=False
)
def k_add(val1_obj, val2_obj):
    val1 = val1_obj.value
    val2 = val2_obj.value
    # Logic
    is_val1_str = isinstance(val1, (str, bytes)) or (isinstance(val1, np.ndarray) and val1.dtype.kind in 'SU')
    is_val2_str = isinstance(val2, (str, bytes)) or (isinstance(val2, np.ndarray) and val2.dtype.kind in 'SU')

    if is_val1_str and is_val2_str:
        result = np.char.add(val1, val2)
        return [KArray(result)]
    elif not is_val1_str and not is_val2_str:
        # Both numeric (or boolean)
        result = np.add(val1, val2)
        if isinstance(result, np.ndarray):
            return [KArray(result)]
        return [KLiteral(result)]
    else:
        # Mixed numeric and string
        return [KErrorValue(
            KGenericException(f"Type mismatch: cannot add {type(val1).__name__} and {type(val2).__name__}"))]


k_builtin_library.register(k_add)

# Subtraction
k_builtin_library.register(numpy_to_kfunction(
    np.subtract,
    [("x1", K_NP_MATH_TYPE), ("x2", K_NP_MATH_TYPE)],
    [("y", KAnyTypeInfo())],
    name="-"
))


# Multiplication
@kfunction(
    inputs=[("x1", K_MULT_TYPE), ("x2", K_MULT_TYPE)],
    outputs=[("y", KAnyTypeInfo())],
    name="*",
    use_values=True,
    use_context=False
)
def k_multiply(val1_obj, val2_obj):
    val1 = val1_obj.value
    val2 = val2_obj.value
    is_val1_str = isinstance(val1, (str, bytes)) or (isinstance(val1, np.ndarray) and val1.dtype.kind in 'SU')
    is_val2_str = isinstance(val2, (str, bytes)) or (isinstance(val2, np.ndarray) and val2.dtype.kind in 'SU')

    if is_val1_str and is_val2_str:
        return [KErrorValue(KGenericException("Type mismatch: cannot multiply string by string"))]

    if is_val1_str or is_val2_str:
        # One is string, one must be integer (or array of integers)
        string_val = val1 if is_val1_str else val2
        int_val = val2 if is_val1_str else val1

        # Check if int_val is indeed integer
        if isinstance(int_val, (int, np.integer)):
            result = np.char.multiply(string_val, int_val)
            if isinstance(result, np.ndarray):
                return [KArray(result)]
            return [KLiteral(result)]
        elif isinstance(int_val, np.ndarray) and np.issubdtype(int_val.dtype, np.integer):
            result = np.char.multiply(string_val, int_val)
            return [KArray(result)]
        else:
            return [
                KErrorValue(KGenericException(f"Type mismatch: cannot multiply string by {type(int_val).__name__}"))]

    # Both numeric
    result = np.multiply(val1, val2)
    if isinstance(result, np.ndarray):
        return [KArray(result)]
    return [KLiteral(result)]


k_builtin_library.register(k_multiply)

# Division
k_builtin_library.register(numpy_to_kfunction(
    np.divide,
    [("x1", K_NP_MATH_TYPE), ("x2", K_NP_MATH_TYPE)],
    [("y", KAnyTypeInfo())],
    name="/"
))

# Power
k_builtin_library.register(numpy_to_kfunction(
    np.power,
    [("x1", K_NP_MATH_TYPE), ("x2", K_NP_MATH_TYPE)],
    [("y", KAnyTypeInfo())],
    name="^"
))

# Unary Negation
k_builtin_library.register(numpy_to_kfunction(
    np.negative,
    [("x", K_NP_MATH_TYPE)],
    [("y", KAnyTypeInfo())],
    name="unary_-"
))

# Comparison Operators

# Equals
k_builtin_library.register(numpy_to_kfunction(
    k_compare_wrapper(np.equal, np.char.equal),
    [("x1", K_ADD_TYPE), ("x2", K_ADD_TYPE)],
    [("y", KAnyTypeInfo())],
    name="=="
))

# Not Equals
k_builtin_library.register(numpy_to_kfunction(
    k_compare_wrapper(np.not_equal, np.char.not_equal),
    [("x1", K_ADD_TYPE), ("x2", K_ADD_TYPE)],
    [("y", KAnyTypeInfo())],
    name="!="
))

# Greater Than
k_builtin_library.register(numpy_to_kfunction(
    k_compare_wrapper(np.greater, np.char.greater),
    [("x1", K_ADD_TYPE), ("x2", K_ADD_TYPE)],
    [("y", KAnyTypeInfo())],
    name=">"
))

# Less Than
k_builtin_library.register(numpy_to_kfunction(
    k_compare_wrapper(np.less, np.char.less),
    [("x1", K_ADD_TYPE), ("x2", K_ADD_TYPE)],
    [("y", KAnyTypeInfo())],
    name="<"
))

# Greater Than or Equal
k_builtin_library.register(numpy_to_kfunction(
    k_compare_wrapper(np.greater_equal, np.char.greater_equal),
    [("x1", K_ADD_TYPE), ("x2", K_ADD_TYPE)],
    [("y", KAnyTypeInfo())],
    name=">="
))

# Less Than or Equal
k_builtin_library.register(numpy_to_kfunction(
    k_compare_wrapper(np.less_equal, np.char.less_equal),
    [("x1", K_ADD_TYPE), ("x2", K_ADD_TYPE)],
    [("y", KAnyTypeInfo())],
    name="<="
))

# Logical Operators

# Logical Not
k_builtin_library.register(numpy_to_kfunction(
    np.logical_not,
    [("x", K_NP_MATH_TYPE)],
    [("y", KAnyTypeInfo())],
    name="unary_!"
))

# Logical And
k_builtin_library.register(numpy_to_kfunction(
    np.logical_and,
    [("x1", K_NP_MATH_TYPE), ("x2", K_NP_MATH_TYPE)],
    [("y", KAnyTypeInfo())],
    name="and"
))

# Logical Or
k_builtin_library.register(numpy_to_kfunction(
    np.logical_or,
    [("x1", K_NP_MATH_TYPE), ("x2", K_NP_MATH_TYPE)],
    [("y", KAnyTypeInfo())],
    name="or"
))
