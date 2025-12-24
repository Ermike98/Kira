"""
Preview widget for KNode elements (functions, workflows).
"""

from PySide6.QtWidgets import QLabel, QVBoxLayout, QFrame
from PySide6.QtCore import Qt
from kira.knodes.knode import KNode
from .base_preview import BasePreview
from typing import Any


class NodePreview(BasePreview):
    """Preview widget for KNode elements."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._info_label = None
        self._inputs_label = None
        self._outputs_label = None
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI components."""
        # Info label
        self._info_label = QLabel()
        self._info_label.setStyleSheet("color: #666666; font-size: 12px;")
        self._layout.addWidget(self._info_label)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("color: #d0d0d0;")
        self._layout.addWidget(separator)
        
        # Inputs label
        inputs_title = QLabel("Inputs:")
        inputs_title.setStyleSheet("font-weight: bold; color: #333333; font-size: 13px;")
        self._layout.addWidget(inputs_title)
        
        self._inputs_label = QLabel()
        self._inputs_label.setStyleSheet("color: #333333; font-size: 12px; padding: 5px;")
        self._inputs_label.setWordWrap(True)
        self._layout.addWidget(self._inputs_label)
        
        # Separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.HLine)
        separator2.setFrameShadow(QFrame.Shadow.Sunken)
        separator2.setStyleSheet("color: #d0d0d0;")
        self._layout.addWidget(separator2)
        
        # Outputs label
        outputs_title = QLabel("Outputs:")
        outputs_title.setStyleSheet("font-weight: bold; color: #333333; font-size: 13px;")
        self._layout.addWidget(outputs_title)
        
        self._outputs_label = QLabel()
        self._outputs_label.setStyleSheet("color: #333333; font-size: 12px; padding: 5px;")
        self._outputs_label.setWordWrap(True)
        self._layout.addWidget(self._outputs_label)
        
        # Add stretch
        self._layout.addStretch()
    
    def update_preview(self, element: KNode):
        """Update the preview with KNode data."""
        if not isinstance(element, KNode):
            self._info_label.setText("Invalid element type")
            return
        
        # Get node information
        node_type = element.__class__.__name__
        self._info_label.setText(f"Node Type: {node_type}")
        
        # Format inputs
        inputs_text = []
        for name, type_info in zip(element.input_names, element.input_types):
            type_str = type_info.type.name
            inputs_text.append(f"  • {name}: {type_str}")
        self._inputs_label.setText("\n".join(inputs_text) if inputs_text else "  (no inputs)")
        
        # Format outputs
        outputs_text = []
        for name, type_info in zip(element.output_names, element.output_types):
            type_str = type_info.type.name
            outputs_text.append(f"  • {name}: {type_str}")
        self._outputs_label.setText("\n".join(outputs_text) if outputs_text else "  (no outputs)")
        
        # Set title
        self.set_title(f"Node: {element.name}")
    
    def can_preview(self, element: Any) -> bool:
        """Check if this preview can handle the element."""
        return isinstance(element, KNode)

