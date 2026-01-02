from __future__ import annotations

from typing import NamedTuple

from kira.core.kcontext import KContext
from kira.core.kobject import KObject, KTypeInfo
from kira.core.kresult import KResult
from kira.kdata.kdata import KData
from kira.knodes.knode import KNode


class KNodeInstanceTypeInfo(KTypeInfo):
    def match(self, value: KObject) -> bool:
        return False

    def __repr__(self) -> str:
        return "KNodeInstanceTypeInfo()"


class KNodeInstance(KObject):

    def __init__(self, name: str, node: KNode, node_inputs: list[KObject]):
        super().__init__(name)
        assert len(node_inputs) == len(node.input_names), "The number of inputs must match the number of inputs in the node"
        self._node = node
        self._node_inputs = node_inputs

    @property
    def type(self) -> KTypeInfo:
        return KNodeInstanceTypeInfo()

    def eval(self, context: KContext) -> KResult:
        local_context = KContext(context)

        inputs = {node_name: node_input.eval(local_context)
                  for node_name, node_input in zip(self._node.input_names, self._node_inputs)}

        result = KResult(self.name, self._node(inputs, local_context))

        context.register_object(result)

        return result

    # def __call__(self, inputs: dict[str, KData]) -> KResult:
    #     return KResult(self.name, self.node(inputs))
