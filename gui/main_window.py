"""
Main window for the Kira GUI application.
"""

import sys
from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QTabBar, QToolBar
)
from PySide6.QtGui import QAction

from .homepage import HomepageTab
from .workflow_tab import WorkflowTab
from .styles import LIGHT_THEME
from gui.kproject import KProject


class MainWindow(QMainWindow):
    """
    Main application window with tabbed interface.
    The homepage tab is fixed and cannot be closed.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Kira - Data Analysis & Manipulation")
        self.setGeometry(100, 100, 1400, 900)
        
        # Initialize the project manager
        self._project = KProject("Demo Project")
        
        # Apply styling
        self.setStyleSheet(LIGHT_THEME)
        
        # Setup UI
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the main window UI."""
        # Create tab widget
        self._tab_widget = QTabWidget()
        self._tab_widget.setTabsClosable(True)
        self._tab_widget.tabCloseRequested.connect(self._on_tab_close_requested)
        
        # Create and add homepage tab (fixed, not closable)
        self._homepage = HomepageTab(self._project)
        self._homepage.workflow_opened.connect(self._on_workflow_opened)
        self._homepage_index = self._tab_widget.addTab(self._homepage, "Homepage")
        
        # Make homepage tab not closable
        self._tab_widget.tabBar().setTabButton(self._homepage_index, QTabBar.ButtonPosition.LeftSide, None)
        self._tab_widget.tabBar().setTabButton(self._homepage_index, QTabBar.ButtonPosition.RightSide, None)
        
        # Set as central widget
        self.setCentralWidget(self._tab_widget)
        
        # Add some test elements to the explorer (for demonstration)
        self._add_test_elements()
        
        # Clear undo stack after initialization so test data isn't undoable
        self._project.clear_undo_stack()
        
        # Add global shortcuts for Undo/Redo
        self._setup_shortcuts()
    
    def _setup_shortcuts(self):
        """Setup global keyboard shortcuts."""
        self._undo_action = QAction("Undo", self)
        self._undo_action.setShortcut("Ctrl+Z")
        self._undo_action.triggered.connect(self._project.undo)
        self.addAction(self._undo_action)
        
        self._redo_action = QAction("Redo", self)
        self._redo_action.setShortcut("Ctrl+Y")
        self._redo_action.triggered.connect(self._project.redo)
        self.addAction(self._redo_action)
    
    def _on_tab_close_requested(self, index: int):
        """Handle tab close request."""
        # Prevent closing the homepage tab
        if index == self._homepage_index:
            # Don't show message box, just prevent closing silently
            return
        
        # Close other tabs
        widget = self._tab_widget.widget(index)
        if widget:
            widget.deleteLater()
            self._tab_widget.removeTab(index)
            
    def _on_workflow_opened(self, workflow):
        """Handle workflow opening in a new tab."""
        # Check if the workflow is already open
        for i in range(self._tab_widget.count()):
            tab = self._tab_widget.widget(i)
            if isinstance(tab, WorkflowTab) and tab.workflow == workflow:
                self._tab_widget.setCurrentIndex(i)
                return
        
        # Open a new tab
        new_tab = WorkflowTab(self._project, workflow)
        index = self._tab_widget.addTab(new_tab, workflow.name)
        self._tab_widget.setCurrentIndex(index)
    
    def _add_test_elements(self):
        """Add some test elements to the explorer for demonstration."""
        try:
            import pandas as pd
            import numpy as np
            from kira.kdata.kdata import KData
            from kira.kdata.ktable import KTable
            from kira.kdata.kliteral import KLiteral
            from kira.knodes.kworkflow import KWorkflow
            from kira.kexpections.kexception import KException
            
            # Small test table
            small_df = pd.DataFrame({
                'ID': [1, 2, 3, 4, 5],
                'Name': ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve'],
                'Value': [10.5, 20.3, 15.7, 8.9, 12.1]
            })
            small_table = KData("Small Table", KTable(small_df))
            self._project.add_data(small_table)

            # Test workflows
            wf_example = KWorkflow("Example Workflow", [], [])
            self._project.add_workflow(wf_example)
            
            wf1 = KWorkflow("Data Cleanup", [], [])
            self._project.add_workflow(wf1)
            
            wf2 = KWorkflow("Sales Analysis", [], [])
            self._project.add_workflow(wf2)
            
            # Medium table (hundreds of rows)
            np.random.seed(42)
            medium_df = pd.DataFrame({
                'Product_ID': range(1, 501),
                'Product_Name': [f'Product_{i}' for i in range(1, 501)],
                'Price': np.random.uniform(10, 1000, 500).round(2),
                'Stock': np.random.randint(0, 1000, 500),
                'Category': np.random.choice(['Electronics', 'Clothing', 'Food', 'Books'], 500)
            })
            medium_table = KData("Products Catalog", KTable(medium_df))
            self._project.add_data(medium_table)
            
            # Large table (thousands of rows)
            large_df = pd.DataFrame({
                'Transaction_ID': range(1, 5001),
                'Date': pd.date_range('2024-01-01', periods=5000, freq='h'),
                'Customer_ID': np.random.randint(1, 500, 5000),
                'Amount': np.random.uniform(5, 500, 5000).round(2),
                'Payment_Method': np.random.choice(['Credit Card', 'Debit Card', 'Cash', 'PayPal'], 5000),
                'Status': np.random.choice(['Completed', 'Pending', 'Failed'], 5000, p=[0.85, 0.10, 0.05])
            })
            large_table = KData("Transactions (5K)", KTable(large_df))
            self._project.add_data(large_table)
            
            # Very large table (tens of thousands)
            very_large_df = pd.DataFrame({
                'Sensor_ID': range(1, 25001),
                'Timestamp': pd.date_range('2024-01-01', periods=25000, freq='min'),
                'Temperature': np.random.normal(20, 5, 25000).round(2),
                'Humidity': np.random.uniform(30, 90, 25000).round(2),
                'Pressure': np.random.normal(1013, 10, 25000).round(2),
                'Location': np.random.choice(['Building A', 'Building B', 'Building C'], 25000)
            })
            very_large_table = KData("Sensor Data (25K)", KTable(very_large_df))
            self._project.add_data(very_large_table)
            
            # Literals - different types
            int_literal = KData("Integer Value", KLiteral(42))
            self._project.add_data(int_literal)
            
            float_literal = KData("Float Value", KLiteral(3.14159))
            self._project.add_data(float_literal)
            
            string_literal = KData("String Value", KLiteral("Hello, Kira!"))
            self._project.add_data(string_literal)
            
            bool_literal = KData("Boolean Value", KLiteral(True))
            self._project.add_data(bool_literal)
            
            # Error elements - KData with error but no value
            # Create concrete error classes
            from kira.kexpections.kexception import KException
            
            class SimpleError(KException):
                def __init__(self, message):
                    self._message = message
                def __str__(self):
                    return self._message
            
            error_data = KData("Failed Calculation", None, SimpleError("Division by zero occurred"))
            self._project.add_data(error_data)
            
            # Another error with different message
            error_data2 = KData("Missing Data", None, SimpleError("Required data source not found"))
            self._project.add_data(error_data2)
            
            # Add a welcome message
            self._project.log(
                "Welcome to Kira! Select an element in the Explorer to see its preview.",
                "info"
            )
            self._project.log(
                f"Loaded {len(self._project.get_all_data())} test elements.",
                "success"
            )
            
            # Demonstrate "Jump to Source"
            self._project.log(
                "There was an error in this data object.",
                "error",
                source=error_data
            )
        except Exception as e:
            # If imports fail, just show an error
            self._project.log(f"Failed to load test elements: {str(e)}", "error")
    
    def add_tab(self, widget: QWidget, title: str) -> int:
        """
        Add a new tab to the main window.
        
        Args:
            widget: The widget to add as a tab
            title: The tab title
            
        Returns:
            The index of the newly added tab
        """
        return self._tab_widget.addTab(widget, title)
    
    @property
    def homepage(self) -> HomepageTab:
        """Get the homepage tab."""
        return self._homepage


def run_app():
    """Run the Kira GUI application."""
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QFont
    
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    run_app()

