"""
Main entry point to run the Kira GUI application.
"""
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from PySide6.QtWidgets import QApplication
from gui.main_window import MainWindow
from gui.qt_project import QTProject
from kproject.kproject import KProject
from kproject.kpersistence_manager import KPersistenceManager

def run_app():
    app = QApplication(sys.argv)
    
    # Initialize Core (In-memory by default, can be extended for file loading)
    pm = KPersistenceManager(None)
    kp = KProject(pm)
    
    # Wrap for Qt Reactivity
    qp = QTProject(kp)
    
    # Launch Main Window
    window = MainWindow(qp)
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    run_app()
