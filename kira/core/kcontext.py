from __future__ import annotations
from kira.core.kobject import KObject
from kira.core.kresult import KResult
from kira.kexpections.kgenericexception import KGenericException


class KContext:
    def __init__(self, parent: KContext | None = None):
        self._parent = parent
        self._objects = {}

    def register_object(self, obj: KObject):

        self._objects[obj.name] = obj

        if isinstance(obj, KResult):
            for i in obj.results:
                name = f"{obj.name}.{i.name}"
                self._objects[name] = i

        return self

    def get_object(self, name: str) -> KObject:
        if name not in self._objects:
            if self._parent is not None:
                return self._parent.get_object(name)

            return KGenericException(f"Object '{name}' not found in context")

        return self._objects[name]
