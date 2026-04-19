from kira import KLiteralType
from kira import KData
from functools import wraps
from typing import Callable

import numpy as np

from kira.core.kobject import KTypeInfo
from kira.kdata.karray import K_ARRAY_INTEGER_TYPE, K_ARRAY_NUMBER_TYPE, K_ARRAY_BOOLEAN_TYPE, KArray
from kira.kdata.kliteral import K_BOOLEAN_TYPE, K_INTEGER_TYPE, K_NUMBER_TYPE, KLiteral
from kira.knodes.kfunction import KFunction, kfunction
from kira.ktypeinfo.union_type import KUnionTypeInfo
from kira.library.node_library import KLibrary
from kira import keval_script
import scipy.special as sp

# Create a library of basic math functions wrapping Numpy functions

K_NP_MATH_TYPE = KUnionTypeInfo([
    K_INTEGER_TYPE, K_NUMBER_TYPE, K_BOOLEAN_TYPE,
    K_ARRAY_INTEGER_TYPE, K_ARRAY_NUMBER_TYPE, K_ARRAY_BOOLEAN_TYPE
])

k_math_library = KLibrary("Math")


from kira.library.library_utils import numpy_to_kfunction

# Trigonometric Functions

# Trigonometric sine, element-wise.
k_math_library.register(numpy_to_kfunction(
    np.sin,  # (x, /[, out, where, casting, order, ...])
    [("x", K_NP_MATH_TYPE)],
    [("y", K_NP_MATH_TYPE)]
))

# Trigonometric cosine, element-wise.
k_math_library.register(numpy_to_kfunction(
    np.cos,  # (x, /[, out, where, casting, order, ...])
    [("x", K_NP_MATH_TYPE)],
    [("y", K_NP_MATH_TYPE)]
))

# Trigonometric tangent, element-wise.
k_math_library.register(numpy_to_kfunction(
    np.tan,  # (x, /[, out, where, casting, order, ...])
    [("x", K_NP_MATH_TYPE)],
    [("y", K_NP_MATH_TYPE)]
))

# Trigonometric inverse sine, element-wise.
k_math_library.register(numpy_to_kfunction(
    np.arcsin,  # (x, /[, out, where, casting, order, ...])
    [("x", K_NP_MATH_TYPE)],
    [("y", K_NP_MATH_TYPE)]
))

# Trigonometric inverse cosine, element-wise.
k_math_library.register(numpy_to_kfunction(
    np.arccos,  # (x, /[, out, where, casting, order, ...])
    [("x", K_NP_MATH_TYPE)],
    [("y", K_NP_MATH_TYPE)]
))

# Trigonometric inverse tangent, element-wise.
k_math_library.register(numpy_to_kfunction(
    np.arctan,  # (x, /[, out, where, casting, order, ...])
    [("x", K_NP_MATH_TYPE)],
    [("y", K_NP_MATH_TYPE)]
))

# Element-wise arc tangent of x1/x2 choosing the quadrant correctly.
k_math_library.register(numpy_to_kfunction(
    np.arctan2,  # (x1, x2, /[, out, where, casting, ...])
    [("x1", K_NP_MATH_TYPE), ("x2", K_NP_MATH_TYPE)],
    [("y", K_NP_MATH_TYPE)]
))

# Convert angles from degrees to radians.
k_math_library.register(numpy_to_kfunction(
    np.deg2rad,  # (x, /[, out, where, casting, order, ...])
    [("x", K_NP_MATH_TYPE)],
    [("y", K_NP_MATH_TYPE)]
))

# Convert angles from radians to degrees.
k_math_library.register(numpy_to_kfunction(
    np.rad2deg,  # (x, /[, out, where, casting, order, ...])
    [("x", K_NP_MATH_TYPE)],
    [("y", K_NP_MATH_TYPE)]
))


# Exponential and Logarithmic Functions

# Exponential function, element-wise.
k_math_library.register(numpy_to_kfunction(
    np.exp,
    [("x", K_NP_MATH_TYPE)],
    [("y", K_NP_MATH_TYPE)]
))

# Natural logarithm, element-wise.
k_math_library.register(numpy_to_kfunction(
    np.log,
    [("x", K_NP_MATH_TYPE)],
    [("y", K_NP_MATH_TYPE)]
))

# Base-10 logarithm, element-wise.
k_math_library.register(numpy_to_kfunction(
    np.log10,
    [("x", K_NP_MATH_TYPE)],
    [("y", K_NP_MATH_TYPE)]
))

# Base-2 logarithm, element-wise.
k_math_library.register(numpy_to_kfunction(
    np.log2,
    [("x", K_NP_MATH_TYPE)],
    [("y", K_NP_MATH_TYPE)]
))

# Square root, element-wise.
k_math_library.register(numpy_to_kfunction(
    np.sqrt,
    [("x", K_NP_MATH_TYPE)],
    [("y", K_NP_MATH_TYPE)]
))

# Cube root, element-wise.
k_math_library.register(numpy_to_kfunction(
    np.cbrt,
    [("x", K_NP_MATH_TYPE)],
    [("y", K_NP_MATH_TYPE)]
))


# Hyperbolic Functions

# Hyperbolic sine, element-wise.
k_math_library.register(numpy_to_kfunction(
    np.sinh,  # (x, /[, out, where, casting, order, ...])
    [("x", K_NP_MATH_TYPE)],
    [("y", K_NP_MATH_TYPE)]
))

# Hyperbolic cosine, element-wise.
k_math_library.register(numpy_to_kfunction(
    np.cosh,  # (x, /[, out, where, casting, order, ...])
    [("x", K_NP_MATH_TYPE)],
    [("y", K_NP_MATH_TYPE)]
))

# Hyperbolic tangent, element-wise.
k_math_library.register(numpy_to_kfunction(
    np.tanh,  # (x, /[, out, where, casting, order, ...])
    [("x", K_NP_MATH_TYPE)],
    [("y", K_NP_MATH_TYPE)]
))

# Inverse hyperbolic sine, element-wise.
k_math_library.register(numpy_to_kfunction(
    np.arcsinh,  # (x, /[, out, where, casting, order, ...])
    [("x", K_NP_MATH_TYPE)],
    [("y", K_NP_MATH_TYPE)]
))

# Inverse hyperbolic cosine, element-wise.
k_math_library.register(numpy_to_kfunction(
    np.arccosh,  # (x, /[, out, where, casting, order, ...])
    [("x", K_NP_MATH_TYPE)],
    [("y", K_NP_MATH_TYPE)]
))

# Inverse hyperbolic tangent, element-wise.
k_math_library.register(numpy_to_kfunction(
    np.arctanh,  # (x, /[, out, where, casting, order, ...])
    [("x", K_NP_MATH_TYPE)],
    [("y", K_NP_MATH_TYPE)]
))


# Rounding Functions

# Round to nearest integer.
k_math_library.register(numpy_to_kfunction(
    np.round,
    [("x", K_NP_MATH_TYPE)],
    [("y", K_NP_MATH_TYPE)],
    name="round"
))

# Round to n decimal places.
k_math_library.register(numpy_to_kfunction(
    np.round,
    [("x", K_NP_MATH_TYPE), ("decimals", K_INTEGER_TYPE)],
    [("y", K_NP_MATH_TYPE)],
    name="roundn"
))

# Floor element-wise.
k_math_library.register(numpy_to_kfunction(
    np.floor,
    [("x", K_NP_MATH_TYPE)],
    [("y", K_NP_MATH_TYPE)]
))

# Ceil element-wise.
k_math_library.register(numpy_to_kfunction(
    np.ceil,
    [("x", K_NP_MATH_TYPE)],
    [("y", K_NP_MATH_TYPE)]
))


# Absolute and Sign Functions

# Absolute value, element-wise.
k_math_library.register(numpy_to_kfunction(
    np.abs,
    [("x", K_NP_MATH_TYPE)],
    [("y", K_NP_MATH_TYPE)],
    name="abs"
))

# Sign of each element.
k_math_library.register(numpy_to_kfunction(
    np.sign,
    [("x", K_NP_MATH_TYPE)],
    [("y", K_NP_MATH_TYPE)]
))


# Miscellaneous Utilities

# Element-wise remainder of division.
k_math_library.register(numpy_to_kfunction(
    np.mod,
    [("x1", K_NP_MATH_TYPE), ("x2", K_NP_MATH_TYPE)],
    [("y", K_NP_MATH_TYPE)]
))

# Clip (limit) the values in an array.
k_math_library.register(numpy_to_kfunction(
    np.clip,
    [("x", K_NP_MATH_TYPE), ("min", K_NP_MATH_TYPE), ("max", K_NP_MATH_TYPE)],
    [("y", K_NP_MATH_TYPE)]
))

# Element-wise minimum.
k_math_library.register(numpy_to_kfunction(
    np.minimum,
    [("x1", K_NP_MATH_TYPE), ("x2", K_NP_MATH_TYPE)],
    [("y", K_NP_MATH_TYPE)],
    name="minimum"
))

# Element-wise maximum.
k_math_library.register(numpy_to_kfunction(
    np.maximum,
    [("x1", K_NP_MATH_TYPE), ("x2", K_NP_MATH_TYPE)],
    [("y", K_NP_MATH_TYPE)],
    name="maximum"
))


# Special Functions

# Gamma function.
k_math_library.register(numpy_to_kfunction(
    sp.gamma,
    [("x", K_NP_MATH_TYPE)],
    [("y", K_NP_MATH_TYPE)],
    name="gamma"
))

# Sigmoid function implemented as a workflow.
sigmoid_src = """
workflow sigmoid(x) -> y:
    y = 1 / (1 + exp(-x))
    return y
"""
k_math_library.register(keval_script(sigmoid_src))

k_math_library.register(KData("PI", KLiteral(np.pi, KLiteralType.NUMBER)))
k_math_library.register(KData("E", KLiteral(np.e, KLiteralType.NUMBER)))