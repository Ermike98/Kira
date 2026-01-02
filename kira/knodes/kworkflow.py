from typing import NamedTuple

from kira.core.kcontext import KContext
from kira.kdata.kdata import KData, KDataValue
from kira.core.kobject import KTypeInfo, KObject
from kira.kdata.kerrorvalue import KErrorValue
from kira.knodes.knode import KNode
from kira.knodes.knode_instance import KNodeInstance


class EdgeWorkflow(NamedTuple):
    from_node: KNodeInstance | None
    from_name: str
    to_node: KNodeInstance | None
    to_name: str


class KWorkflow(KNode):
    def __init__(self,
                 name: str,
                 inputs: list[tuple[str, KTypeInfo] | str],
                 outputs: list[tuple[str, KTypeInfo] | str],
                 output_symbols: list[str],
                 nodes: list[KObject] = None):
        super().__init__(name, inputs, outputs)
        assert len(output_symbols) == len(outputs), "The number of output symbols must match the number of outputs"
        self._output_symbols = output_symbols
        self._nodes: list[KObject] = nodes if nodes is not None else []

    # def _init_graph(self):
    #     graph = {node: set() for node in self._nodes}
    #     # node_input_map: KNodeInstance -> { input_name: context_key }
    #     node_input_map  = {node: {} for node in self._nodes}
    #     # workflow_output_map: output_name -> context_key
    #     workflow_output_map  = {}
    #
    #     for edge in self._edges:
    #         # Prepare the context key: "NodeName.KDataName" or just "KDataName" if from workflow input
    #         context_key = edge.from_name if edge.from_node is None else f"{edge.from_node.name}.{edge.from_name}"
    #
    #         if edge.to_node is not None:
    #             # Track dependency for TopologicalSorter
    #             if edge.from_node is not None:
    #                 graph[edge.to_node].add(edge.from_node)
    #             # Map node input to its source in the context
    #             node_input_map[edge.to_node][edge.to_name] = context_key
    #         else:
    #             # Map workflow-level output to its source in the context
    #             workflow_output_map[edge.to_name] = context_key
    #
    #     return graph, node_input_map, workflow_output_map

    def call(self, inputs: list[KData], context: KContext) -> list[KDataValue]:
        ctx = KContext(context)

        # 1. Register workflow inputs into context using their intrinsic names
        for data in inputs:
            ctx.register_object(data)

        # 2. Execute nodes in the topological order
        for node in self._nodes:
            # Execute the node and register its KResult in context
            result = node.eval(ctx)
            ctx.register_object(result)

        # 3. Collect final workflow outputs
        workflow_results = []
        for out_name, ctx_key in zip(self._outputs_names, self._output_symbols):
            val = ctx.get_object(ctx_key)

            # Extract KDataValue from KData
            assert isinstance(val, KData), f"Output {out_name} is not a KData."

            if val:
                workflow_results.append(val.value)
            else:
                workflow_results.append(KErrorValue(val.error))

        return workflow_results

    def add_node(self, node: KNode):
        pass

    def add_edge(self, edge: EdgeWorkflow):
        pass

    def remove_node(self, node: KNode):
        pass

    def remove_edge(self, edge: EdgeWorkflow):
        pass

    # @property
    # def type(self) -> KNodeType:
    #     return KNodeType.WORKFLOW
