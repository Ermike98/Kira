from __future__ import annotations

from kira.kdata.kdata import KData
from kira.core.kcontext import KContext
from kira.core.kobject import KObject, KTypeInfo
from kira.core.kformula import KFormula
from kira.kdata.kcollection import KCollection
from kira.kdata.ktable import KTable
from kira.kdata.karray import KArray
from kira.knodes.knode import KNode
from kira.kexpections.kgenericexception import KGenericException


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
            min_expected = len(node.input_names) - len(node.default_inputs)
            assert len(node_inputs) >= min_expected, f"Input count mismatch for '{node.name}'. Expected at least {min_expected}, got {len(node_inputs)}"
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
            min_expected = len(self._node.input_names) - len(self._node.default_inputs)

            if len(self._node_inputs) < min_expected:
                result = KData(self.name, None, KGenericException(f"Input count mismatch for '{self._target_name}'. Expected at least {min_expected}, got {len(self._node_inputs)}"))
                context.register_object(result)
                return result

            # assert len(self._node_inputs) >= min_expected, \
            #     f"Input count mismatch for '{self._target_name}'. Expected at least {min_expected}, got {len(self._node_inputs)}"

        inputs = {}

        for node_name, node_input in zip(self._node.input_names, self._node_inputs):
            if isinstance(node_input, KFormula):
                res = node_input.eval(formulas_context)
            else:
                res = node_input.eval(local_context)

                if isinstance(res, KGenericException):
                    res = KData(node_name, None, res)
                
                # Auto-unpack strategy: inject DataFrame columns into formulas_context
                if res and isinstance(res.value, KTable):
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
