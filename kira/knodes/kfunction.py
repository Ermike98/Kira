
from collections.abc import Callable

from kira.kdata.kdata import KData, KTypeInfo, KDataValue
from kira.knodes.knode import KNode, KNodeType


class KFunction(KNode):

    def __init__(self,
                 name: str,
                 func: Callable[[list[KDataValue]], list[KDataValue]],
                 inputs: list[tuple[str, KTypeInfo] | str],
                 outputs: list[tuple[str, KTypeInfo] | str]
                 ):
        super().__init__(name, inputs, outputs)
        self._func = func

    def call(self, inputs: list[KData]) -> list[KDataValue]:
        input_vals = [i.value for i in inputs]
        return self._func(input_vals)

    @property
    def type(self) -> KNodeType:
        return KNodeType.FUNCTION
