
from collections.abc import Callable

from kira.kdata.kdata import KData, KTypeInfo, KDataValue
from kira.knodes.knode import KNode, KNodeType


class KFunction(KNode):

    def __init__(self,
                 name: str,
                 func: Callable[[list[KData]], list[KDataValue]],
                 inputs: list[tuple[str, KTypeInfo] | str],
                 outputs: list[tuple[str, KTypeInfo] | str]
                 ):
        super().__init__(name, inputs, outputs)
        self._func = func

    def call(self, inputs: list[KData]) -> list[KDataValue]:
        return self._func(inputs)

    # def instantiate(self) -> KResult[KData]:
    #     results = [dependency.instantiate() for dependency in self.dependencies]
    #
    #     # check if all dependencies are valid
    #     failed_dependencies = [dependency for result, dependency in zip(results, self.dependencies) if not result]
    #     if failed_dependencies:
    #         return KResult([KOptional(name, None, KFailedDependency(failed_dependencies)) for name in self._outputs_names])
    #
    #     # if all dependencies are valid, check input names
    #     total_result_values = KResult(sum([res.results for res in results], []))
    #     inputs = [total_result_values.get(name) for name in self._input_names]
    #     missing_input_names = [i.name for i in inputs if not i]
    #     if missing_input_names:
    #         return KResult([KOptional(name, None, KMissingResults(missing_input_names)) for name in self._outputs_names])
    #
    #     # if all input names are valid, check types
    #     failed_type_checks = [(i.value, t) for i, t in zip(inputs, self._input_types) if not t.validate(i.value)]
    #     if failed_type_checks:
    #         return KResult([KOptional(name, None, KFailedTypeChecks(failed_type_checks)) for name in self._outputs_names])
    #
    #     return self._func([i.value for i in inputs])

    @property
    def type(self) -> KNodeType:
        return KNodeType.FUNCTION
