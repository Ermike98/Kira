"""
Preview widget for KData elements with errors.
"""

from PySide6.QtWidgets import QLabel, QVBoxLayout, QFrame
from PySide6.QtCore import Qt
from kira.kdata.kdata import KData
from .base_preview import BasePreview
from typing import Any


class ErrorPreview(BasePreview):
    """Preview widget for KData elements with errors."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._error_label = None
        self._message_label = None
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI components."""
        # Error icon/title
        self._error_label = QLabel("⚠ Error")
        self._error_label.setStyleSheet("""
            color: #d13438;
            font-size: 18px;
            font-weight: bold;
            padding: 10px;
        """)
        self._layout.addWidget(self._error_label)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("color: #e0e0e0;")
        self._layout.addWidget(separator)
        
        # Error message
        self._message_label = QLabel()
        self._message_label.setStyleSheet("""
            color: #333333;
            font-size: 13px;
            padding: 10px;
            background-color: #ffebee;
            border-radius: 4px;
        """)
        self._message_label.setWordWrap(True)
        self._message_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self._layout.addWidget(self._message_label)
        
        # Add stretch
        self._layout.addStretch()
    
    def update_preview(self, element: KData):
        """Update the preview with error information."""
        if not isinstance(element, KData):
            self._message_label.setText("Invalid element type")
            return
        
        if element.error is None:
            self._message_label.setText("No error information available")
            return
        
        # Get error message
        error_message = str(element.error)
        
        # Update labels
        self._message_label.setText(f"Error: {error_message}")
        
        # Set title
        self.set_title(f"Error: {element.name}")
    
    def can_preview(self, element: Any) -> bool:
        """Check if this preview can handle the element."""
        if not isinstance(element, KData):
            return False
        
        # This preview handles KData elements with errors (value is None and error is not None)
        return element.value is None and element.error is not None

