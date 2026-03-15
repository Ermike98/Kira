from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, QWidget
from PySide6.QtCore import Qt

class TransformationsPanel(QFrame):
    """
    Panel to display the history of transformations applied to the table.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TransformationsPanel")
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QWidget()
        header.setFixedHeight(40)
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(10, 0, 10, 0)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        title = QLabel("Transformations")
        title.setStyleSheet("font-weight: bold; font-size: 14px; color: #333;")
        header_layout.addWidget(title)
        
        # List of transformations
        self._list_widget = QListWidget()
        self._list_widget.setFrameShape(QFrame.Shape.NoFrame)
        self._list_widget.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                outline: none;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f0f0f0;
            }
            QListWidget::item:selected {
                background-color: #e8f5e9;
                color: #333;
            }
        """)
        
        # Add initial item
        self.add_transformation("Original Data", "Loaded from source")
        
        layout.addWidget(header)
        layout.addWidget(self._list_widget)
        
        # Styling for this frame (Rounded, White)
        self.setStyleSheet("""
            QFrame#TransformationsPanel {
                background-color: white;
                border-radius: 8px;
            }
        """)

    def add_transformation(self, title: str, description: str = ""):
        """Add a new transformation to the list."""
        item = QListWidgetItem()
        
        # Create a custom widget for the item
        widget = QWidget()
        w_layout = QVBoxLayout(widget)
        w_layout.setContentsMargins(5, 5, 5, 5)
        w_layout.setSpacing(2)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: 600; font-size: 13px;")
        
        desc_label = QLabel(description)
        desc_label.setStyleSheet("color: #666; font-size: 11px;")
        
        w_layout.addWidget(title_label)
        w_layout.addWidget(desc_label)
        
        item.setSizeHint(widget.sizeHint())
        
        self._list_widget.addItem(item)
        self._list_widget.setItemWidget(item, widget)
