from kira.core.kobject import KObject, KObjectType
from kira.core.kresult import KResult
from kira.kdata.kdata import KData
from kira.kexpections.kgenericexception import KGenericException


class KContext:
    def __init__(self):
        self._objects = {}

    def register_object(self, obj: KObject):

        self._objects[obj.name] = obj

        if obj.type != KObjectType.KRESULT:
            return self

        # If obj is a KResult store also the individual KData objects
        assert isinstance(obj, KResult), "KResult must be a KResult object"

        for i in obj.results:
            name = f"{obj.name}.{i.name}"
            self._objects[name] = i

        return self

    def get_object(self, name: str) -> KObject:
        if name not in self._objects:
            return KData(name, None, KGenericException(f"Object '{name}' not found in context"))

        return self._objects[name]
