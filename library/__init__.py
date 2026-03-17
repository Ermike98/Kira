from .builtin_library import k_builtin_library
from .math_library import k_math_library
from kira import KContext

default_libraries = [
    k_builtin_library,
    k_math_library,
]

def load_libraries(ctx: KContext):
    for lib in default_libraries:
        lib.eval(ctx)

    ctx.debug_print()
