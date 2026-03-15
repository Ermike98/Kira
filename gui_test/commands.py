from PySide6.QtGui import QUndoCommand
from kira.kdata.kdata import KData
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gui.kproject import KProject

class AddDataCommand(QUndoCommand):
    def __init__(self, project: 'KProject', data: KData):
        super().__init__(f"Add Data: {data.name}")
        self._project = project
        self._data = data

    def redo(self):
        self._project._data_store[self._data.name] = self._data
        self._project.data_added.emit(self._data)

    def undo(self):
        if self._data.name in self._project._data_store:
            del self._project._data_store[self._data.name]
            self._project.data_removed.emit(self._data)

class RemoveDataCommand(QUndoCommand):
    def __init__(self, project: 'KProject', data: KData):
        super().__init__(f"Remove Data: {data.name}")
        self._project = project
        self._data = data

    def redo(self):
        if self._data.name in self._project._data_store:
            del self._project._data_store[self._data.name]
            self._project.data_removed.emit(self._data)

    def undo(self):
        self._project._data_store[self._data.name] = self._data
        self._project.data_added.emit(self._data)
