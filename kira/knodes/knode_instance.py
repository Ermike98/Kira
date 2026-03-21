from __future__ import annotations

from kira.kdata.kdata import KData
from kira.core.kcontext import KContext
from kira.core.kobject import KObject, KTypeInfo
from kira.core.kformula import KFormula
from kira.kdata.kcollection import KCollection
from kira.kdata.ktable import KTable
from kira.kdata.karray import KArray
from kira.knodes.knode import KNode


class KNodeInstanceTypeInfo(KTypeInfo):
    def match(self, value: KObject) -> bool:
        return False

    def __repr__(self) -> str:
        return "KNodeInstanceTypeInfo()"


class KNodeInstance(KObject):

    def __init__(self, name: str, node: KNode | str, node_inputs: list[KObject]):
        super().__init__(name)
        
        self._target_name = None
        self._node = None
        
        if isinstance(node, KNode):
            assert len(node_inputs) == len(node.input_names), "The number of inputs must match the number of inputs in the node"
            self._node = node
            self._target_name = node.name
        else:
            self._target_name = node
            
        self._node_inputs = node_inputs

    @property
    def type(self) -> KTypeInfo:
        return KNodeInstanceTypeInfo()

    def eval(self, context: KContext) -> KData:
        local_context = KContext(context)
        formulas_context = KContext(context)

        # Resolve node if not already resolved
        if self._node is None:
            obj = context.get_object(self._target_name)
            assert isinstance(obj, KNode), f"Object '{self._target_name}' is not a KNode"
            self._node = obj
            # Deferred validation
            assert len(self._node_inputs) == len(self._node.input_names), \
                f"Input count mismatch for '{self._target_name}'. Expected {len(self._node.input_names)}, got {len(self._node_inputs)}"

        inputs = {}

        for node_name, node_input in zip(self._node.input_names, self._node_inputs):
            if isinstance(node_input, KFormula):
                res = node_input.eval(formulas_context)
            else:
                res = node_input.eval(local_context)
                
                # Auto-unpack strategy: inject DataFrame columns into formulas_context
                if isinstance(res.value, KTable):
                    df = res.value.value
                    for col in df.columns:
                        formulas_context.register_object(KData(col, KArray(df[col].to_numpy())))

            inputs[node_name] = KData(node_name, res.value, res.error)


        call_result = self._node(inputs, local_context)

        if len(call_result) == 1:
            result = KData(self.name, call_result[0].value, call_result[0].error)
        else:
            result = KData(self.name, KCollection(call_result))

        context.register_object(result)

        return result
