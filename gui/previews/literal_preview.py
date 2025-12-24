"""
Preview widget for KLiteral data.
"""

from PySide6.QtWidgets import QLabel, QVBoxLayout
from PySide6.QtCore import Qt
from kira.kdata.kdata import KData, KDataType
from kira.kdata.kliteral import KLiteral
from .base_preview import BasePreview
from typing import Any


class LiteralPreview(BasePreview):
    """Preview widget for KLiteral data."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._value_label = None
        self._type_label = None
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI components."""
        # Type label
        self._type_label = QLabel()
        self._type_label.setStyleSheet("color: #666666; font-size: 12px; font-style: italic;")
        self._layout.addWidget(self._type_label)
        
        # Value label
        self._value_label = QLabel()
        self._value_label.setStyleSheet("color: #333333; font-size: 14px; padding: 10px;")
        self._value_label.setWordWrap(True)
        self._value_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self._layout.addWidget(self._value_label)
        
        # Add stretch to push content to top
        self._layout.addStretch()
    
    def update_preview(self, element: KData):
        """Update the preview with KLiteral data."""
        if not isinstance(element, KData):
            self._type_label.setText("Invalid element type")
            return
        
        if element.value is None:
            self._type_label.setText("No data available (error occurred)")
            return
        
        if not isinstance(element.value, KLiteral):
            self._type_label.setText("Element is not a KLiteral")
            return
        
        # Get the literal value and type
        literal = element.value
        value = literal.value
        lit_type = literal.lit_type
        
        # Update labels
        self._type_label.setText(f"Type: {lit_type.name}")
        self._value_label.setText(f"Value: {repr(value)}")
        
        # Set title
        self.set_title(f"Literal: {element.name}")
    
    def can_preview(self, element: Any) -> bool:
        """Check if this preview can handle the element."""
        if not isinstance(element, KData):
            return False
        
        if element.value is None:
            return False
        
        return isinstance(element.value, KLiteral) or element.type.type == KDataType.LITERAL

