from abc import ABC, abstractmethod
from kproject.kevent import KEvent

class KManager(ABC):
    @abstractmethod
    def process_event(self, event: KEvent):
        pass
