import sys
from pathlib import Path
# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication, QMainWindow
from gui.components.workflow_editor import WorkflowEditor
from gui.components.node_items import WorkflowNodeItem
from gui.style import LIGHT_THEME

def verify_ui():
    app = QApplication(sys.argv)
    app.setStyleSheet(LIGHT_THEME)
    
    window = QMainWindow()
    window.setWindowTitle("Verify Node Editor UI")
    # Create a dummy project structure to test node extraction
    from kproject.kproject import KProject
    from kproject.kpersistence_manager import KPersistenceManager
    from gui.qt_project import QTProject
    
    pm = KPersistenceManager(None) # In-memory
    kp = KProject(pm)
    project = QTProject(kp)
    
    editor = WorkflowEditor(project)
    window.setCentralWidget(editor)
    
    # Initialize with some inputs/outputs
    editor.set_workflow("test_workflow", "")
    
    # Add dummy nodes to verify rendering
    node1 = WorkflowNodeItem("node_1", "Mean", ["array"], ["result"])
    node1.setPos(100, 100)
    editor.scene.addItem(node1)
    
    node2 = WorkflowNodeItem("node_2", "Add", ["a", "b"], ["out"])
    node2.setPos(400, 150)
    editor.scene.addItem(node2)
    
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    verify_ui()
