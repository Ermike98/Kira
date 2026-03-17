"""
gui/components/data_view.py
---------------------------
Unified viewer for all KData value types:

  • KLiteral  → LiteralView  (large centred value card)
  • KArray    → ArrayView    (scrollable list with index numbers)
  • KTable    → TableView    (Excel-like table with zoom, sort, copy)

Features:
  • Periodic state-version checking (every 1s) to auto-refresh when variables
    recalculate (e.g. WAITING -> READY).
  • Persistent display: while recalculating, keeps showing old data if available.
  • "Calculating..." placeholder for first-time evaluation.
  • Uses QStackedWidget for reliable content transitions.
"""

from __future__ import annotations
from typing import Optional, TYPE_CHECKING
import pandas as pd
import numpy as np

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QScrollArea, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QStackedWidget
)
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QFont, QColor
from gui import style_system
from gui.utils import colors

from gui.utils.svg_utils import icon_from_svg, recolor_svg
from kira.kdata.kliteral import KLiteral
from kira.kdata.karray import KArray
from kira.kdata.ktable import KTable

if TYPE_CHECKING:
    from kira.kdata.kdata import KData
    from gui.qt_project import QTProject


# ---------------------------------------------------------------------------#
#  1. Literal View (Scalar)                                                  #
# ---------------------------------------------------------------------------#

class LiteralView(QWidget):
    """Centered Card view for single values (Strings, Numbers, Booleans)."""
    def __init__(self, name: str, value: KLiteral, parent=None):
        super().__init__(parent)
        self._name = name
        self._value = value
        self._scale = 1.0 # Base scale for zoom
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Scroll Area for overflow
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setAlignment(Qt.AlignCenter) # Center widget when smaller than viewport
        main_layout.addWidget(self.scroll)
        
        # Inner centering widget
        self.centering_widget = QWidget()
        self.scroll.setWidget(self.centering_widget)
        
        self.center_layout = QVBoxLayout(self.centering_widget)
        self.center_layout.setContentsMargins(40, 40, 40, 40)
        self.center_layout.setAlignment(Qt.AlignCenter)
        
        # --- The Card ---
        self.card = QFrame()
        self.card.setObjectName("LiteralCard")
        self.card_layout = QVBoxLayout(self.card)
        self.card_layout.setContentsMargins(0, 0, 0, 0)
        self.card_layout.setSpacing(0)
        
        # Header: [Name | Type]
        self.header_row = QWidget()
        self.header_layout = QHBoxLayout(self.header_row)
        # Margins will be set in _update_style
        
        self.name_lbl = QLabel(name)
        self.name_lbl.setObjectName("LiteralTitle")
        self.header_layout.addWidget(self.name_lbl, alignment=Qt.AlignBottom)
        
        self.header_layout.addStretch()
        
        self.type_lbl = QLabel(str(value.lit_type.name))
        self.type_lbl.setObjectName("LiteralMeta")
        self.header_layout.addWidget(self.type_lbl, alignment=Qt.AlignBottom)
        
        self.card_layout.addWidget(self.header_row)
        
        # Separator (full width)
        self.line = QFrame()
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Plain)
        self.card_layout.addWidget(self.line)
        
        # Value
        self.val_lbl = QLabel()
        self.val_lbl.setObjectName("LiteralValue")
        self.val_lbl.setAlignment(Qt.AlignCenter)
        self.val_lbl.setWordWrap(True)
        self.val_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.card_layout.addWidget(self.val_lbl)
        
        self.center_layout.addWidget(self.card)
        self._update_style()

    def _update_style(self):
        """Scale all styling parameters and apply current font size."""
        s = self._scale
        
        # Base dimensions/spacing (multiplied by scale)
        font_val = int(style_system.font_xxlarge_i * s)
        font_name = int(style_system.font_xxlarge_i * s)
        font_type = int(style_system.font_medium_i * s)
        padding = int(32 * s)
        radius = int(style_system.radius_large_i * s)
        card_min_w = int(300 * s)
        
        # Apply style to the Card
        self.card.setStyleSheet(f"""
            #LiteralCard {{
                background-color: white;
                border: 1px solid {colors.slate_200};
                border-radius: {radius}px;
            }}
        """)
        self.card.setMinimumWidth(card_min_w)
        
        # Move padding to sub-layouts to allow the line to touch borders
        self.header_layout.setContentsMargins(padding, padding, padding, int(padding/2))
        self.val_lbl.setContentsMargins(padding, int(padding/2), padding, padding)
        
        self.name_lbl.setStyleSheet(f"font-weight: bold; font-size: {font_name}px; color: {colors.slate_900}; padding: 0; margin: 0;")
        self.type_lbl.setStyleSheet(f"font-size: {font_type}px; color: {colors.slate_400}; text-transform: uppercase; font-weight: 600; padding: 0; margin: 0;")
        
        # Full width line (no horizontal margin)
        self.line.setStyleSheet(f"color: {colors.slate_100}; background-color: {colors.slate_100}; border: none; height: 1px; margin: 0;")
        
        display_val = str(self._value.value)
        if self._value.lit_type.name == "STRING":
            display_val = f'"{display_val}"'
            
        self.val_lbl.setText(display_val)
        self.val_lbl.setStyleSheet(f"font-size: {font_val}px; color: {colors.slate_900};")

    def resizeEvent(self, event):
        super().resizeEvent(event)

    def wheelEvent(self, event):
        """Handle zoom for literal card by scaling entire UI."""
        if event.modifiers() & Qt.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self._scale = min(4.0, self._scale + 0.1)
            else:
                self._scale = max(0.5, self._scale - 0.1)
            
            self._update_style()
            event.accept()
        else:
            super().wheelEvent(event)


# ---------------------------------------------------------------------------#
#  2. Array View (Numpy)                                                     #
# ---------------------------------------------------------------------------#

class ArrayView(QWidget):
    """Scrollable list for 1D/2D arrays with zoom support."""
    def __init__(self, name: str, array: KArray, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        
        self.table = _ArrayTableView(array.value)
        layout.addWidget(self.table)


class _ArrayTableView(QTableWidget):
    """
    Subclass of QTableWidget that supports zooming for Numpy arrays.
    """
    def __init__(self, array_data: np.ndarray, parent=None):
        super().__init__(parent)
        self._font_size = 16 # Default px size (medium)
        self.setAlternatingRowColors(True)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setSelectionBehavior(QTableWidget.SelectItems)
        self.setFrameShape(QFrame.NoFrame)
        
        data = array_data
        if data.ndim == 1:
            self.setRowCount(len(data))
            self.setColumnCount(1)
            for i, val in enumerate(data):
                self.setItem(i, 0, QTableWidgetItem(str(val)))
        elif data.ndim == 2:
            rows, cols = data.shape
            self.setRowCount(rows)
            self.setColumnCount(cols)
            for r in range(rows):
                for c in range(cols):
                    self.setItem(r, c, QTableWidgetItem(str(data[r, c])))
        else:
            self.setRowCount(1)
            self.setColumnCount(1)
            self.setItem(0, 0, QTableWidgetItem("High-dimensional array"))

        self._update_style()

    def _update_style(self):
        """Apply current font size to the table."""
        style = f"""
            QTableWidget {{ 
                font-size: {self._font_size}px; 
            }}
            QHeaderView::section {{
                font-size: {self._font_size}px;
                padding: {style_system.spacing_xsmall};
            }}
        """
        self.setStyleSheet(style)
        # Update row height
        new_h = int(self._font_size * 2.2)
        self.verticalHeader().setDefaultSectionSize(new_h)

    def wheelEvent(self, event):
        """Handle zoom with Ctrl + Mouse Wheel."""
        if event.modifiers() & Qt.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self._font_size = min(60, self._font_size + 2)
            else:
                self._font_size = max(6, self._font_size - 2)
            
            self._update_style()
            event.accept()
        else:
            super().wheelEvent(event)


# ---------------------------------------------------------------------------#
#  3. Table View (Pandas)                                                    #
# ---------------------------------------------------------------------------#

class TableView(QWidget):
    """Rich Excel-like table for DataFrames."""
    def __init__(self, name: str, table_data: KTable, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        
        df = table_data.value # pandas DataFrame
        self.table = _ExcelTableView(df)
        layout.addWidget(self.table)


class _ExcelTableView(QTableWidget):
    """
    Rich table with smart column stretching and content-aware resizing.
    """
    def __init__(self, df: pd.DataFrame, parent=None):
        super().__init__(parent)
        self._df = df
        self._font_size = 16 # Default px size (medium)
        self.setAlternatingRowColors(True)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setSelectionBehavior(QTableWidget.SelectItems)
        self.setSortingEnabled(True)
        
        self.setColumnCount(len(df.columns))
        self.setHorizontalHeaderLabels(df.columns.tolist())
        self.setRowCount(len(df))
        
        for r in range(len(df)):
            for c in range(len(df.columns)):
                val = df.iloc[r, c]
                item = QTableWidgetItem(str(val))
                if isinstance(val, (int, float, np.number)):
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.setItem(r, c, item)
        
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.verticalHeader().setDefaultSectionSize(28)
        
        # Initial styling and sizing
        self._update_style()
        self._smart_stretch()

    def _update_style(self):
        """Apply current font size to the table and its headers."""
        style = f"""
            QTableWidget {{ 
                font-size: {self._font_size}px; 
            }}
            QHeaderView::section {{
                font-size: {self._font_size}px;
                padding: {style_system.spacing_xsmall};
            }}
        """
        self.setStyleSheet(style)

    def wheelEvent(self, event):
        """Handle zoom with Ctrl + Mouse Wheel."""
        if event.modifiers() & Qt.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self._font_size = min(40, self._font_size + 1)
            else:
                self._font_size = max(6, self._font_size - 1)
            
            # Update row height (approx 2.5x font size)
            new_h = int(self._font_size * 2.5)
            self.verticalHeader().setDefaultSectionSize(new_h)
            
            self._update_style()
            self._smart_stretch()
            event.accept()
        else:
            super().wheelEvent(event)

    def _smart_stretch(self):
        """
        Calculates column widths based on the first 100 rows and 
        stretches them to fill the viewport if there is remaining space.
        """
        if self.columnCount() == 0:
            return

        fm = self.fontMetrics()
        header_fm = self.horizontalHeader().fontMetrics()
        
        # 1. Determine base widths from content (max 100 rows)
        content_widths = []
        max_rows = min(100, self.rowCount())
        
        for c in range(self.columnCount()):
            # Start with header width
            col_name = self.horizontalHeaderItem(c).text()
            max_w = header_fm.horizontalAdvance(col_name) + 30 # + padding
            
            # Check rows
            for r in range(max_rows):
                text = self.item(r, c).text()
                w = fm.horizontalAdvance(text) + 20
                if w > max_w:
                    max_w = w
            
            # Threshold cap
            max_w = min(max_w, 500)
            content_widths.append(max_w)
            self.setColumnWidth(c, max_w)

        # 2. Check if we should stretch to fill viewport
        total_content_w = sum(content_widths)
        viewport_w = self.viewport().width()
        
        if total_content_w < viewport_w:
            extra = (viewport_w - total_content_w) // self.columnCount()
            for c in range(self.columnCount()):
                self.setColumnWidth(c, content_widths[c] + extra)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Re-apply stretch on resize to maintain "fill" behavior
        self._smart_stretch()


# ---------------------------------------------------------------------------#
#  Fallback / error / loading view                                            #
# ---------------------------------------------------------------------------#

class _StatusView(QWidget):
    def __init__(self, name: str, message: str, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        lbl = QLabel(f"<b>{name}</b><br><br>{message}")
        lbl.setObjectName("DataErrorLabel")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setWordWrap(True)
        layout.addWidget(lbl)


# ---------------------------------------------------------------------------#
#  Public factory: DataView                                                   #
# ---------------------------------------------------------------------------#

class DataView(QWidget):
    """
    Factory widget: inspects a KData object and shows the right sub-view.
    Uses QStackedWidget for robust content transitions.
    """

    def __init__(self, project: Optional[QTProject] = None, name: Optional[str] = None, parent=None):
        super().__init__(parent)
        self.project = project
        self.name = name
        self._last_version = ""
        self._has_valid_data = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        # Version-checking timer
        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._check_refresh)
        if project:
            self._poll_timer.start(1000)

    # ---- Public API ---------------------------------------------------------

    def set_kdata(self, name: str, kdata: KData):
        self.name = name
        self._refresh_from_kdata(kdata)

    def _refresh_from_kdata(self, kdata: KData):
        from kira.kdata.kdata import KData as _KData
        
        is_ready = isinstance(kdata, _KData) and kdata.value is not None
        
        if is_ready:
            self._replace(self._build_view(self.name, kdata))
            self._has_valid_data = True
            if self.project:
                self._last_version = self.project.state_version
        else:
            if not self._has_valid_data:
                msg = "Calculating..."
                if kdata is not None and not isinstance(kdata, _KData):
                    msg = f"Calculating...\n({kdata})"
                self._replace(_StatusView(self.name, msg))

    # ---- Internal -----------------------------------------------------------

    def _check_refresh(self):
        if not self.project or not self.name:
            return

        current_version = self.project.state_version
        if current_version != self._last_version or not self._has_valid_data:
            kdata = self.project.get_value(self.name)
            self._refresh_from_kdata(kdata)

    def _build_view(self, name: str, kdata: KData) -> QWidget:
        val = kdata.value

        if isinstance(val, KLiteral):
            return LiteralView(name, val)

        if isinstance(val, KArray):
            return ArrayView(name, val)

        if isinstance(val, KTable):
            return TableView(name, val)

        return _StatusView(name, f"Unsupported data type: {type(val).__name__}")

    def _replace(self, new_widget: QWidget):
        old_widget = self.stack.currentWidget()
        self.stack.addWidget(new_widget)
        self.stack.setCurrentWidget(new_widget)
        if old_widget:
            self.stack.removeWidget(old_widget)
            old_widget.deleteLater()
