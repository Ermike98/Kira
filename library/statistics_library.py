import numpy as np
from kira.kdata.karray import K_ARRAY_TYPE
from kira.kdata.kliteral import K_NUMBER_TYPE
from kira.library.node_library import KLibrary
from kira.library.library_utils import numpy_to_kfunction

# Create a library of basic statistics functions
k_statistics_library = KLibrary("Statistics")

# Minimum element in an array.
k_statistics_library.register(numpy_to_kfunction(
    np.min,
    [("x", K_ARRAY_TYPE)],
    [("y", K_NUMBER_TYPE)],
    name="min"
))

# Maximum element in an array.
k_statistics_library.register(numpy_to_kfunction(
    np.max,
    [("x", K_ARRAY_TYPE)],
    [("y", K_NUMBER_TYPE)],
    name="max"
))

# Arithmetic mean.
k_statistics_library.register(numpy_to_kfunction(
    np.mean,
    [("x", K_ARRAY_TYPE)],
    [("y", K_NUMBER_TYPE)],
    name="mean"
))

# Median.
k_statistics_library.register(numpy_to_kfunction(
    np.median,
    [("x", K_ARRAY_TYPE)],
    [("y", K_NUMBER_TYPE)],
    name="median"
))

# Standard deviation.
k_statistics_library.register(numpy_to_kfunction(
    np.std,
    [("x", K_ARRAY_TYPE)],
    [("y", K_NUMBER_TYPE)],
    name="std"
))

# Variance.
k_statistics_library.register(numpy_to_kfunction(
    np.var,
    [("x", K_ARRAY_TYPE)],
    [("y", K_NUMBER_TYPE)],
    name="var"
))

# Quantile.
k_statistics_library.register(numpy_to_kfunction(
    np.quantile,
    [("x", K_ARRAY_TYPE), ("q", K_NUMBER_TYPE)],
    [("y", K_NUMBER_TYPE)],
    name="quantile"
))
