from __future__ import annotations

from abc import abstractmethod

from kira.kdata.kdata import KData, KTypeInfo, KDataType, KDataValue
from kira.core.kobject import KObject
from kira.core.kresult import KResult

import enum

from kira.kexpections.knode_exception import KNodeException, KNodeExceptionType
from kira.knodes.validate_types import validate_type


class KNodeType(enum.Enum):
    FUNCTION = 1
    WORKFLOW = 2

class KNode(KObject):

    def __init__(self,
                 name: str | None,
                 inputs: list[tuple[str, KTypeInfo] | str],
                 outputs: list[tuple[str, KTypeInfo] | str]
                 ):
        super().__init__(name=name)

        self._input_names = [el if isinstance(el, str) else el[0] for el in inputs]
        self._input_types: list[KTypeInfo] = [KTypeInfo(KDataType.ANY) if isinstance(el, str) else el[1] for el in inputs]

        self._outputs_names = [el if isinstance(el, str) else el[0] for el in outputs]
        self._outputs_types: list[KTypeInfo] = [KTypeInfo(KDataType.ANY) if isinstance(el, str) else el[1] for el in
                                                outputs]

    # @abstractmethod
    # def instantiate(self, inputs: dict[str, KData]) -> KResult[KData]:
    #     pass

    @abstractmethod
    def call(self, inputs: list[KData]) -> list[KDataValue]:
        pass

    def __call__(self, inputs: dict[str, KData]) -> KResult:
        # check input names
        missing_input_names = [name for name in self._input_names if (name not in inputs) or (not inputs[name])]
        if missing_input_names:
            return KResult(
                [KData(name, None, KNodeException(self, KNodeExceptionType.MISSING_INPUTS,
                                                  missing_input_names=missing_input_names))
                 for name in self._outputs_names])

        # if all input names are valid, check types
        input_vals = [inputs[name] for name in self._input_names]
        failed_in_type_checks = [(i, t) for i, t in zip(input_vals, self._input_types) if not validate_type(i.value, t)]
        if failed_in_type_checks:
            return KResult(
                [KData(name, None, KNodeException(self, KNodeExceptionType.WRONG_INPUT_TYPES,
                                                  failed_in_type_checks=failed_in_type_checks))
                 for name in self._outputs_names])

        output_val = self.call(input_vals)

        # check output size
        if len(output_val) < len(self._outputs_names):
            missing_output_names = [name for name in self._input_names if name not in inputs]
            return KResult(
                [KData(name, None, KNodeException(self, KNodeExceptionType.MISSING_OUTPUTS,
                                                  missing_input_names=missing_output_names))
                 for name in self._outputs_names])
        elif len(output_val) > len(self._outputs_names):
            return KResult(
                [KData(name, None, KNodeException(self, KNodeExceptionType.TOO_MANY_OUTPUTS))
                 for name in self._outputs_names])

        # check output types
        failed_out_type_checks = [(i, t) for i, t in zip(output_val, self._outputs_types) if not validate_type(i, t)]
        if failed_out_type_checks:
            return KResult(
                [KData(name, None, KNodeException(self, KNodeExceptionType.WRONG_OUTPUT_TYPES,
                                                      failed_out_type_checks=failed_out_type_checks))
                 for name in self._outputs_names])

        return KResult([KData(name, val) for name, val in zip(self._outputs_names, output_val)])


    @property
    def input_names(self) -> list[str]:
        return self._input_names

    @property
    def input_types(self) -> list[KTypeInfo]:
        return self._input_types

    @property
    def output_names(self) -> list[str]:
        return self._outputs_names

    @property
    def output_types(self) -> list[KTypeInfo]:
        return self._outputs_types