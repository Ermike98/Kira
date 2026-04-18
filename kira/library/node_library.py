from typing import TYPE_CHECKING
from kira.core.kobject import KObject, KTypeInfo
from kira.ktypeinfo.no_type import KNoTypeInfo

if TYPE_CHECKING:
    from kira.core.kcontext import KContext

class KLibrary(KObject):
    def __init__(self, name: str, objs: list[KObject] = None):
        super().__init__(name)
        self._library = {obj.name: obj for obj in objs} if objs is not None else {}

    def register(self, node: KObject):
        self._library[node.name] = node

    def get(self, name:str) -> KObject | None:
        if name not in self._library:
            return None
        return self._library[name]

    @property
    def type(self) -> KTypeInfo:
        return KNoTypeInfo()

    def eval(self, context: 'KContext') -> KObject:
        print(f"Loading library '{self.name}'")
        context.register_object(self)
        for obj in self._library.values():
            print(f"Registering object '{obj.name}'")
            context.register_object(obj)
        return self

