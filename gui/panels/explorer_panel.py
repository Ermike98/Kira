"""
Explorer panel - displays all elements in the project as clickable buttons.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QFrame, QPushButton, QLabel, QGridLayout,
    QHBoxLayout, QMenu
)
from PySide6.QtCore import Qt, Signal, QEvent, QTimer, QPoint
from PySide6.QtGui import QFontMetrics, QAction
from typing import List, Any, Optional


class ExplorerButton(QPushButton):
    """Custom button for explorer elements that supports double-click."""
    doubleClicked = Signal()

    def mouseDoubleClickEvent(self, event):
        self.doubleClicked.emit()
        super().mouseDoubleClickEvent(event)

class ExplorerPanel(QFrame):
    """
    Top-left panel showing all project elements (data, nodes, charts, etc.).
    Each element is displayed as a button that can be clicked to show its preview.
    """
    
    # Signal emitted when an element is selected
    element_selected = Signal(object)  # Emits the selected element
    # Signal emitted when an element is double clicked
    element_double_clicked = Signal(object)  # Emits the double clicked element
    # Signal emitted when a workflow should be opened in a new tab
    workflow_opened = Signal(object)  # Emits the KWorkflow to open
    # Signal emitted when an element should be deleted
    element_deleted = Signal(object)  # Emits the element to delete
    # Signals for undo/redo requests
    undo_requested = Signal()
    redo_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ExplorerPanel")
        self._elements: List[Any] = []
        self._selected_element: Optional[Any] = None
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Title
        title = QLabel("Explorer")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #333333; padding: 5px;")
        layout.addWidget(title)
        
        # Scroll area for element buttons
        scroll_area = QScrollArea()
        scroll_area.setObjectName("ExplorerScrollArea")
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        # Container widget for buttons - using grid layout
        self._container = QWidget()
        self._container.setObjectName("ExplorerContainer")
        self._container_layout = QGridLayout(self._container)
        self._container_layout.setContentsMargins(0, 0, 0, 50)  # Bottom margin for floating toolbar
        self._container_layout.setSpacing(12)
        self._container_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Track grid position and button widgets
        self._grid_row = 0
        self._grid_col = 0
        self._button_widgets: List[QWidget] = []  # Store all button widgets for rebuilding
        self._button_widget_width = 80  # Width of each button widget
        self._grid_spacing = 12  # Spacing between buttons
        self._grid_margins = 20  # Total horizontal margins (10 on each side)
        self._columns_per_row = self._calculate_columns()
        
        scroll_area.setWidget(self._container)
        layout.addWidget(scroll_area)
        
        # Floating Toolbar at the bottom center
        self._toolbar_container = QFrame(self)
        self._toolbar_container.setObjectName("FloatingToolbar")
        self._toolbar_container.setStyleSheet("""
            QFrame#FloatingToolbar {
                background-color: rgba(255, 255, 255, 0.9);
                border: 1px solid #d0d0d0;
                border-radius: 20px;
            }
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 16px;
                text-align: center;
                padding: 0;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 0.05);
            }
        """)
        
        toolbar_layout = QHBoxLayout(self._toolbar_container)
        toolbar_layout.setContentsMargins(10, 4, 10, 4)
        toolbar_layout.setSpacing(10)
        
        # Add button with menu
        self._add_button = QPushButton("➕")
        self._add_button.setFixedSize(32, 32)
        self._add_button.setToolTip("Add new element")
        self._add_button.clicked.connect(self._on_add_clicked)
        
        self._add_menu = QMenu(self)
        self._add_menu.addAction(self._get_type_prefix("data") + " Data", lambda: print("Add Data clicked"))
        self._add_menu.addAction(self._get_type_prefix("workflow") + " Workflow", lambda: print("Add Workflow clicked"))
        self._add_menu.addAction(self._get_type_prefix("chart") + " Chart", lambda: print("Add Chart clicked"))
        
        # Save button
        self._save_button = QPushButton("💾")
        self._save_button.setFixedSize(32, 32)
        self._save_button.setToolTip("Save project")
        # Save does nothing for now
        
        # Undo button
        self._undo_button = QPushButton("↩️")
        self._undo_button.setFixedSize(32, 32)
        self._undo_button.setToolTip("Undo (Ctrl+Z)")
        self._undo_button.clicked.connect(self.undo_requested.emit)
        
        # Redo button
        self._redo_button = QPushButton("↪️")
        self._redo_button.setFixedSize(32, 32)
        self._redo_button.setToolTip("Redo (Ctrl+Y)")
        self._redo_button.clicked.connect(self.redo_requested.emit)
        
        # Delete button
        self._delete_button = QPushButton("🗑️")
        self._delete_button.setFixedSize(32, 32)
        self._delete_button.setToolTip("Delete selected element")
        self._delete_button.clicked.connect(self._on_delete_clicked)
        
        toolbar_layout.addWidget(self._add_button)
        toolbar_layout.addWidget(self._save_button)
        toolbar_layout.addWidget(self._undo_button)
        toolbar_layout.addWidget(self._redo_button)
        toolbar_layout.addWidget(self._delete_button)
        
        # Adjust size to fit content
        self._toolbar_container.adjustSize()
        
        # Install event filter to detect resize
        self.installEventFilter(self)
        
        # Rebuild grid after initial layout
        QTimer.singleShot(100, self._rebuild_grid)  # Delay to ensure layout is complete
        QTimer.singleShot(100, self._update_toolbar_position)
    
    def _update_toolbar_position(self):
        """Position the floating toolbar at the bottom center."""
        if not hasattr(self, '_toolbar_container'):
            return
            
        margin = 15
        x = (self.width() - self._toolbar_container.width()) // 2
        y = self.height() - self._toolbar_container.height() - margin
        self._toolbar_container.move(x, y)
        self._toolbar_container.raise_()
    
    def add_element(self, element: Any):
        """
        Add an element to the explorer.
        
        Args:
            element: The element to add (KData, KNode, etc.)
        """
        if element in self._elements:
            return
        
        self._elements.append(element)
        self._create_element_button(element)
    
    def remove_element(self, element: Any):
        """
        Remove an element from the explorer.
        
        Args:
            element: The element to remove
        """
        if element not in self._elements:
            return
        
        self._elements.remove(element)
        # Find and remove the button widget
        for widget in self._button_widgets[:]:  # Copy list to avoid modification during iteration
            if hasattr(widget, '_element') and widget._element == element:
                # Remove from grid
                self._container_layout.removeWidget(widget)
                self._button_widgets.remove(widget)
                widget.deleteLater()
                # Reset grid position tracking
                self._rebuild_grid()
                break
        
        # If this was the selected element, clear selection
        if self._selected_element == element:
            self._selected_element = None
    
    def _calculate_columns(self) -> int:
        """Calculate number of columns based on panel width."""
        if self.width() < 10:  # Not yet laid out
            return 2  # Default
        available_width = self.width() - self._grid_margins
        # Calculate: (button_width + spacing) * columns <= available_width
        # So: columns <= (available_width + spacing) / (button_width + spacing)
        columns = max(1, int((available_width + self._grid_spacing) / (self._button_widget_width + self._grid_spacing)))
        return columns
    
    def _rebuild_grid(self):
        """Rebuild the grid layout with current column count."""
        # Remove all widgets from grid
        for i in range(self._container_layout.count()):
            item = self._container_layout.itemAt(i)
            if item:
                self._container_layout.removeItem(item)
        
        # Recalculate columns
        new_columns = self._calculate_columns()
        if new_columns != self._columns_per_row:
            self._columns_per_row = new_columns
        
        # Re-add all widgets
        row, col = 0, 0
        for widget in self._button_widgets:
            if widget.parent() is None or widget.parent() == self._container:
                self._container_layout.addWidget(widget, row, col)
                col += 1
                if col >= self._columns_per_row:
                    col = 0
                    row += 1
    
    def _reset_grid(self):
        """Reset grid position tracking after removal."""
        self._rebuild_grid()
    
    def _create_element_button(self, element: Any):
        """Create a square icon button for an element."""
        # Get element name
        name = getattr(element, 'name', str(element))
        
        # Determine element type for icon/color
        element_type = self._get_element_type(element)
        type_icon = self._get_type_prefix(element_type)
        type_color = self._get_type_color(element_type)
        
        # Create container widget for icon and label
        button_widget = QWidget()
        button_widget._element = element  # Store reference to element
        button_widget.setFixedSize(80, 90)  # Square-ish button
        button_layout = QVBoxLayout(button_widget)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(6)
        button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Icon button (square)
        icon_button = ExplorerButton(type_icon)
        icon_button._element = element
        icon_button.setCheckable(True)
        icon_button.setFixedSize(60, 60)
        icon_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {type_color};
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                font-size: 36px;
                color: #333333;
                padding: 0px;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: {self._lighten_color(type_color)};
                border-color: #0078d4;
                border-width: 2px;
            }}
            QPushButton:checked {{
                background-color: #0078d4;
                border-color: #005a9e;
                border-width: 2px;
                color: white;
            }}
        """)
        
        # Name label below icon - fixed height with elided text
        name_label = QLabel(name)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
        name_label.setFixedHeight(20)
        name_label.setWordWrap(False)
        # Elide long names
        metrics = QFontMetrics(name_label.font())
        elided_name = metrics.elidedText(name, Qt.TextElideMode.ElideRight, 75)
        name_label.setText(elided_name)
        name_label.setToolTip(name)  # Show full name on hover
        name_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #666666;
                background-color: transparent;
                padding: 0px;
            }
        """)
        
        # Add to layout
        button_layout.addWidget(icon_button)
        button_layout.addWidget(name_label)
        
        # Connect signals
        icon_button.clicked.connect(lambda checked, el=element, btn=icon_button: self._on_element_clicked(el, btn))
        icon_button.doubleClicked.connect(lambda el=element: self._on_element_double_clicked(el))
        
        # Store widget reference
        self._button_widgets.append(button_widget)
        
        # Rebuild grid with current column count
        self._rebuild_grid()
    
    def _get_element_type(self, element: Any) -> str:
        """Get the type string for an element."""
        from kira.kdata.kdata import KData
        from kira.knodes.knode import KNode
        from kira.knodes.kworkflow import KWorkflow
        
        if isinstance(element, KData):
            if element.value is None:
                return "error"
            from kira.kdata.ktable import KTable
            from kira.kdata.kliteral import KLiteral
            if isinstance(element.value, KTable):
                return "table"
            elif isinstance(element.value, KLiteral):
                return "literal"
            return "data"
        elif isinstance(element, KWorkflow):
            return "workflow"
        elif isinstance(element, KNode):
            return "node"
        else:
            return "unknown"
    
    def _get_type_prefix(self, element_type: str) -> str:
        """Get a prefix icon/emoji for the element type."""
        prefixes = {
            "table": "📊",
            "literal": "🔢",
            "data": "📦",
            "node": "⚙️",
            "workflow": "🌿",
            "chart": "📈",
            "error": "❌",
            "unknown": "❓"
        }
        return prefixes.get(element_type, "")
    
    def _get_type_color(self, element_type: str) -> str:
        """Get background color for the element type icon button."""
        colors = {
            "table": "#e8f5e9",      # Light green
            "literal": "#fff3e0",     # Light orange
            "data": "#e3f2fd",        # Light blue
            "node": "#f3e5f5",        # Light purple
            "workflow": "#e0f2f1",   # Light teal
            "chart": "#fce4ec",      # Light pink
            "error": "#ffebee",       # Light red
            "unknown": "#f5f5f5"      # Light grey
        }
        return colors.get(element_type, "#f5f5f5")
    
    def _lighten_color(self, hex_color: str) -> str:
        """Lighten a hex color slightly for hover effect."""
        # Simple lightening - increase RGB values by ~15%
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        r = min(255, int(r * 1.15))
        g = min(255, int(g * 1.15))
        b = min(255, int(b * 1.15))
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def _on_element_clicked(self, element: Any, button: QPushButton):
        """Handle element button click."""
        # Uncheck all other icon buttons
        for i in range(self._container_layout.count()):
            item = self._container_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if isinstance(widget, QWidget) and hasattr(widget, '_element'):
                    # Find the icon button in this widget
                    for child in widget.findChildren(QPushButton):
                        if child != button and child.isCheckable():
                            child.setChecked(False)
        
        # Update selected element
        self._selected_element = element
        
        # Emit signal
        self.element_selected.emit(element)

    def _on_element_double_clicked(self, element: Any):
        """Handle element button double click."""
        self.element_double_clicked.emit(element)
        
        # Legacy support: also emit workflow_opened if it's a workflow
        from kira.knodes.kworkflow import KWorkflow
        if isinstance(element, KWorkflow):
            self.workflow_opened.emit(element)
    
    def set_elements(self, elements: List[Any]):
        """
        Set all elements at once (replaces existing).
        
        Args:
            elements: List of elements to display
        """
        # Clear existing buttons
        for widget in self._button_widgets:
            widget.deleteLater()
        
        # Reset
        self._button_widgets = []
        self._elements = []
        
        for element in elements:
            self.add_element(element)
    
    def eventFilter(self, obj, event):
        """Handle resize events to recalculate columns."""
        if obj == self:
            if event.type() == QEvent.Type.Resize:
                # Recalculate columns and rebuild grid
                new_columns = self._calculate_columns()
                if new_columns != self._columns_per_row:
                    self._rebuild_grid()
                # Update floating toolbar position
                self._update_toolbar_position()
            elif event.type() == QEvent.Type.Show:
                # Ensure toolbar is positioned when panel is first shown
                self._update_toolbar_position()
        
        return super().eventFilter(obj, event)

    def _on_add_clicked(self):
        """Handle add button click."""
        # Show menu below the button
        pos = self._add_button.mapToGlobal(QPoint(0, self._add_button.height()))
        self._add_menu.popup(pos)

    def _on_delete_clicked(self):
        """Handle delete button click."""
        if self._selected_element:
            # Emit signal instead of removing directly to allow undo/redo and project synchronization
            self.element_deleted.emit(self._selected_element)
    
    def get_selected_element(self) -> Optional[Any]:
        """Get the currently selected element."""
        return self._selected_element

