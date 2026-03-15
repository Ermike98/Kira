"""
Preview widget for KTable (pandas DataFrame) data.
"""

from PySide6.QtWidgets import QTableView, QVBoxLayout, QLabel, QHeaderView
from PySide6.QtCore import Qt, QAbstractTableModel
from kira.kdata.kdata import KData, KDataType
from kira.kdata.ktable import KTable
from .base_preview import BasePreview
import pandas as pd


class PandasTableModel(QAbstractTableModel):
    """Model to display pandas DataFrame in QTableView."""
    
    def __init__(self, data: pd.DataFrame):
        super().__init__()
        self._data = data
    
    def rowCount(self, parent=None):
        return self._data.shape[0]
    
    def columnCount(self, parent=None):
        return self._data.shape[1]
    
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        
        value = self._data.iloc[index.row(), index.column()]
        
        if role == Qt.DisplayRole:
            return str(value)
        
        if role == Qt.TextAlignmentRole:
            if isinstance(value, (int, float)):
                return Qt.AlignRight | Qt.AlignVCenter
            return Qt.AlignLeft | Qt.AlignVCenter
        
        return None
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return str(self._data.columns[section])
        if orientation == Qt.Vertical and role == Qt.DisplayRole:
            return str(self._data.index[section])
        return None


class TablePreview(BasePreview):
    """Preview widget for KTable data (pandas DataFrames)."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._table_view = None
        self._info_label = None
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI components."""
        # Info label (shows shape, columns, etc.)
        self._info_label = QLabel()
        self._info_label.setStyleSheet("color: #666666; font-size: 12px;")
        self._layout.addWidget(self._info_label)
        
        # Table view
        self._table_view = QTableView()
        self._table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table_view.setAlternatingRowColors(True)
        self._layout.addWidget(self._table_view)
    
    def update_preview(self, element: KData):
        """Update the preview with KTable data."""
        if not isinstance(element, KData):
            self._info_label.setText("Invalid element type")
            return
        
        if element.value is None:
            self._info_label.setText("No data available (error occurred)")
            return
        
        if not isinstance(element.value, KTable):
            self._info_label.setText("Element is not a KTable")
            return
        
        # Get the pandas DataFrame
        df = element.value.value
        
        # Update info label
        shape_text = f"Shape: {df.shape[0]} rows × {df.shape[1]} columns"
        columns_text = f"Columns: {', '.join(df.columns.astype(str))}"
        self._info_label.setText(f"{shape_text} | {columns_text}")
        
        # Update table view
        model = PandasTableModel(df)
        self._table_view.setModel(model)
        
        # Set title
        self.set_title(f"Table: {element.name}")
    
    def can_preview(self, element) -> bool:
        """Check if this preview can handle the element."""
        if not isinstance(element, KData):
            return False
        
        if element.value is None:
            return False
        
        return isinstance(element.value, KTable) or element.type.type == KDataType.TABLE

