from typing import Optional, List
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLabel, QLineEdit, QFrame
from PySide6.QtCore import Qt, Signal

from gui.qt_project import QTProject
from gui.utils import colors
from gui import style_system
from repl.repl_backend import KiraREPL, format_value
from kproject.kevent import KEventTypes
from kproject.kevaluator import KVariableStatus


class ReplLineEdit(QLineEdit):
    """Custom QLineEdit that captures Up/Down arrows for command history navigation."""
    up_pressed = Signal()
    down_pressed = Signal()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Up:
            self.up_pressed.emit()
        elif event.key() == Qt.Key_Down:
            self.down_pressed.emit()
        else:
            super().keyPressEvent(event)


class QReplConsole(QWidget):
    """
    An interactive, non-blocking REPL Console widget for the Kira GUI application.
    Integrates with the running QTProject session, desugars expressions,
    and updates reactively when evaluations finish without blocking the main thread.
    """

    def __init__(self, project: QTProject, parent=None):
        super().__init__(parent)
        self.project = project
        self.repl = KiraREPL(self.project.kproject)
        self.setObjectName("ReplConsole")

        # Command history for arrow navigation
        self.cmd_history: List[str] = []
        self.history_index: int = -1
        self.temp_input: str = ""

        # Reactive tracking for running variable evaluation
        self.waiting_target: Optional[str] = None

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 1. Scrollable History View (Read-Only)
        self.history_view = QTextEdit()
        self.history_view.setReadOnly(True)
        self.history_view.setStyleSheet(f"""
            QTextEdit {{
                background-color: {colors.bg_panel};
                color: {colors.text_primary};
                font-family: {style_system.font_family_mono};
                font-size: {style_system.font_small};
                border: none;
                padding: 12px;
            }}
        """)
        layout.addWidget(self.history_view)

        # Welcome message
        self.history_view.append(
            f"<font color='{colors.zinc_500}'><b>Kira Interactive REPL Console</b></font><br>"
            f"<font color='{colors.zinc_400}'>Evaluate variables, write workflows, or type expressions directly.</font><br>"
            f"<font color='{colors.zinc_400}'>Type exit/quit to exit or clear to clear console.</font><br>"
            f"<font color='{colors.zinc_300}'>--------------------------------------------------</font>"
        )

        # 2. Input Bar Frame
        self.input_frame = QFrame()
        self.input_frame.setFixedHeight(36)
        self.input_frame.setStyleSheet(f"""
            QFrame {{
                border-top: 1px solid {colors.border_light};
                background-color: {colors.bg_base};
            }}
        """)
        
        input_layout = QHBoxLayout(self.input_frame)
        input_layout.setContentsMargins(8, 0, 8, 0)
        input_layout.setSpacing(4)

        # Prompt Label
        self.prompt_label = QLabel("kira> ")
        self.prompt_label.setStyleSheet(f"""
            QLabel {{
                color: {colors.accent_base};
                font-family: {style_system.font_family_mono};
                font-size: {style_system.font_small};
                font-weight: bold;
            }}
        """)
        input_layout.addWidget(self.prompt_label)

        # Line Input field
        self.line_input = ReplLineEdit()
        self.line_input.setPlaceholderText("Type Kira expression...")
        self.line_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: transparent;
                color: {colors.text_primary};
                font-family: {style_system.font_family_mono};
                font-size: {style_system.font_small};
                border: none;
            }}
        """)
        input_layout.addWidget(self.line_input)
        layout.addWidget(self.input_frame)

    def _connect_signals(self):
        self.line_input.returnPressed.connect(self._on_execute)
        self.line_input.up_pressed.connect(self._on_history_up)
        self.line_input.down_pressed.connect(self._on_history_down)
        self.project.status_changed.connect(self._on_status_changed)

    def _on_execute(self):
        command = self.line_input.text().strip()
        if not command:
            return

        # Record in history list
        self.cmd_history.append(command)
        self.history_index = -1
        self.temp_input = ""

        # Clear input field
        self.line_input.clear()

        # Echo the command in history view
        self.history_view.append(
            f"<font color='{colors.zinc_400}'><b>kira&gt;</b></font> "
            f"<font color='{colors.text_primary}'>{command}</font>"
        )

        # Parse command non-blockingly
        parsed = self.repl._parse_line(command)
        t = parsed["type"]

        if t == "empty":
            return

        if t == "command":
            cmd = parsed["rewritten"].lower()
            if cmd in ("clear", "cls"):
                self.history_view.clear()
            elif cmd in ("exit", "quit"):
                self.history_view.append(f"<font color='{colors.zinc_400}'>REPL session closed. Exit GUI to close application.</font>")
            return

        if t == "error":
            self.history_view.append(f"<font color='{colors.status_error}'>Syntax Error: {parsed['error']}</font>")
            return

        if t == "query":
            # Direct lookup is instant and synchronous
            name = parsed["target"]
            try:
                value = self.project.get_value(name)
                output = format_value(name, value)
                self._append_output(output, success=True)
            except Exception as e:
                self._append_output(f"Error: {e}", success=False)
            return

        # Assignment, expression, or workflow
        target = parsed["target"]
        rewritten = parsed["rewritten"]
        event_type = KEventTypes.AddWorkflow if t == "workflow" else KEventTypes.AddVariable

        if t == "workflow":
            # Workflows evaluate instantly in the manager structural layers
            try:
                self.project.process_event(event_type, target, rewritten)
                self._append_output(f"Workflow '{target}' defined successfully.", success=True)
            except Exception as e:
                self._append_output(f"Error compiling workflow: {e}", success=False)
            return

        # For assignments and expressions, we dispatch and set waiting target
        self.waiting_target = target
        try:
            self.project.process_event(event_type, target, rewritten)
        except Exception as e:
            self.waiting_target = None
            self._append_output(f"Error dispatching variable event: {e}", success=False)

    def _on_status_changed(self, statuses: dict):
        """Reacts to background status updates non-blockingly."""
        if not self.waiting_target:
            return

        target = self.waiting_target
        if target in statuses:
            status = statuses[target]
            status_str = str(status.value) if hasattr(status, "value") else str(status)

            if status_str in ("READY", "ERROR"):
                # Evaluation finished! Reset wait state
                self.waiting_target = None

                # Fetch and format result
                try:
                    value = self.project.get_value(target)
                    output = format_value(target, value)
                    self._append_output(output, success=(status_str == "READY"))
                except Exception as e:
                    self._append_output(f"Error fetching evaluated value: {e}", success=False)

    def _append_output(self, text: str, success: bool = True):
        color = colors.text_secondary if success else colors.status_error
        # Indent each line for clean output alignment
        indented = "<br>".join(f"  {line}" for line in text.splitlines())
        self.history_view.append(f"<font color='{color}'>{indented}</font>")
        
        # Scroll to bottom
        scrollbar = self.history_view.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _on_history_up(self):
        if not self.cmd_history:
            return

        if self.history_index == -1:
            # Save unsent input
            self.temp_input = self.line_input.text()
            self.history_index = len(self.cmd_history) - 1
        elif self.history_index > 0:
            self.history_index -= 1

        self.line_input.setText(self.cmd_history[self.history_index])

    def _on_history_down(self):
        if not self.cmd_history or self.history_index == -1:
            return

        if self.history_index == len(self.cmd_history) - 1:
            self.history_index = -1
            self.line_input.setText(self.temp_input)
        else:
            self.history_index += 1
            self.line_input.setText(self.cmd_history[self.history_index])
