from __future__ import annotations
from kira.core.kobject import KObject
from kira.kexpections.kgenericexception import KGenericException
from kira.kdata.kdata import KData
from kira.knodes.knode import KNode
from kira.library.node_library import KLibrary

class KContext:
    def __init__(self, parent: KContext | None = None):
        self._parent = parent
        self._objects = {}

    def register_object(self, obj: KObject):

        self._objects[obj.name] = obj

        # if isinstance(obj, KResult):
        #     for i in obj.results:
        #         name = f"{obj.name}.{i.name}"
        #         self._objects[name] = i

        return self

    def get_object(self, name: str) -> KObject:
        if name not in self._objects:
            if self._parent is not None:
                return self._parent.get_object(name)

            return KData(name, None, KGenericException(f"Object '{name}' not found in context"))

        return self._objects[name]

    def get_context_state(self) -> dict:
        state = {"node": [], "data": [], "library": []}
        for obj in self._objects.values():
            if isinstance(obj, KNode):
                state["node"].append(obj)
            elif isinstance(obj, KData):
                state["data"].append(obj)
            elif isinstance(obj, KLibrary):
                state["library"].append(obj)
        return state
