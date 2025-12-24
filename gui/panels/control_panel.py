"""
Control panel - displays error messages and other information.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTextBrowser, QLabel, QFrame
)
from PySide6.QtCore import Qt, Signal
from typing import List, Optional, Any
from datetime import datetime


class ControlPanel(QFrame):
    """
    Bottom-left panel showing error messages, execution logs, and other information.
    """
    
    # Signal emitted when a source link is clicked: (source_object)
    source_clicked = Signal(object)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ControlPanel")
        self._sources = {} # Map anchor names to objects
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Title
        title = QLabel("Control Panel")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #333333; padding: 5px;")
        layout.addWidget(title)
        
        # Tabs or sections for different types of messages
        # For now, we'll use a single text area
        self._text_area = QTextBrowser()
        self._text_area.setReadOnly(True)
        self._text_area.setOpenExternalLinks(False)
        self._text_area.anchorClicked.connect(self._on_anchor_clicked)
        self._text_area.setPlaceholderText("No messages yet...")
        self._text_area.setStyleSheet("""
            QTextBrowser {
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                background-color: #fafafa;
            }
        """)
        layout.addWidget(self._text_area)

    def _on_anchor_clicked(self, url):
        """Handle click on source link."""
        anchor = url.toString()
        if anchor in self._sources:
            self.source_clicked.emit(self._sources[anchor])
    
    def add_message(self, message: str, message_type: str = "info", source: Optional[Any] = None):
        """
        Add a message to the control panel.
        
        Args:
            message: The message text
            message_type: Type of message ('info', 'error', 'warning', 'success')
            source: Optional object that caused the message
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Color coding based on type
        color_map = {
            "info": "#333333",
            "error": "#d13438",
            "warning": "#ffaa00",
            "success": "#107c10"
        }
        color = color_map.get(message_type, "#333333")
        
        source_link = ""
        if source:
            from kira.core.kobject import KObject
            source_name = source.name if isinstance(source, KObject) else str(source)
            anchor_id = f"source_{len(self._sources)}"
            self._sources[anchor_id] = source
            source_link = f' <a href="{anchor_id}" style="color: #0078d4; text-decoration: none;">[Go to {source_name}]</a>'
        
        # Format message
        formatted_message = f'<span style="color: {color};">[{timestamp}] [{message_type.upper()}] {message}{source_link}</span><br>'
        
        # Append to text area
        self._text_area.append(formatted_message)
        
        # Auto-scroll to bottom
        scrollbar = self._text_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def add_error(self, error: Exception, context: Optional[str] = None):
        """
        Add an error message to the control panel.
        
        Args:
            error: The exception object
            context: Optional context information
        """
        error_msg = str(error)
        if context:
            error_msg = f"{context}: {error_msg}"
        self.add_message(error_msg, "error")
    
    def clear_messages(self):
        """Clear all messages from the control panel."""
        self._text_area.clear()
    
    def get_messages(self) -> str:
        """Get all messages as plain text."""
        return self._text_area.toPlainText()

