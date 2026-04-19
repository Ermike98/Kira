from .builtin_library import k_builtin_library
from .math_library import k_math_library
from .array_library import k_array_library
from .table_library import k_table_library
from .statistics_library import k_statistics_library
from kira import KContext

default_libraries = [
    k_builtin_library,
    k_math_library,
    k_array_library,
    k_table_library,
    k_statistics_library,
]

def load_libraries(ctx: KContext):
    for lib in default_libraries:
        lib.eval(ctx)
