from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import hashlib


class KEventTypes(str, Enum):
    AddVariable = "AddVariable"
    AddData = "AddData"
    AddWorkflow = "AddWorkflow"
    DeleteVariable = "DeleteVariable"
    DeleteData = "DeleteData"
    DeleteWorkflow = "DeleteWorkflow"
    UpdateWorkflow = "UpdateWorkflow"

@dataclass
class KEvent:
    author: str
    timestamp: datetime
    type: KEventTypes
    target: str
    body: str = ""
    event_id: str = field(init=False)

    def __post_init__(self):
        # Compute event_id once at construction
        hasher = hashlib.sha256()
        hasher.update(self.author.encode())
        hasher.update(self.timestamp.isoformat().encode())
        hasher.update(self.type.encode())
        hasher.update(self.target.encode())
        hasher.update(self.body.encode())
        self.event_id = hasher.hexdigest()

"""
match event.type:
    case KEventTypes.AddVariable:
        pass
    case KEventTypes.AddData:
        pass
    case KEventTypes.AddWorkflow:
        pass
    case KEventTypes.DeleteVariable:
        pass
    case KEventTypes.DeleteData:
        pass
    case KEventTypes.DeleteWorkflow:
        pass
    case KEventTypes.UpdateWorkflow:
        pass
    case KEventTypes.Store:
        pass
    case _ as v:
        raise TypeError(f"Unhandled event type: {v}")
"""
