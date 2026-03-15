"""
Tab widget for displaying KTable (pandas DataFrame) data.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableView, QHeaderView, QApplication, QSplitter, QFrame, QHBoxLayout, QSizePolicy
from PySide6.QtCore import Qt, QAbstractTableModel, Slot, QPoint, Signal, QSize
from gui.panels.transformations_panel import TransformationsPanel
from PySide6.QtGui import QKeySequence, QShortcut, QFont, QWheelEvent, QFontMetrics
import pandas as pd
from kira.kdata.ktable import KTable

class PandasTableModel(QAbstractTableModel):
    """Model to display pandas DataFrame in QTableView."""
    
    # Signals for backend/undo integration
    value_changed = Signal(int, int, object, object) # row, col, old_val, new_val
    layout_changed = Signal() # Helper for view update
    
    def __init__(self, data: pd.DataFrame):
        super().__init__()
        self._data = data
    
    def rowCount(self, parent=None):
        return self._data.shape[0]
    
    def columnCount(self, parent=None):
        return self._data.shape[1]
    
    def flags(self, index):
        """Allow editing."""
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEditable
    
    def setData(self, index, value, role=Qt.EditRole):
        """Update data on edit."""
        if not index.isValid() or role != Qt.EditRole:
            return False
            
        row = index.row()
        col = index.column()
        
        # Get current value for undo reference
        old_value = self._data.iloc[row, col]
        
        # Try to convert type to match column if possible, otherwise string
        try:
            dtype = self._data.dtypes.iloc[col]
            if pd.api.types.is_numeric_dtype(dtype):
                if pd.api.types.is_float_dtype(dtype):
                    new_value = float(value)
                else:
                    new_value = int(value)
            else:
                new_value = str(value)
        except ValueError:
            # Fallback to string if conversion fails
            new_value = str(value)
            
        # Update DataFrame
        self._data.iloc[row, col] = new_value
        
        # Emit signal for data change (Standard)
        self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole])
        
        # Emit custom signal for undo stack
        self.value_changed.emit(row, col, old_value, new_value)
        
        return True
    
    def sort(self, column, order):
        """Sort the DataFrame."""
        col_name = self._data.columns[column]
        ascending = (order == Qt.SortOrder.AscendingOrder)
        
        self.layoutAboutToBeChanged.emit()
        self._data.sort_values(by=col_name, ascending=ascending, inplace=True)
        self.layoutChanged.emit()
        
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        
        if role == Qt.DisplayRole or role == Qt.EditRole:
            value = self._data.iloc[index.row(), index.column()]
            return str(value)
        
        if role == Qt.TextAlignmentRole:
            value = self._data.iloc[index.row(), index.column()]
            if isinstance(value, (int, float)):
                return Qt.AlignRight | Qt.AlignVCenter
            return Qt.AlignLeft | Qt.AlignVCenter
        
        return None
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            col_name = str(self._data.columns[section])
            col_type = str(self._data.dtypes.iloc[section])
            return f"{col_name}\n({col_type})"
            
        if orientation == Qt.Vertical and role == Qt.DisplayRole:
            return str(self._data.index[section])
        
        return None

class ExcelTableView(QTableView):
    """Custom TableView with Zoom support and Excel-like feel."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._font_size = 10
        self._base_row_height = 30
        self._base_row_height = 30
        self.setFont(QFont("Segoe UI", self._font_size))
        
        # Remove default frame border
        self.setFrameShape(QFrame.Shape.NoFrame)
        
        # Set initial row height
        self.verticalHeader().setDefaultSectionSize(self._base_row_height)
        
        # Initial style application
        self.update_style()
        
        # Connect column resize to layout update
        self.horizontalHeader().sectionResized.connect(self.update_layout_width)
        
    def wheelEvent(self, event: QWheelEvent):
        """Handle zoom with Ctrl+Wheel."""
        if event.modifiers() & Qt.ControlModifier:
            delta = event.angleDelta().y()
            
            # Current state
            old_size = self._font_size
            old_row_h = self.verticalHeader().defaultSectionSize()
            
            # Mouse position in viewport
            viewport_pos = event.position().toPoint()
            mouse_x = viewport_pos.x()
            mouse_y = viewport_pos.y()
            
            # Current scroll absolute position (pixels)
            scroll_x = self.horizontalScrollBar().value()
            scroll_y = self.verticalScrollBar().value()
            
            # Absolute mouse position in content space
            abs_mouse_x = scroll_x + mouse_x
            abs_mouse_y = scroll_y + mouse_y
            
            # Determine target size
            target_size = old_size
            if delta > 0:
                target_size += 1
            else:
                target_size = max(6, target_size - 1)
            
            if target_size == old_size:
                event.accept()
                return

            # Apply zoom
            self.set_zoom(target_size)
            
            # Calculate ratios
            # X ratio: derived from proportional scaling in set_zoom (target / old)
            ratio_x = target_size / old_size
            
            # Y ratio: derived from default section size change
            new_row_h = self.verticalHeader().defaultSectionSize()
            ratio_y = new_row_h / old_row_h if old_row_h else 1.0
            
            # Calculate new absolute mouse position in content space
            new_abs_mouse_x = abs_mouse_x * ratio_x
            new_abs_mouse_y = abs_mouse_y * ratio_y
            
            # Calculate new scroll positions to maintain viewport offset
            new_scroll_x = int(new_abs_mouse_x - mouse_x)
            new_scroll_y = int(new_abs_mouse_y - mouse_y)
            
            # Apply new scroll positions
            self.horizontalScrollBar().setValue(new_scroll_x)
            self.verticalScrollBar().setValue(new_scroll_y)
            
            event.accept()
        else:
            super().wheelEvent(event)
            
    def set_zoom(self, font_size: int):
        """Apply zoom level."""
        if font_size == self._font_size:
            return
            
        # Calculate scale ratio
        ratio = font_size / self._font_size
        
        # Update stored font size
        self._font_size = font_size
        
        # Scale row height (approximate 2.5x font size for comfortable padding)
        new_row_height = int(self._font_size * 2.5)
        self.verticalHeader().setDefaultSectionSize(new_row_height)
        
        # Update stylesheet to force font size
        self.update_style()
        
        # Proportally scale column widths to maintain user's manual resizing
        header = self.horizontalHeader()
        for i in range(header.count()):
            current_width = self.columnWidth(i)
            new_width = int(current_width * ratio)
            self.setColumnWidth(i, new_width)
            
        self.update_layout_width()

    def resize_columns_to_content(self, max_rows=100):
        """
        Resize columns to fit content, but limited to max_rows for performance.
        Also guarantees header visibility.
        """
        model = self.model()
        if not model:
            return
            
        font = self.font()
        fm = QFontMetrics(font)
        header_font = self.horizontalHeader().font()
        header_fm = QFontMetrics(header_font)
        
        row_count = min(model.rowCount(), max_rows)
        col_count = model.columnCount()
        
        for col in range(col_count):
            # 1. Measure Header
            header_text = str(model.headerData(col, Qt.Horizontal))
            # Header has \n so we need to check widest line
            header_width = max(header_fm.horizontalAdvance(line) for line in header_text.split('\n'))
            max_width = header_width + 20 # Padding
            
            # 2. Measure first N rows
            for row in range(row_count):
                index = model.index(row, col)
                text = str(model.data(index, Qt.DisplayRole))
                text_width = fm.horizontalAdvance(text)
                if text_width > max_width:
                    max_width = text_width
            
            # Add some padding for cell content
            max_width += 20
            
            self.setColumnWidth(col, max_width)
            
        self.update_layout_width()
        
    def update_layout_width(self):
        """Update widget width to match content width + scrollbar."""
        self.updateGeometry()
        
    def sizeHint(self):
        """Calculate exact size needed for content."""
        # Calculate total width of all columns
        header = self.horizontalHeader()
        total_width = 0
        for i in range(header.count()):
            total_width += self.columnWidth(i)
            
        # Add vertical header width (if visible)
        if self.verticalHeader().isVisible():
            total_width += self.verticalHeader().width()
            
        # Add vertical scrollbar width (always reserve space to prevent jitter)
        total_width += self.verticalScrollBar().sizeHint().width()
        
        # Add frame width (borders) (plus a small buffer)
        total_width += self.frameWidth() * 2 + 4
        
        # Current height is fine (expanding)
        return QSize(total_width, self.rect().height())


    def update_style(self):
        """Apply Excel-like CSS styling with current font size."""
        # We inject the font size into the stylesheet dynamically
        style = f"""
            QTableView {{
                background-color: transparent; /* Transparent background as requested */
                gridline-color: #ededed;
                color: #333333;
                font-size: {self._font_size}pt;
                font-family: "Segoe UI", sans-serif;
                border: none; /* Remove border from the view itself */
                outline: none;
                selection-background-color: #e8f5e9;
                selection-color: black;
            }}
            
            QTableView::item {{
                padding: 4px;
                background-color: white; /* Ensure cells are white */
                border-bottom: 0px; 
            }}
            
            QHeaderView::section {{
                background-color: #f0f4f8;
                color: #5f6368;
                border: none;
                border-bottom: 2px solid #e0e0e0;
                border-right: 1px solid #d0d0d0;
                padding: 4px 8px;
                font-weight: 600;
                font-family: "Segoe UI";
                font-size: {self._font_size}pt;
            }}
            
            QHeaderView::section:horizontal {{
                border-bottom: 2px solid #e0e0e0; 
            }}
            
            QHeaderView::section:vertical {{
                border-right: 2px solid #e0e0e0;
                background-color: #f0f4f8;
                color: #5f6368;
                font-weight: normal;
            }}
            
            QTableCornerButton::section {{
                background-color: #f0f4f8;
                border: none;
                border-bottom: 2px solid #e0e0e0;
                border-right: 2px solid #e0e0e0;
            }}
        """
        self.setStyleSheet(style)
        
    def resizeEvent(self, event):
        """Handle resize to ensure layout updates."""
        super().resizeEvent(event)
        self.updateGeometry()

class TableTab(QWidget):
    """
    Tab for visualizing a KTable.
    Supports smooth scrolling, cell copying, zoom, and Excel-like styling.
    """
    
    def __init__(self, table: KTable, name: str, parent=None):
        super().__init__(parent)
        self._table = table
        self.name = name
        self._setup_ui()
        self._setup_shortcuts()
        
        # Initial sizing
        self._table_view.resize_columns_to_content(200) # Slightly deeper check for initial load
        
    def _setup_ui(self):
        """Set up the UI components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0) # Remove margins to touch borders
        main_layout.setSpacing(0)
        
        # Splitter
        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.setHandleWidth(4) # Match homepage width
        self._splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: transparent;
            }
            QSplitter::handle:hover {
                background-color: #0078d4;
            }
            QSplitter::handle:pressed {
                background-color: #005a9e;
            }
        """)
        
        # --- LEFT: Table Container ---
        self._table_container = QFrame()
        self._table_container.setObjectName("TableContainer")
        # Removing borders as requested (up/left/bottom).
        # "Make color the background on the right of the scrollbar transparent" implies container is transparent.
        self._table_container.setStyleSheet("""
            QFrame#TableContainer {
                background-color: transparent; 
                border: none;
            }
        """)
        
        # Use HBox to allow table to sit on left and spacer on right
        table_layout = QHBoxLayout(self._table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.setSpacing(0)
        
        self._table_view = ExcelTableView()
        # Ensure the table only takes as much width as it needs (from sizeHint), but can expand vertically
        self._table_view.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Expanding)
        
        # Smooth scrolling
        self._table_view.setVerticalScrollMode(QTableView.ScrollMode.ScrollPerPixel)
        self._table_view.setHorizontalScrollMode(QTableView.ScrollMode.ScrollPerPixel)
        
        # Selection mode
        self._table_view.setSelectionMode(QTableView.SelectionMode.ContiguousSelection)
        self._table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectItems)
        
        # Sorting
        self._table_view.setSortingEnabled(True)
        
        # Set model
        self._model = PandasTableModel(self._table.value)
        self._table_view.setModel(self._model)
        
        # Header alignment & Context Menu
        header = self._table_view.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft)
        header.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        header.customContextMenuRequested.connect(self._show_header_menu)
        # header.setStretchLastSection(False) # Already default
        
        self._table_view.verticalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        table_layout.addWidget(self._table_view)
        
        # Add stretch to fill the empty space to the right
        table_layout.addStretch()
        
        # --- RIGHT: Transformations Panel ---
        self._transformations_panel = TransformationsPanel()
        
        # Container for transformations to give it some margin (floating card look)
        self._transforms_container = QWidget()
        transforms_layout = QVBoxLayout(self._transforms_container)
        transforms_layout.setContentsMargins(0, 10, 10, 10) # 0 Left margin to touch splitter
        transforms_layout.setSpacing(0)
        transforms_layout.addWidget(self._transformations_panel)
        
        # Add to splitter
        self._splitter.addWidget(self._table_container)
        self._splitter.addWidget(self._transforms_container)
        
        # Set initial sizes (75% table, 25% transformations)
        self._splitter.setStretchFactor(0, 3)
        self._splitter.setStretchFactor(1, 1)
        
        main_layout.addWidget(self._splitter)
            
    def _setup_shortcuts(self):
        """Setup keyboard shortcuts."""
        # Copy shortcut (Ctrl+C)
        self._copy_shortcut = QShortcut(QKeySequence.StandardKey.Copy, self)
        self._copy_shortcut.activated.connect(self._copy_selection)
        
        # Connect model signals
        self._model.value_changed.connect(self._on_value_changed)
        self._model.layoutChanged.connect(self._on_sorting_changed)
        
    @Slot(int, int, object, object)
    def _on_value_changed(self, row, col, old_val, new_val):
        """Handle value changes."""
        col_name = self._table.value.columns[col]
        self._transformations_panel.add_transformation(
            "Value Changed",
            f"Row {row}, Col '{col_name}': {old_val} -> {new_val}"
        )
        
    @Slot()
    def _on_sorting_changed(self):
        """Handle sorting changes."""
        # Note: We don't have exact sort details from layoutChanged, 
        # but we know a sort happened if triggered by header click
        self._transformations_panel.add_transformation(
            "Sorted",
            "Table layout updated"
        )

    @Slot(QPoint)
    def _show_header_menu(self, pos: QPoint):
        """Show context menu for header."""
        from PySide6.QtWidgets import QMenu
        
        header = self._table_view.horizontalHeader()
        col_idx = header.logicalIndexAt(pos)
        
        menu = QMenu(self)
        
        # Sort Actions
        action_sort_asc = menu.addAction("Sort Ascending")
        action_sort_desc = menu.addAction("Sort Descending")
        menu.addSeparator()
        
        # Filter Action
        action_filter = menu.addAction("Filter...")
        menu.addSeparator()
        
        # Add Column Action
        action_add_col = menu.addAction("Add New Column")
        
        # Determine selection for sorting/filtering
        col_name = self._table.value.columns[col_idx] if col_idx >= 0 else None
        
        # Execute
        action = menu.exec(header.mapToGlobal(pos))
        
        if action == action_sort_asc and col_idx >= 0:
            self._model.sort(col_idx, Qt.SortOrder.AscendingOrder)
        elif action == action_sort_desc and col_idx >= 0:
            self._model.sort(col_idx, Qt.SortOrder.DescendingOrder)
        elif action == action_filter and col_idx >= 0:
            self._filter_column(col_idx)
        elif action == action_add_col:
            self._add_column()

    def _filter_column(self, col_idx):
        """Show filter dialog."""
        from PySide6.QtWidgets import QInputDialog
        col_name = self._table.value.columns[col_idx]
        text, ok = QInputDialog.getText(self, "Filter Column", f"Filter '{col_name}' by value (contains):")
        
        if ok and text:
            # Emit transformation signal (Stub logic for now)
            # In a real app, this would apply a mask to the dataframe
            self._transformations_panel.add_transformation(
                "Filter Applied",
                f"Column '{col_name}' contains '{text}'"
            )
            # Backend would handle the actual data filtering
            
    def _add_column(self):
        """Show add column dialog."""
        from PySide6.QtWidgets import QInputDialog
        text, ok = QInputDialog.getText(self, "Add Column", "New Column Name:")
        
        if ok and text:
            # Update DataFrame directly for now (optimistic UI)
            self._model.layoutAboutToBeChanged.emit()
            self._table.value[text] = "" # Empty strings
            self._model.layoutChanged.emit()
            
            self._transformations_panel.add_transformation(
                "Column Added",
                f"New column: '{text}'"
            )

    @Slot()
    def _copy_selection(self):
        """Copy selected cells to clipboard."""
        selection = self._table_view.selectionModel()
        if not selection.hasSelection():
            return
            
        indexes = selection.selectedIndexes()
        if not indexes:
            return
            
        # Sort indexes to ensure correct order
        indexes.sort(key=lambda x: (x.row(), x.column()))
        
        # Get rows and columns range
        rows = sorted(list(set(index.row() for index in indexes)))
        cols = sorted(list(set(index.column() for index in indexes)))
        
        # Create text representation
        text_parts = []
        for r in rows:
            row_parts = []
            for c in cols:
                # Find index for this row/col
                matches = [i for i in indexes if i.row() == r and i.column() == c]
                if matches:
                    data = self._model.data(matches[0], Qt.DisplayRole)
                    row_parts.append(str(data))
                else:
                    row_parts.append("")
            text_parts.append("\t".join(row_parts))
            
        clipboard_text = "\n".join(text_parts)
        QApplication.clipboard().setText(clipboard_text)

    @property
    def table(self) -> KTable:
        return self._table
