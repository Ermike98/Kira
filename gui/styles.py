"""
Styling definitions for the Kira GUI application.
"""

LIGHT_THEME = """
    /* Main Window */
    QMainWindow {
        background-color: #f0f4f8; /* Light blue tint */
    }
    
    /* Homepage and Containers */
    QWidget#HomepageTab, QWidget#WorkflowTab {
        background-color: #f0f4f8;
    }
    
    QFrame#ExplorerContainer, QFrame#EditorContainer, QFrame#ControlContainer, QFrame#PreviewContainer {
        background-color: transparent;
        border: none;
    }
    QTabWidget::pane {
        border: 1px solid #d0d0d0;
        background: #f0f4f8;
        top: -1px;
    }
    
    QTabBar::tab {
        background: #e8e8e8;
        border: 1px solid #d0d0d0;
        padding: 4px 15px;
        margin-right: 2px;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
    }
    
    QTabBar::tab:selected {
        background: white;
        border-bottom-color: white;
        font-weight: bold;
    }
    
    QTabBar::tab:!selected {
        margin-top: 2px;
    }
    
    /* Buttons */
    QPushButton {
        background-color: #ffffff;
        border: 1px solid #d0d0d0;
        padding: 6px 12px;
        border-radius: 4px;
        text-align: left;
        font-size: 13px;
    }
    
    QPushButton:hover {
        background-color: #f0f0f0;
        border-color: #0078d4;
    }
    
    QPushButton:pressed {
        background-color: #e0e0e0;
    }
    
    QPushButton:checked {
        background-color: #0078d4;
        color: white;
        border-color: #005a9e;
    }
    
    /* Scroll Areas */
    QScrollArea {
        border: 1px solid #d0d0d0;
        background: white;
    }
    
    QScrollArea#PreviewScrollArea, QScrollArea#ExplorerScrollArea, QWidget#PreviewScrollContainer, QWidget#ExplorerContainer {
        background-color: transparent;
        border: none;
    }
    
    /* Labels */
    QLabel {
        color: #333333;
        font-size: 13px;
    }
    
    /* Text Edit / Plain Text Edit */
    QTextEdit, QPlainTextEdit {
        background-color: white;
        border: 1px solid #d0d0d0;
        color: #333333;
        font-family: 'Consolas', 'Courier New', monospace;
        font-size: 12px;
    }
    
    /* Table View */
    QTableView {
        background-color: white;
        gridline-color: #e0e0e0;
        color: #333333;
        font-size: 13px;
        border: 1px solid #d0d0d0;
        selection-background-color: #0078d4;
        selection-color: white;
    }
    
    QHeaderView::section {
        background-color: #f9f9f9;
        color: #666666;
        padding: 6px;
        border: 1px solid #d0d0d0;
        font-weight: bold;
    }
    
    /* Splitter */
    QSplitter::handle {
        background-color: transparent;
    }
    
    QSplitter::handle:hover {
        background-color: #0078d4;
    }
    
    QSplitter::handle:horizontal {
        width: 4px;
    }
    
    QSplitter::handle:vertical {
        height: 4px;
    }
    
    QSplitter::handle:pressed {
        background-color: #005a9e;
    }
    
    /* Panel Frames */
    QFrame#ExplorerPanel, QFrame#WorkflowEditorPanel, QFrame#ControlPanel, QFrame#PreviewPanel {
        background-color: white;
        border: none;
        border-radius: 8px;
    }
"""

