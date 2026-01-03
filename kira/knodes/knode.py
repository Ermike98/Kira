from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kira.core.kcontext import KContext
from kira.kdata.kdata import KData, KDataValue
from kira.core.kobject import KObject, KTypeInfo
from kira.kdata.kcollection import KCollection

import enum

from kira.kexpections.kexception import KExceptionTypeInfo
from kira.kexpections.knode_exception import KNodeException, KNodeExceptionType
from kira.ktypeinfo.any_type import KAnyTypeInfo


class KNodeType(enum.Enum):
    FUNCTION = 1
    WORKFLOW = 2


class KNodeTypeInfo(KTypeInfo):
    def match(self, value: KObject) -> bool:
        return isinstance(value, KNode)

    def __repr__(self) -> str:
        return "KNodeTypeInfo()"


class KNode(KObject):

    def __init__(self,
                 name: str | None,
                 inputs: list[tuple[str, KTypeInfo] | str],
                 outputs: list[tuple[str, KTypeInfo] | str]
                 ):
        super().__init__(name=name)

        self._input_names = [el if isinstance(el, str) else el[0] for el in inputs]
        self._input_types: list[KTypeInfo] = [KAnyTypeInfo() if isinstance(el, str) else el[1] for el in
                                              inputs]

        self._outputs_names = [el if isinstance(el, str) else el[0] for el in outputs]
        self._outputs_types: list[KTypeInfo] = [KAnyTypeInfo() if isinstance(el, str) else el[1] for el in
                                                outputs]

    # @abstractmethod
    # def instantiate(self, inputs: dict[str, KData]) -> KResult[KData]:
    #     pass

    def eval(self, context: KContext) -> KData:
        inputs = {name: context.get_object(name) for name in self._input_names}

        result = self(inputs, context)
        if len(result) == 1:
            return result[0]

        return KData(f"result_{self.name}", KCollection(result))

    @abstractmethod
    def call(self, inputs: list[KObject], context: KContext) -> list[KDataValue]:
        pass

    def __call__(self, inputs: dict[str, KObject], context: KContext) -> list[KData]:
        # check input names
        missing_input_names = [name for name in self._input_names if (name not in inputs) or (not inputs[name])]
        if missing_input_names:
            return [KData(name, None, KNodeException(self, KNodeExceptionType.MISSING_INPUTS,
                                                     missing_input_names=missing_input_names))
                    for name in self._outputs_names]

        # if all input names are valid, check types
        input_vals = [inputs[name] for name in self._input_names]
        failed_in_type_checks = [(i, t) for i, t in zip(input_vals, self._input_types) if not t.match(i)]
        if failed_in_type_checks:
            return [KData(name, None, KNodeException(self, KNodeExceptionType.WRONG_INPUT_TYPES,
                                                     failed_in_type_checks=failed_in_type_checks))
                    for name in self._outputs_names]

        output_val = self.call(input_vals, context)

        # check output size
        if len(output_val) < len(self._outputs_names):
            missing_output_names = [name for name in self._input_names if name not in inputs]
            return [KData(name, None, KNodeException(self, KNodeExceptionType.MISSING_OUTPUTS,
                                                     missing_input_names=missing_output_names))
                    for name in self._outputs_names]
        elif len(output_val) > len(self._outputs_names):
            return [KData(name, None, KNodeException(self, KNodeExceptionType.TOO_MANY_OUTPUTS))
                    for name in self._outputs_names]

        kdata_list = []

        for i, t, name in zip(output_val, self._outputs_types, self._outputs_names):
            # check output is valid
            if isinstance(i.type, KExceptionTypeInfo):
                kdata_list.append(KData(name, None, KNodeException(self, KNodeExceptionType.FAILED_OUTPUT,
                                                                   failed_output=i.value)))
            # check output type
            elif not t.match(KData(name, i)):
                kdata_list.append(KData(name, None, KNodeException(self, KNodeExceptionType.WRONG_OUTPUT_TYPES,
                                                                   failed_out_type_checks=(i, t))))
            # output is valid
            else:
                kdata_list.append(KData(name, i))

        return kdata_list

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

    @property
    def type(self) -> KTypeInfo:
        return KNodeTypeInfo()
