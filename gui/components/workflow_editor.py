from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QLineEdit
)
from PySide6.QtCore import Qt, Signal
from gui.components.node_editor import NodeScene, NodeView
from gui import style_system
from gui.utils import colors

class WorkflowEditor(QWidget):
    """
    Component for visually editing workflows.
    Replaces the previous text editor.
    """
    save_requested = Signal(str, str)  # (name, code)
    
    def __init__(self, project, parent=None):
        super().__init__(parent)
        self.project = project
        self._current_name = ""
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Toolbar
        self.toolbar = QFrame()
        self.toolbar.setFixedHeight(45)
        self.toolbar.setStyleSheet(f"background-color: {colors.slate_50}; border-bottom: {style_system.border_thin} solid {colors.slate_200};")
        tool_layout = QHBoxLayout(self.toolbar)
        tool_layout.setContentsMargins(15, 0, 15, 0)
        
        self.title_label = QLabel("New Workflow")
        self.title_label.setStyleSheet(f"font-weight: 600; color: {colors.slate_900}; font-size: {style_system.font_small};")
        tool_layout.addWidget(self.title_label)
        
        tool_layout.addStretch()
        
        self.save_btn = QPushButton("Save Workflow")
        self.save_btn.setObjectName("PrimaryButton")
        self.save_btn.clicked.connect(self._on_save_clicked)
        tool_layout.addWidget(self.save_btn)
        
        tool_layout.addSpacing(20)
        
        # Node Search in Toolbar
        self.add_node_search = QLineEdit()
        self.add_node_search.setPlaceholderText("Type to add node...")
        self.add_node_search.setFixedWidth(200)
        self.add_node_search.setStyleSheet(f"""
            QLineEdit {{
                padding: {style_system.spacing_xxsmall} {style_system.spacing_small};
                border: {style_system.border_thin} solid {colors.slate_200};
                border-radius: {style_system.radius_large};
                background: white;
                font-size: {style_system.font_small};
            }}
            QLineEdit:focus {{ border-color: {colors.sky_500}; }}
        """)
        self.add_node_search.returnPressed.connect(self._on_toolbar_add_node)
        tool_layout.addWidget(self.add_node_search)
        
        layout.addWidget(self.toolbar)
        
        # Node Canvas
        self.scene = NodeScene(self)
        self.view = NodeView(self.scene, self)
        layout.addWidget(self.view)

    def _on_toolbar_add_node(self):
        name = self.add_node_search.text().strip()
        if name:
            # Add to center of view
            view_rect = self.view.viewport().rect()
            center_pos = self.view.mapToScene(view_rect.center())
            self.view._create_node_from_name(name, center_pos, is_scene_pos=True)
            self.add_node_search.clear()

    def set_workflow(self, name: str, code: str):
        """Loads a workflow into the visual editor."""
        self._current_name = name
        self.title_label.setText(f"Workflow: {name}")
        self.scene.clear()
        self.view.boundaries = [] # Reset boundaries
        
        # Placeholder boundary items
        from gui.components.node_items import WorkflowBoundaryItem
        
        self.left_panel = WorkflowBoundaryItem(True, ["input_1", "input_2"])
        self.scene.addItem(self.left_panel)
        self.view.boundaries.append((self.left_panel, True))
        
        self.right_panel = WorkflowBoundaryItem(False, ["output_1"])
        self.scene.addItem(self.right_panel)
        self.view.boundaries.append((self.right_panel, False))
        
        # Trigger initial anchor
        self.view._update_boundaries()
        
        # TODO: Proper DSL parsing
        pass

    def _on_save_clicked(self):
        # TODO: Implement Graph-to-DSL generation
        code = "# Visual Workflow TODO"
        if self._current_name:
            self.save_requested.emit(self._current_name, code)
