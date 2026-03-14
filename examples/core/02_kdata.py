from kira.kdata.kdata import KData
from kira.kdata.kliteral import KLiteral
from kira.kdata.karray import KArray
from kira.kdata.kerrorvalue import KErrorValue
from kira.kexpections.kexception import KException

import numpy as np

def main():
    print("--- Kira Core Example: KData ---")

    # 1. KLiteral: Basic data types
    int_data = KData("my_int", KLiteral(10))
    str_data = KData("my_str", KLiteral("Hello Kira"))
    print(f"Literal Integer: {int_data}")
    print(f"Literal String: {str_data}")

    # 2. KArray: Collection of numeric data via numpy
    # KArray in Kira wraps a numpy array.
    arr_values = np.array([1, 2, 3])
    k_array = KData("my_array", KArray(arr_values))
    print(f"KArray: {k_array}")

    # 3. KData with Error
    # KData can represent a value or an error (or both as a warning)
    error_data = KData("failing_op", None, KException("Something went wrong"))
    print(f"KData with error: {error_data}")
    print(f"Is it valid? {bool(error_data)}")

if __name__ == "__main__":
    main()
