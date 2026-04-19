from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QTextEdit, QLabel
from PySide6.QtCore import Qt

class BottomPanel(QWidget):
    """
    Tabbed panel at the bottom of the main window.
    Contains Logs, Errors, Code preview, etc.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("BottomPanel")
        self.setFixedHeight(200)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.South) # Or North for VS code feel? VS code has it at top of panel
        self.tabs.setDocumentMode(True)
        
        # Logs Tab
        self.log_widget = QTextEdit()
        self.log_widget.setReadOnly(True)
        self.log_widget.setPlaceholderText("No logs yet...")
        self.tabs.addTab(self.log_widget, "OUTPUT")
        
        # Errors Tab
        self.error_widget = QTextEdit()
        self.error_widget.setReadOnly(True)
        self.error_widget.setPlaceholderText("No errors reported.")
        self.tabs.addTab(self.error_widget, "ERRORS")
        
        # Terminal Tab (Placeholder)
        self.terminal_widget = QTextEdit()
        from gui.utils import colors
        from gui import style_system
        self.terminal_widget.setStyleSheet(f"background-color: {colors.text_primary}; color: {colors.bg_base}; font-family: 'Consolas', monospace; font-size: {style_system.font_small};")
        self.tabs.addTab(self.terminal_widget, "TERMINAL")
        
        layout.addWidget(self.tabs)

    def log(self, message: str, level: str = "info"):
        self.log_widget.append(f"[{level.upper()}] {message}")
        
    def log_error(self, message: str):
        self.error_widget.append(f"[ERROR] {message}")
        self.tabs.setCurrentWidget(self.error_widget)
