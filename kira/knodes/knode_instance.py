from __future__ import annotations

from kira.kdata.kdata import KData
from kira.core.kcontext import KContext
from kira.core.kobject import KObject, KTypeInfo
from kira.core.kformula import KFormula
from kira.kdata.kcollection import KCollection, KCollectionTypeInfo
from kira.kdata.ktable import KTable
from kira.kdata.karray import KArray
from kira.kdata.kerrorvalue import KErrorValue
from kira.knodes.knode import KNode
from kira.kexpections.kgenericexception import KGenericException
from kira.ktypeinfo.variadic_type import KVariadicTypeInfo


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
            num_fixed = len(node.input_names) - (1 if node.has_variadic else 0)
            min_expected = num_fixed - len(node.default_inputs)
            assert len(node_inputs) >= min_expected, \
                f"Input count mismatch for '{node.name}'. Expected at least {min_expected}, got {len(node_inputs)}"
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
            if not isinstance(obj, KNode):
                result = KData(self.name, None, KGenericException(f"Object '{self._target_name}' is not a KNode"))
                context.register_object(result)
                return result

            self._node = obj

        num_fixed = len(self._node.input_names) - (1 if self._node.has_variadic else 0)
        min_expected = num_fixed - len(self._node.default_inputs)

        # Validate input count
        if len(self._node_inputs) < min_expected:
            result = KData(self.name, None, KGenericException(
                f"Input count mismatch for '{self._target_name}'. "
                f"Expected at least {min_expected}, got {len(self._node_inputs)}"))
            context.register_object(result)
            return result

        # 1. Evaluate all inputs
        evaluated = []
        for i, node_input in enumerate(self._node_inputs):
            if isinstance(node_input, KFormula):
                res = node_input.eval(formulas_context)
            else:
                res = node_input.eval(local_context)

            if isinstance(res, KGenericException):
                input_name = self._node.input_names[i] if i < num_fixed else self._node.input_names[-1]
                res = KData(input_name, None, res)
            
            # Auto-unpack strategy: inject DataFrame columns into formulas_context
            if res and isinstance(res.value, KTable):
                df = res.value.value
                for col in df.columns:
                    formulas_context.register_object(KData(col, KArray(df[col].to_numpy())))

            evaluated.append(res)

        # 2. Build inputs dict
        inputs = {}

        for i in range(min(num_fixed, len(evaluated))):
            node_name = self._node.input_names[i]
            inputs[node_name] = KData(node_name, evaluated[i].value, evaluated[i].error)

        if self._node.has_variadic:
            var_name = self._node.input_names[-1]
            variadic_type = self._node.input_types[-1]
            remaining = evaluated[num_fixed:]

            # Determine if this is a multi-variadic (element_type is KCollectionTypeInfo)
            is_multi = isinstance(variadic_type, KVariadicTypeInfo) and \
                       isinstance(variadic_type.element_type, KCollectionTypeInfo)

            if is_multi:
                # Multi-variadic: group arguments into KCollections
                field_names = variadic_type.element_type.field_names
                group_size = len(field_names)

                if len(remaining) % group_size != 0:
                    inputs[var_name] = KData(var_name, None, KGenericException(
                        f"Variadic input count mismatch for '{var_name}'. "
                        f"Expected multiple of {group_size}, got {len(remaining)}"))
                else:
                    variadic_values = [
                        KCollection([KData(field_names[k], remaining[j + k].value, remaining[j + k].error)
                                     for k in range(group_size)])
                        for j in range(0, len(remaining), group_size)
                    ]
                    inputs[var_name] = KData(var_name, KArray(variadic_values))
            else:
                # Single variadic: pack KDataValues directly
                # TODO if element_type is KLiteralTypeInfo, unwrap them so the resulting array has the specified literal type and is not an array of objects (KDataValues)
                variadic_values = [
                    res.value if res else KErrorValue(res.error)
                    for res in remaining
                ]
                inputs[var_name] = KData(var_name, KArray(variadic_values))

        call_result = self._node(inputs, local_context)

        if len(call_result) == 1:
            result = KData(self.name, call_result[0].value, call_result[0].error)
        else:
            result = KData(self.name, KCollection(call_result))

        context.register_object(result)

        return result
