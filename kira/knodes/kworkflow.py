from typing import NamedTuple

from graphlib import TopologicalSorter, CycleError

from kira.core.kcontext import KContext
from kira.kdata.kdata import KData, KDataValue
from kira.core.kobject import KTypeInfo
from kira.kdata.kerrorvalue import KErrorValue
from kira.kexpections.kgenericexception import KGenericException
from kira.knodes.knode import KNode, KNodeType, KNodeInstance


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
                 nodes: list[KNodeInstance] = None,
                 edges: list[EdgeWorkflow] = None):
        super().__init__(name, inputs, outputs)
        self._nodes: list[KNodeInstance] = nodes if nodes is not None else []
        self._edges: list[EdgeWorkflow] = edges if edges is not None else []

    def _init_graph(self):
        graph = {node: set() for node in self._nodes}
        # node_input_map: KNodeInstance -> { input_name: context_key }
        node_input_map  = {node: {} for node in self._nodes}
        # workflow_output_map: output_name -> context_key
        workflow_output_map  = {}

        for edge in self._edges:
            # Prepare the context key: "NodeName.KDataName" or just "KDataName" if from workflow input
            context_key = edge.from_name if edge.from_node is None else f"{edge.from_node.name}.{edge.from_name}"

            if edge.to_node is not None:
                # Track dependency for TopologicalSorter
                if edge.from_node is not None:
                    graph[edge.to_node].add(edge.from_node)
                # Map node input to its source in the context
                node_input_map[edge.to_node][edge.to_name] = context_key
            else:
                # Map workflow-level output to its source in the context
                workflow_output_map[edge.to_name] = context_key

        return graph, node_input_map, workflow_output_map

    def call(self, inputs: list[KData]) -> list[KDataValue]:
        ctx = KContext()

        # 1. Register workflow inputs into context using their intrinsic names
        for data in inputs:
            ctx.register_object(data)

        graph, input_map, output_map = self._init_graph()
        ts = TopologicalSorter(graph)
        try:
            topological_order = list(ts.static_order())
        except CycleError:
            return [KErrorValue(KGenericException(
                "The workflow contains a cycle and cannot be executed."))] * len(self._outputs_names)

        # 2. Execute nodes in the topological order
        for node_instance in topological_order:
            # Retrieve context keys from our pre-built input map
            node_inputs = {
                name: ctx.get_object(ctx_key)
                for name, ctx_key in input_map[node_instance].items()
            }

            # Execute the node instance and register its KResult in context
            result = node_instance(node_inputs)
            ctx.register_object(result)

        # 3. Collect final workflow outputs using the pre-built output map
        workflow_results = []
        for out_name in self._outputs_names:
            ctx_key = output_map.get(out_name)
            if ctx_key:
                val = ctx.get_object(ctx_key)

                # Extract KDataValue from KData
                assert isinstance(val, KData), f"Output {out_name} is not a KData."

                if val:
                    workflow_results.append(val.value)
                else:
                    workflow_results.append(KErrorValue(val.error))

            else:
                workflow_results.append(KErrorValue(KGenericException(f"Output {out_name} is not connected.")))

        return workflow_results

    def add_node(self, node: KNode):
        pass

    def add_edge(self, edge: EdgeWorkflow):
        pass

    def remove_node(self, node: KNode):
        pass

    def remove_edge(self, edge: EdgeWorkflow):
        pass

    @property
    def type(self) -> KNodeType:
        return KNodeType.WORKFLOW
