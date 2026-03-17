from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QTextEdit, QPushButton, 
    QDialogButtonBox
)
from PySide6.QtCore import Qt

class AddVariableDialog(QDialog):
    """Dialog for creating a new variable."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Variable")
        self.setMinimumWidth(400)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Name
        layout.addWidget(QLabel("Variable Name:"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g. results_sum")
        layout.addWidget(self.name_edit)
        
        # Expression
        layout.addWidget(QLabel("Expression (e.g. name = 10 + 5):"))
        self.expr_edit = QTextEdit()
        self.expr_edit.setPlaceholderText("x = 10")
        self.expr_edit.setMaximumHeight(100)
        layout.addWidget(self.expr_edit)
        
        # Buttons
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

    def get_data(self):
        return self.name_edit.text(), self.expr_edit.toPlainText()
