"""
Workflow tab - interface for editing a specific workflow.
Matches the design of the homepage but with a workflow editor instead of the explorer.
"""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFrame
)
from PySide6.QtCore import Qt
from typing import Any

from .panels.workflow_editor_panel import WorkflowEditorPanel
from .panels.control_panel import ControlPanel
from .panels.preview_panel import PreviewPanel
from gui.kproject import KProject
from kira.knodes.kworkflow import KWorkflow


class WorkflowTab(QWidget):
    """
    Workflow tab containing:
    - Top-left: Workflow editor panel
    - Bottom-left: Control panel
    - Right: Preview panel
    """
    
    def __init__(self, project: KProject, workflow: KWorkflow, parent=None):
        super().__init__(parent)
        self.setObjectName("WorkflowTab")
        self._project = project
        self._workflow = workflow
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """Set up the UI layout."""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)  # External border
        main_layout.setSpacing(0)
        
        # Create splitter for resizable panels
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(main_splitter)
        
        # Left side: Editor and Control panels (vertical split)
        left_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Editor panel (top-left) - Replaces ExplorerPanel from Homepage
        self._editor_container = QFrame()
        self._editor_container.setObjectName("EditorContainer")
        editor_layout = QVBoxLayout(self._editor_container)
        editor_layout.setContentsMargins(0, 0, 1, 1)  # Half of internal separation
        editor_layout.setSpacing(0)
        
        self._editor_panel = WorkflowEditorPanel(self._workflow)
        editor_layout.addWidget(self._editor_panel)
        left_splitter.addWidget(self._editor_container)
        
        # Control panel (bottom-left)
        self._control_container = QFrame()
        self._control_container.setObjectName("ControlContainer")
        control_layout = QVBoxLayout(self._control_container)
        control_layout.setContentsMargins(0, 1, 1, 0)  # Half of internal separation
        control_layout.setSpacing(0)
        
        self._control_panel = ControlPanel()
        control_layout.addWidget(self._control_panel)
        left_splitter.addWidget(self._control_container)
        
        # Set splitter proportions
        left_splitter.setSizes([300, 150])
        
        # Preview panel (right)
        self._preview_container = QFrame()
        self._preview_container.setObjectName("PreviewContainer")
        preview_layout = QVBoxLayout(self._preview_container)
        preview_layout.setContentsMargins(1, 0, 0, 0)  # Half of internal separation
        preview_layout.setSpacing(0)
        
        self._preview_panel = PreviewPanel()
        preview_layout.addWidget(self._preview_panel)
        
        # Add to main splitter
        main_splitter.addWidget(left_splitter)
        main_splitter.addWidget(self._preview_container)
        
        # Set main splitter proportions
        main_splitter.setSizes([300, 700])
    
    def _connect_signals(self):
        """Connect signals between panels and project."""
        # Connect source clicking to preview
        self._control_panel.source_clicked.connect(self._on_source_clicked)
        
        # Connect project signals to panels
        self._project.message_logged.connect(self._control_panel.add_message)

    def _on_source_clicked(self, source: Any):
        """Handle when a source link is clicked in the control panel."""
        from kira.kdata.kdata import KData
        from kira.knodes.knode import KNode
        
        if isinstance(source, (KData, KNode)):
            # Show preview
            self._preview_panel.show_preview(source)
    
    @property
    def workflow(self) -> KWorkflow:
        """Get the workflow being edited."""
        return self._workflow
    
    @property
    def editor_panel(self) -> WorkflowEditorPanel:
        """Get the editor panel."""
        return self._editor_panel
    
    @property
    def control_panel(self) -> ControlPanel:
        """Get the control panel."""
        return self._control_panel
    
    @property
    def preview_panel(self) -> PreviewPanel:
        """Get the preview panel."""
        return self._preview_panel
