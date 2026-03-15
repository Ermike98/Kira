from typing import List, Dict, Any, Optional
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QUndoStack
from kira.kdata.kdata import KData
from kira.knodes.knode import KNode
from kira.knodes.kworkflow import KWorkflow
from .commands import AddDataCommand, RemoveDataCommand

class KProject(QObject):
    """
    The central project manager that coordinates data, nodes, and workflows.
    It acts as the single source of truth and notifies observers (GUI) of changes.
    """
    
    # Signals to notify the GUI about changes
    data_added = Signal(KData)
    data_removed = Signal(KData)
    data_updated = Signal(KData)
    
    node_added = Signal(KNode)
    node_removed = Signal(KNode)
    
    workflow_added = Signal(KWorkflow)
    workflow_removed = Signal(KWorkflow)
    workflow_updated = Signal(KWorkflow)
    
    # Logging signal: (message, type, source_object)
    # source_object is an optional KObject that caused the message (e.g. for jumping to source)
    message_logged = Signal(str, str, object)

    def __init__(self, name: str = "New Project"):
        super().__init__()
        self._name = name
        self._data_store: Dict[str, KData] = {}
        self._nodes: List[KNode] = []
        self._workflows: List[KWorkflow] = []
        self._undo_stack = QUndoStack(self)

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value

    def add_data(self, data: KData):
        """Add a KData object to the project via undoable command."""
        self._undo_stack.push(AddDataCommand(self, data))

    def remove_data(self, name: str):
        """Remove a KData object by name via undoable command."""
        if name in self._data_store:
            data = self._data_store[name]
            self._undo_stack.push(RemoveDataCommand(self, data))

    def undo(self):
        """Undo the last action."""
        self._undo_stack.undo()

    def redo(self):
        """Redo the last undone action."""
        self._undo_stack.redo()

    def clear_undo_stack(self):
        """Clear the undo/redo stack."""
        self._undo_stack.clear()

    def can_undo(self) -> bool:
        return self._undo_stack.canUndo()

    def can_redo(self) -> bool:
        return self._undo_stack.canRedo()

    def get_all_data(self) -> List[KData]:
        """Return all KData objects in the project."""
        return list(self._data_store.values())

    def add_workflow(self, workflow: KWorkflow):
        """Add a workflow to the project."""
        self._workflows.append(workflow)
        self.workflow_added.emit(workflow)

    def get_workflows(self) -> List[KWorkflow]:
        """Return all workflows."""
        return self._workflows

    def log(self, message: str, message_type: str = "info", source: Optional[Any] = None):
        """Log a message and notify observers."""
        self.message_logged.emit(message, message_type, source)

    # Add more methods to manage nodes, execute workflows, etc.
