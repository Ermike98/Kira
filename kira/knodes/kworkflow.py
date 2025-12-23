from typing import NamedTuple

from kira.kdata.kdata import KData, KTypeInfo
from kira.knodes.knode import KNode, KNodeType

class EdgeWorkflow(NamedTuple):
    from_node: KNode
    from_name: str
    to_node: KNode
    to_name: str

class KWorkflow(KNode):
    def __init__(self,
                 name: str,
                 inputs: list[tuple[str, KTypeInfo] | str],
                 outputs: list[tuple[str, KTypeInfo] | str],
                 nodes: list[KNode] = None,
                 edges: list[EdgeWorkflow] = None):
        super().__init__(name, inputs, outputs)
        self._nodes = nodes if nodes is not None else []
        self._edges = edges if edges is not None else []

    def call(self, inputs: list[KData]) -> list[KData]:
        pass

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

