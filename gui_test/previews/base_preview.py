"""
Abstract base class for preview widgets.
"""

from abc import abstractmethod
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from typing import Any


class BasePreview(QWidget):
    """
    Abstract base class for all preview widgets.
    Each preview type should inherit from this and implement the update_preview method.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(10, 10, 5, 5)
        self._layout.setSpacing(10)
        
        # Title label (hidden by default - shown in card header instead)
        self._title_label = QLabel("Preview")
        self._title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333333;")
        self._title_label.hide()  # Hide since title is shown in PreviewCard header
        self._layout.addWidget(self._title_label)
        
        # Content area (to be populated by subclasses)
        self._content_widget = None
        
    def set_title(self, title: str):
        """Set the preview title."""
        self._title_label.setText(title)
    
    @abstractmethod
    def update_preview(self, element):
        """
        Update the preview with the given element.
        
        Args:
            element: The element to preview (KData, KNode, etc.)
        """
        pass
    
    @abstractmethod
    def can_preview(self, element) -> bool:
        """
        Check if this preview widget can handle the given element.
        
        Args:
            element: The element to check
            
        Returns:
            True if this preview can handle the element, False otherwise
        """
        pass

