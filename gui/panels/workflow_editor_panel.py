"""
Workflow editor panel - a visual interface for editing workflows.
"""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from kira.knodes.kworkflow import KWorkflow

class WorkflowEditorPanel(QFrame):
    """
    Panel for visually editing a workflow.
    In a real implementation, this would be a node-based graph editor.
    For now, it's a placeholder showing the workflow name.
    """
    
    def __init__(self, workflow: KWorkflow, parent=None):
        super().__init__(parent)
        self.setObjectName("WorkflowEditorPanel")
        self._workflow = workflow
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title = QLabel(f"Workflow Editor: {self._workflow.name}")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #555555;")
        layout.addWidget(title)
        
        info = QLabel("Visual node-based editor coming soon...")
        info.setStyleSheet("font-size: 14px; color: #888888;")
        layout.addWidget(info)
        
        self.setStyleSheet("")

    @property
    def workflow(self) -> KWorkflow:
        return self._workflow
