"""
Preview card widget - wraps a preview with a close button.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QSizePolicy, QLabel
)
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QFont, QMouseEvent, QCursor
from typing import Tuple, Optional

from ..previews.base_preview import BasePreview


class ClickableLabel(QLabel):
    """A QLabel that emits a clicked signal when clicked."""
    clicked = Signal()
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class ResizeHandle(QWidget):
    """A resize handle widget for resizing preview cards."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(6)
        self.setCursor(Qt.CursorShape.SizeVerCursor)
        self.setStyleSheet("""
            ResizeHandle {
                background-color: transparent;
                border-top: 1px solid transparent;
            }
            ResizeHandle:hover {
                background-color: #f0f0f0;
                border-top: 1px solid #d0d0d0;
            }
        """)
        self._mouse_press_pos: Optional[QPoint] = None
        self._initial_height: Optional[int] = None
        self._parent_card: Optional[QWidget] = None
    
    def _find_parent_card(self) -> Optional[QWidget]:
        """Find the PreviewCard parent widget."""
        if self._parent_card:
            return self._parent_card
        parent = self.parent()
        while parent:
            # Check if it's a QFrame with the right object name or has the preview property
            if isinstance(parent, QFrame) and hasattr(parent, '_preview'):
                self._parent_card = parent
                return parent
            parent = parent.parent()
        return None
    
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._mouse_press_pos = event.globalPosition().toPoint()
            parent_card = self._find_parent_card()
            if parent_card:
                self._initial_height = parent_card.height()
                # Grab mouse to track movement even outside the widget
                self.grabMouse()
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        if self._mouse_press_pos is not None and self._initial_height is not None:
            # Calculate height change
            delta = event.globalPosition().toPoint().y() - self._mouse_press_pos.y()
            new_height = max(200, self._initial_height + delta)  # Minimum 200px
            
            parent_card = self._find_parent_card()
            if parent_card:
                parent_card.setFixedHeight(new_height)
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        if self._mouse_press_pos is not None:
            # Release mouse grab
            self.releaseMouse()
        self._mouse_press_pos = None
        self._initial_height = None
        super().mouseReleaseEvent(event)


class PreviewCard(QFrame):
    """
    A card widget that wraps a preview with a close button in the top right corner.
    """
    
    # Signal emitted when the close button is clicked
    close_requested = Signal(object)  # Emits the preview card itself
    # Signal emitted when the minimize button is clicked
    minimize_toggled = Signal(bool)  # Emits True if minimized, False otherwise
    
    def __init__(self, preview: BasePreview, element_name: str = "Preview", element_type: str = "unknown", parent=None):
        super().__init__(parent)
        self._preview = preview
        self._element_name = element_name
        self._element_type = element_type
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI with close button."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header with title and close button
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(12, 10, 10, 10)
        header_layout.setSpacing(8)
        
        # Get type icon and color
        type_icon, header_color = self._get_type_style(self._element_type)
        
        # Icon label
        icon_label = QLabel(type_icon)
        icon_label.setStyleSheet("font-size: 18px;")
        header_layout.addWidget(icon_label)
        
        # Title label (bigger)
        title_label = QLabel(self._element_name)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333333;")
        header_layout.addWidget(title_label)
        
        # Minimize button (clickable QLabel)
        header_layout.addStretch()
        self._is_minimized = False
        self._minimize_button = ClickableLabel("−")
        self._minimize_button.setFixedSize(30, 30)
        self._minimize_button.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        self._minimize_button.setToolTip("Minimize preview")
        self._minimize_button.setStyleSheet("""
            QLabel {
                color: #999999;
                font-size: 18px;
                font-weight: normal;
                padding: 0px;
                background-color: transparent;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
            }
            QLabel:hover {
                color: #ffffff;
                background-color: #0078d4;
                border-color: #0078d4;
            }
        """)
        self._minimize_button.clicked.connect(self._toggle_minimize)
        header_layout.addWidget(self._minimize_button)
        
        # Close button (clickable QLabel) - minimal and modern
        self._close_button = ClickableLabel("×")
        self._close_button.setFixedSize(30, 30)
        self._close_button.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        self._close_button.setToolTip("Close preview")
        self._close_button.setStyleSheet("""
            QLabel {
                color: #999999;
                font-size: 18px;
                font-weight: normal;
                padding: 0px;
                background-color: transparent;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
            }
            QLabel:hover {
                color: #ffffff;
                background-color: #d13438;
                border-color: #d13438;
            }
        """)
        self._close_button.clicked.connect(lambda: self.close_requested.emit(self))
        header_layout.addWidget(self._close_button)
        
        # Create header widget with color-coded background
        header_widget = QWidget()
        header_widget.setLayout(header_layout)
        header_widget.setFixedHeight(45)
        # Use the color determined by element type (no bottom border)
        header_widget.setStyleSheet(f"background-color: {header_color};")
        
        main_layout.addWidget(header_widget)
        
        # Add a placeholder for when the card is minimized
        self._minimized_placeholder = QFrame()
        self._minimized_placeholder.setFixedHeight(15)
        self._minimized_placeholder.setStyleSheet("""
            QFrame {
                background-color: #f0f0f0;
                border-top: 1px solid #e0e0e0;
                border-bottom: 1px solid #e0e0e0;
            }
        """)
        self._minimized_placeholder.hide()  # Hidden by default
        main_layout.addWidget(self._minimized_placeholder)
        
        # Add the preview widget
        main_layout.addWidget(self._preview)
        
        # Add resize handle at the bottom
        self._resize_handle = ResizeHandle(self)
        main_layout.addWidget(self._resize_handle)
        
        # Style the card
        self.setStyleSheet("""
            PreviewCard {
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                background-color: white;
            }
        """)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Plain)  # No shadow
        
        # Set minimum height for preview cards
        self.setMinimumHeight(200)
        # Allow manual resizing (user can resize via handle)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    
    def _get_type_style(self, element_type: str) -> Tuple[str, str]:
        """
        Get the icon and header color for an element type.
        
        Args:
            element_type: The type string (table, literal, node, etc.)
            
        Returns:
            Tuple of (icon_emoji, header_color_hex)
        """
        type_styles = {
            "table": ("📊", "#e8f5e9"),      # Light green
            "literal": ("🔢", "#fff3e0"),    # Light orange
            "data": ("📦", "#e3f2fd"),       # Light blue
            "node": ("⚙️", "#f3e5f5"),       # Light purple
            "error": ("❌", "#ffebee"),       # Light red
            "unknown": ("❓", "#f9f9f9")      # Light grey (default)
        }
        return type_styles.get(element_type, type_styles["unknown"])

    def _toggle_minimize(self):
        """Toggle the minimized state of the card."""
        self._is_minimized = not self._is_minimized
        
        if self._is_minimized:
            self._preview.hide()
            self._resize_handle.hide()
            self._minimized_placeholder.show()
            self._minimize_button.setText("+")
            self._minimize_button.setToolTip("Expand preview")
            # Store current size policy and set to fixed for minimized state
            self._old_size_policy = self.sizePolicy()
            self.setFixedHeight(60)  # Height of header (45) + placeholder (15)
        else:
            self._preview.show()
            self._resize_handle.show()
            self._minimized_placeholder.hide()
            self._minimize_button.setText("−")
            self._minimize_button.setToolTip("Minimize preview")
            # Restore size policy and allow expansion
            self.setMinimumHeight(200)
            self.setMaximumHeight(16777215) # QWIDGETSIZE_MAX
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            # Re-adjust height to fit content or previous size
            self.adjustSize()
            
        self.minimize_toggled.emit(self._is_minimized)
    
    @property
    def preview(self) -> BasePreview:
        """Get the wrapped preview widget."""
        return self._preview

