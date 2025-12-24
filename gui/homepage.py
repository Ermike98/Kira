"""
Homepage tab - the main interface with explorer, control panel, and preview.
"""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFrame
)
from PySide6.QtCore import Qt, Signal
from typing import Any

from .panels.explorer_panel import ExplorerPanel
from .panels.control_panel import ControlPanel
from .panels.preview_panel import PreviewPanel
from gui.kproject import KProject


class HomepageTab(QWidget):
    """
    Homepage tab containing:
    - Top-left: Explorer panel
    - Bottom-left: Control panel
    - Right: Preview panel
    """
    
    # Signal emitted when a workflow should be opened in a new tab
    workflow_opened = Signal(object)
    
    def __init__(self, project: KProject, parent=None):
        super().__init__(parent)
        self.setObjectName("HomepageTab")
        self._project = project
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
        
        # Left side: Explorer and Control panels (vertical split)
        left_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Explorer panel (top-left)
        self._explorer_container = QFrame()
        self._explorer_container.setObjectName("ExplorerContainer")
        explorer_layout = QVBoxLayout(self._explorer_container)
        explorer_layout.setContentsMargins(0, 0, 1, 1)  # Half of internal separation
        explorer_layout.setSpacing(0)
        
        self._explorer_panel = ExplorerPanel()
        explorer_layout.addWidget(self._explorer_panel)
        left_splitter.addWidget(self._explorer_container)
        
        # Control panel (bottom-left)
        self._control_container = QFrame()
        self._control_container.setObjectName("ControlContainer")
        control_layout = QVBoxLayout(self._control_container)
        control_layout.setContentsMargins(0, 1, 1, 0)  # Half of internal separation
        control_layout.setSpacing(0)
        
        self._control_panel = ControlPanel()
        control_layout.addWidget(self._control_panel)
        left_splitter.addWidget(self._control_container)
        
        # Set splitter proportions (explorer takes more space)
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
        
        # Set main splitter proportions (left side smaller, preview larger)
        main_splitter.setSizes([300, 700])
    
    def _connect_signals(self):
        """Connect signals between panels and project."""
        # When an element is selected in explorer, show its preview
        self._explorer_panel.element_selected.connect(self._preview_panel.show_preview)
        
        # When a workflow is requested to be opened
        self._explorer_panel.workflow_opened.connect(self.workflow_opened.emit)
        
        # When an element is requested to be deleted in explorer, remove it from project
        self._explorer_panel.element_deleted.connect(self._on_element_deleted)
        
        # Connect undo/redo signals
        self._explorer_panel.undo_requested.connect(self._project.undo)
        self._explorer_panel.redo_requested.connect(self._project.redo)
        
        # Connect source clicking to preview (and potentially selecting in explorer)
        self._control_panel.source_clicked.connect(self._on_source_clicked)
        
        # Connect project signals to panels
        self._project.data_added.connect(self._explorer_panel.add_element)
        self._project.data_removed.connect(self._explorer_panel.remove_element)
        self._project.workflow_added.connect(self._explorer_panel.add_element)
        self._project.workflow_removed.connect(self._explorer_panel.remove_element)
        self._project.message_logged.connect(self._control_panel.add_message)
        
        # Initial population
        for data in self._project.get_all_data():
            self._explorer_panel.add_element(data)
        for workflow in self._project.get_workflows():
            self._explorer_panel.add_element(workflow)

    def _on_element_deleted(self, element: Any):
        """Handle when an element is deleted in the explorer."""
        from kira.kdata.kdata import KData
        if isinstance(element, KData):
            self._project.remove_data(element.name)
        else:
            # Handle other types if necessary
            self._project.log(f"Cannot delete element of type {type(element)}", "warning")

    def _on_source_clicked(self, source: Any):
        """Handle when a source link is clicked in the control panel."""
        from kira.kdata.kdata import KData
        from kira.knodes.knode import KNode
        
        if isinstance(source, (KData, KNode)):
            # Show preview
            self._preview_panel.show_preview(source)
            # You might also want to scroll to/highlight it in the explorer, 
            # but for now preview is the main 'jump' target.
    
    @property
    def explorer_panel(self) -> ExplorerPanel:
        """Get the explorer panel."""
        return self._explorer_panel
    
    @property
    def control_panel(self) -> ControlPanel:
        """Get the control panel."""
        return self._control_panel
    
    @property
    def preview_panel(self) -> PreviewPanel:
        """Get the preview panel."""
        return self._preview_panel

