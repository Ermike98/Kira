"""
gui/components/step_editor.py
------------------------------
Visual Pipeline Editor for variables.

Decomposes a variable's code (e.g. ``y = Sales_Table |> head(10) |> select(["Region"])``)
into an editable list of steps: a Source card followed by zero or more
function-step cards.  Each card exposes inline text inputs for the
function's parameters (the first "piped" arg is hidden).

On blur of any input the full code string is recomposed, validated via
the tokenizer + parser, and — if valid — committed as an ``AddVariable``
event through ``QTProject``.
"""

from __future__ import annotations

import ast
import re
import logging
from dataclasses import dataclass, field
from typing import Optional, List, Tuple, TYPE_CHECKING

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QFrame, QScrollArea, QPushButton,
    QListWidget, QListWidgetItem, QAbstractItemView,
    QSizePolicy, QCompleter, QListView
)
from PySide6.QtCore import Qt, Signal, QSize, QTimer, QSortFilterProxyModel, QModelIndex, QMimeData
from PySide6.QtGui import QFont, QStandardItemModel, QStandardItem, QDrag, QPixmap, QPainter
from gui.components.sidebar import get_icon_name_for_type, type_icon

from gui.utils import colors

if TYPE_CHECKING:
    from gui.qt_project import QTProject

logger = logging.getLogger("kira.step_editor")

# ---------------------------------------------------------------------------#
#  0. Autocomplete Utilities                                                  #
# ---------------------------------------------------------------------------#

class SuggestionFilterModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._prefix = ""
        self.setSortCaseSensitivity(Qt.CaseInsensitive)
        self.setDynamicSortFilter(True)

    def set_search_prefix(self, prefix: str):
        self._prefix = prefix.lower()
        self.invalidate()
        self.sort(0)

    def lessThan(self, left: QModelIndex, right: QModelIndex) -> bool:
        left_text = self.sourceModel().data(left, Qt.DisplayRole) or ""
        right_text = self.sourceModel().data(right, Qt.DisplayRole) or ""
        left_type = self.sourceModel().data(left, Qt.UserRole + 1) or 2
        right_type = self.sourceModel().data(right, Qt.UserRole + 1) or 2

        left_starts = left_text.lower().startswith(self._prefix) if self._prefix else False
        right_starts = right_text.lower().startswith(self._prefix) if self._prefix else False
        
        if left_starts != right_starts:
            return left_starts

        if left_type != right_type:
            return left_type < right_type

        return left_text.lower() < right_text.lower()


class WordCompleter(QCompleter):
    def __init__(self, model, parent=None):
        super().__init__(model, parent)
        self.setCompletionRole(Qt.DisplayRole)
        self.setFilterMode(Qt.MatchContains)
        self.setCaseSensitivity(Qt.CaseInsensitive)
        self.setModelSorting(QCompleter.UnsortedModel)
        self.setWidget(parent)

        self._current_text = ""
        self._cursor_pos = 0
        self._word_start = 0
        self._word_len = 0
        self.target_cursor_pos = -1

    def update_context(self, text: str, cursor_pos: int):
        self._current_text = text
        self._cursor_pos = cursor_pos
        
        left_text = text[:cursor_pos]
        match = re.search(r'[a-zA-Z_]\w*$', left_text)
        word = match.group(0) if match else ""
        if match:
            self._word_start = match.start()
            self._word_len = len(word)
        else:
            self._word_start = cursor_pos
            self._word_len = 0

    def splitPath(self, path: str):
        left_text = path[:self._cursor_pos]
        match = re.search(r'[a-zA-Z_]\w*$', left_text)
        word = match.group(0) if match else ""
        
        proxy = self.model()
        if isinstance(proxy, SuggestionFilterModel):
            proxy.set_search_prefix(word)
            
        return [word]

    def pathFromIndex(self, index: QModelIndex) -> str:
        completion_val = self.model().data(index, Qt.UserRole)
        if not completion_val:
            completion_val = self.model().data(index, Qt.DisplayRole)
            
        left = self._current_text[:self._word_start]
        right = self._current_text[self._word_start + self._word_len:]
        
        self.target_cursor_pos = self._word_start + len(completion_val)
        if completion_val.endswith("()"):  # Specifically set cursor between parens
            self.target_cursor_pos -= 1
            
        return left + completion_val + right


def attach_word_completer(line_edit: QLineEdit, source_model: QStandardItemModel):
    proxy = SuggestionFilterModel(line_edit)
    proxy.setSourceModel(source_model)
    proxy.sort(0)
    
    completer = WordCompleter(proxy, line_edit)
    popup = QListView()
    popup.setObjectName("AutocompletePopup")
    completer.setPopup(popup)
    line_edit.setCompleter(completer)
    
    def on_text_edited(text):
        completer.update_context(text, line_edit.cursorPosition())
        completer.setCompletionPrefix(text)
        
    line_edit.textEdited.connect(on_text_edited)
    
    def on_activated(text):
        target = getattr(completer, "target_cursor_pos", -1)
        if target >= 0:
            def _safe_set_cursor():
                try:
                    # Check if widget still exists
                    if not line_edit.isWidgetType():
                        return
                    line_edit.setCursorPosition(target)
                except (RuntimeError, AttributeError):
                    pass
            QTimer.singleShot(0, _safe_set_cursor)
            
    completer.activated.connect(on_activated)


# ---------------------------------------------------------------------------#
#  1. Pipeline Utilities                                                      #
# ---------------------------------------------------------------------------#

def decompose_variable_code(code: str) -> Tuple[str, str, List[str]]:
    """Split a variable code string into (target, source, [step, ...]).

    Uses the Kira tokenizer to find the assignment ``=`` and top-level
    ``|>`` tokens (respecting bracket depth so nested pipes are not split).

    Returns
    -------
    target : str
        Variable name (left of ``=``).
    source : str
        Source expression string (first segment after ``=``).
    steps : list[str]
        Remaining pipe-step strings (e.g. ``["head(10)", "select([\"R\"])"]``).
    """
    from kira.klanguage.ktokenizer import ktokenize, KTokenType

    tokens = ktokenize(code)
    # Strip whitespace tokens for analysis but keep positions in source
    meaningful = [(t, i) for i, t in enumerate(tokens) if t.token_type != KTokenType.WHITESPACE]

    # --- Find assignment '=' ---
    assign_char_pos = None
    for t, _ in meaningful:
        if t.token_type == KTokenType.ASSIGN:
            # Find position in original code string
            # We'll locate by scanning the code for '=' that's not '=='
            break

    # Simpler: find first '=' that is ASSIGN (not '==') by re-scanning code
    # We'll use a character-offset approach instead
    assign_idx = _find_assign_offset(code)
    if assign_idx is None:
        # No assignment — treat entire code as source
        return ("", code.strip(), [])

    target = code[:assign_idx].strip()
    rhs = code[assign_idx + 1:].strip()

    # --- Split RHS by top-level |> ---
    parts = _split_by_toplevel_pipe(rhs)
    source = parts[0].strip()
    steps = [p.strip() for p in parts[1:]]

    return target, source, steps


def _find_assign_offset(code: str) -> Optional[int]:
    """Return the character offset of the first top-level ``=`` (not ``==``)."""
    i = 0
    depth = 0
    while i < len(code):
        ch = code[i]
        if ch in ("(", "["):
            depth += 1
        elif ch in (")", "]"):
            depth -= 1
        elif ch == "=" and depth == 0:
            # Check it's not '=='
            if i + 1 < len(code) and code[i + 1] == "=":
                i += 2
                continue
            # Check it's not '<=' or '>=' or '!='
            if i > 0 and code[i - 1] in ("<", ">", "!"):
                i += 1
                continue
            return i
        elif ch in ('"', "'"):
            # Skip string
            quote = ch
            i += 1
            while i < len(code) and code[i] != quote:
                i += 1
        i += 1
    return None


def _split_by_toplevel_pipe(expr: str) -> List[str]:
    """Split *expr* by top-level ``|>`` tokens, respecting brackets and strings."""
    parts: List[str] = []
    depth = 0
    current_start = 0
    i = 0
    while i < len(expr):
        ch = expr[i]
        if ch in ("(", "["):
            depth += 1
        elif ch in (")", "]"):
            depth -= 1
        elif ch in ('"', "'"):
            quote = ch
            i += 1
            while i < len(expr) and expr[i] != quote:
                i += 1
        elif ch == "$":
            # Skip formula $...$
            i += 1
            while i < len(expr) and expr[i] != "$":
                i += 1
        elif ch == "|" and depth == 0:
            if i + 1 < len(expr) and expr[i + 1] == ">":
                parts.append(expr[current_start:i].strip())
                i += 2  # skip |>
                current_start = i
                continue
        i += 1
    # Last segment
    parts.append(expr[current_start:].strip())
    return parts


def compose_variable_code(target: str, source: str, steps: List[Tuple[str, List[str]]]) -> str:
    """Build a full variable assignment string from parts.

    Parameters
    ----------
    target : str
        Variable name.
    source : str
        Source expression string.
    steps : list of (func_name, [arg_str, ...])
        Each step's function name and non-piped argument strings.
    """
    code = f"{target} = {source}"
    for func_name, args in steps:
        if args:
            args_str = ", ".join(args)
            code += f" |> {func_name}({args_str})"
        else:
            code += f" |> {func_name}"
    return code


def parse_step_string(step_str: str) -> Tuple[str, List[str]]:
    """Parse a step string like ``head(10, 5)`` into ``("head", ["10", "5"])``.

    Also handles zero-arg calls: ``"transpose"`` → ``("transpose", [])``.
    """
    step_str = step_str.strip()
    paren_idx = step_str.find("(")
    if paren_idx == -1:
        return (step_str, [])

    func_name = step_str[:paren_idx].strip()
    # Extract content between outer parens
    inner = step_str[paren_idx + 1:]
    if inner.endswith(")"):
        inner = inner[:-1]

    args = _split_args(inner)
    return func_name, args


def _split_args(inner: str) -> List[str]:
    """Split a comma-separated argument string respecting brackets and strings."""
    args: List[str] = []
    depth = 0
    current_start = 0
    i = 0
    while i < len(inner):
        ch = inner[i]
        if ch in ("(", "["):
            depth += 1
        elif ch in (")", "]"):
            depth -= 1
        elif ch in ('"', "'"):
            quote = ch
            i += 1
            while i < len(inner) and inner[i] != quote:
                i += 1
        elif ch == "$":
            i += 1
            while i < len(inner) and inner[i] != "$":
                i += 1
        elif ch == "," and depth == 0:
            args.append(inner[current_start:i].strip())
            current_start = i + 1
        i += 1
    # Last arg
    last = inner[current_start:].strip()
    if last:
        args.append(last)
    return args


# ---------------------------------------------------------------------------#
#  2. Data Classes                                                            #
# ---------------------------------------------------------------------------#

@dataclass
class PipelineStep:
    """In-memory representation of one step in the pipeline."""
    func_name: str = ""
    param_names: List[str] = field(default_factory=list)
    param_values: List[str] = field(default_factory=list)
    param_defaults: List[Optional[str]] = field(default_factory=list)


# ---------------------------------------------------------------------------#
#  3. Source Card                                                             #
# ---------------------------------------------------------------------------#

class SourceCard(QFrame):
    """Card for the pipeline source expression — visually distinct from steps."""

    source_changed = Signal()

    def __init__(self, source_text: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("SourceCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)


        # Input
        self.input = QLineEdit(source_text)
        self.input.setObjectName("StepSourceInput")
        self.input.setPlaceholderText("e.g. Sales_Table, 1250000, range(1, 10)")
        self.input.editingFinished.connect(self.source_changed.emit)
        layout.addWidget(self.input)

    def set_completer_model(self, model: QStandardItemModel):
        if not self.input.completer():
            attach_word_completer(self.input, model)

    @property
    def value(self) -> str:
        return self.input.text().strip()

    @value.setter
    def value(self, v: str):
        self.input.setText(v)


# ---------------------------------------------------------------------------#
#  4. Step Card                                                               #
# ---------------------------------------------------------------------------#

class StepCard(QFrame):
    """Card for a single function step in the pipeline."""

    step_changed = Signal()
    step_deleted = Signal()
    func_name_changed = Signal(str, bool)  # name, should_focus_params

    def __init__(self, step: PipelineStep, step_index: int = 0, parent=None):
        super().__init__(parent)
        self.setObjectName("StepCard")
        self._step = step
        self._step_index = step_index
        self._param_inputs: List[QLineEdit] = []
        self._func_model: Optional[QStandardItemModel] = None
        self._mixed_model: Optional[QStandardItemModel] = None

        self._is_entering = False
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(12, 10, 12, 10)
        self._main_layout.setSpacing(6)

        # ---- Header ----
        header = QHBoxLayout()
        header.setSpacing(8)

        # Drag handle
        self._drag_handle = QLabel("≡")
        self._drag_handle.setObjectName("StepDragHandle")
        self._drag_handle.setCursor(Qt.OpenHandCursor)
        header.addWidget(self._drag_handle)

        if not step.func_name:
            self._drag_handle.hide()


        # Function name (editable if empty, label if set)
        if step.func_name:
            self._func_label = QLabel(step.func_name)
            self._func_label.setObjectName("StepFuncName")
            header.addWidget(self._func_label)
            # Use fixed index (1) as badge is removed
            # self._func_label is at index 1 (after drag handle)
            self._func_input = None
        else:
            self._func_input = QLineEdit()
            self._func_input.setObjectName("StepFuncInput")
            self._func_input.setPlaceholderText("function name…")
            self._func_input.editingFinished.connect(self._on_func_name_entered)
            self._func_input.returnPressed.connect(self._on_func_return)
            header.addWidget(self._func_input)
            # Index 1 (after drag handle)
            self._func_label = None

        header.addStretch()

        # Delete button
        self._del_btn = QPushButton("×")
        self._del_btn.setObjectName("StepDeleteButton")
        self._del_btn.setFixedSize(24, 24)
        self._del_btn.setCursor(Qt.PointingHandCursor)
        self._del_btn.clicked.connect(self.step_deleted.emit)
        header.addWidget(self._del_btn)

        if not step.func_name:
            self._del_btn.hide()

        self._main_layout.addLayout(header)

        # ---- Parameter inputs ----
        self._params_container = QWidget()
        self._params_layout = QVBoxLayout(self._params_container)
        self._params_layout.setContentsMargins(0, 0, 0, 0)
        self._params_layout.setSpacing(4)
        self._main_layout.addWidget(self._params_container)

        self._build_param_inputs()

    def _build_param_inputs(self):
        """Create text inputs for each parameter."""
        # Clear existing
        self._param_inputs.clear()
        while self._params_layout.count():
            item = self._params_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for name, value, default in zip(
            self._step.param_names,
            self._step.param_values,
            self._step.param_defaults
        ):
            row = QHBoxLayout()
            row.setSpacing(8)

            lbl = QLabel(name)
            lbl.setObjectName("StepParamLabel")
            lbl.setFixedWidth(90)
            lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            row.addWidget(lbl)

            inp = QLineEdit(value)
            inp.setObjectName("StepParamInput")
            if default is not None:
                inp.setPlaceholderText(f"default: {default}")
            inp.editingFinished.connect(self._on_param_changed)
            inp.returnPressed.connect(lambda i=len(self._param_inputs): self._on_param_return_pressed(i))
            row.addWidget(inp)

            self._param_inputs.append(inp)
            self._params_layout.addLayout(row)

        # Re-apply model to new param inputs if available
        if self._mixed_model:
            self.set_models(self._func_model, self._mixed_model)

    def _on_func_return(self):
        self._is_entering = True

    def _on_func_name_entered(self):
        """User typed a function name via Blur or Enter."""
        if self._func_input:
            name = self._func_input.text().strip()
            if name:
                self.func_name_changed.emit(name, self._is_entering)
        self._is_entering = False

    def _on_param_return_pressed(self, index: int):
        """User pressed enter in a parameter input."""
        if index < len(self._param_inputs) - 1:
            self._param_inputs[index + 1].setFocus()
            self._param_inputs[index + 1].selectAll()
        else:
            self.step_changed.emit()

    def focus_first_param(self):
        if self._param_inputs:
            self._param_inputs[0].setFocus()
            self._param_inputs[0].selectAll()
        else:
            # If no params, we probably already committed via func_name_changed
            # but we can emit step_changed just in case to ensure project sync
            self.step_changed.emit()

    def focus_param(self, index: int):
        if 0 <= index < len(self._param_inputs):
            self._param_inputs[index].setFocus()
            self._param_inputs[index].selectAll()

    def _on_param_changed(self):
        """Sync param values back into the step model and emit."""
        for i, inp in enumerate(self._param_inputs):
            if i < len(self._step.param_values):
                self._step.param_values[i] = inp.text().strip()
        self.step_changed.emit()

    def update_step(self, step: PipelineStep, index: int):
        """Replace the displayed step and rebuild param inputs."""
        self._step = step
        self._step_index = index

        # Replace function name label
        if self._func_label:
            self._func_label.setText(step.func_name)
        elif self._func_input and step.func_name:
            # Switch from input to label
            self._func_input.setVisible(False)
            self._func_label = QLabel(step.func_name)
            self._func_label.setObjectName("StepFuncName")
            # Insert after badge
            header_layout = self._main_layout.itemAt(0).layout()
            # Insert after drag handle (index 0)
            header_layout.insertWidget(1, self._func_label)

        self._build_param_inputs()

    def set_models(self, func_model: QStandardItemModel, mixed_model: QStandardItemModel):
        self._func_model = func_model
        self._mixed_model = mixed_model

        if self._func_input:
            if not self._func_input.completer():
                attach_word_completer(self._func_input, func_model)

        for inp in self._param_inputs:
            if not inp.completer():
                attach_word_completer(inp, mixed_model)

    def mousePressEvent(self, event):
        if (event.button() == Qt.LeftButton and 
            hasattr(self, "_drag_handle") and
            self._drag_handle.isVisible() and 
            self._drag_handle.geometry().contains(event.pos())):
            self._start_drag()
        super().mousePressEvent(event)

    def _start_drag(self):
        drag = QDrag(self)
        mime = QMimeData()
        mime.setData("application/x-kira-step-index", str(self._step_index).encode())
        drag.setMimeData(mime)
        
        pixmap = self.grab()
        drag.setPixmap(pixmap)
        drag.setHotSpot(self._drag_handle.geometry().center())
        
        drag.exec(Qt.MoveAction)

    @property
    def step(self) -> PipelineStep:
        return self._step


# ---------------------------------------------------------------------------#
#  5. Pipeline Arrow (visual connector)                                       #
# ---------------------------------------------------------------------------#

class _PipelineArrow(QWidget):
    """A small "↓" connector between cards."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(20)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)
        lbl = QLabel("↓")
        lbl.setObjectName("PipelineArrow")
        lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl)


# ---------------------------------------------------------------------------#
#  6. Step Editor Panel                                                       #
# ---------------------------------------------------------------------------#

class StepEditorPanel(QWidget):
    """Full pipeline editor panel.

    Shows a SourceCard + a list of StepCards with drag-and-drop reordering.
    On any edit, recomposes the code, validates parsing, and fires an
    ``AddVariable`` event.
    """

    def __init__(self, project: QTProject, variable_name: str, parent=None):
        super().__init__(parent)
        self.project = project
        self.variable_name = variable_name
        self.setObjectName("StepEditorPanel")

        self._source_text: str = ""
        self._steps: List[PipelineStep] = []
        self._step_cards: List[StepCard] = []
        self._committing = False  # re-entrance guard
        self._context_state: dict = {}
        self._func_model = QStandardItemModel()
        self._mixed_model = QStandardItemModel()
        self._status: str = ""

        # ---- Layout ----
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)


        # Header
        self._header = QWidget()
        self._header.setObjectName("StepEditorHeader")
        header_layout = QHBoxLayout(self._header)
        header_layout.setContentsMargins(16, 12, 16, 10)
        self._title = QLabel(self.variable_name)
        self._title.setObjectName("StepEditorTitle")
        self._title.setAutoFillBackground(True)
        header_layout.addWidget(self._title)
        header_layout.addStretch()
        outer.addWidget(self._header)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        outer.addWidget(scroll)

        self._content = QWidget()
        self._content.setObjectName("StepEditorContent")
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(12, 8, 12, 12)
        self._content_layout.setSpacing(0)
        self._content_layout.setAlignment(Qt.AlignTop)
        scroll.setWidget(self._content)
        scroll.setStyleSheet(f"QScrollArea {{ background-color: {colors.bg_base}; border: none; }}")
        self._content.setStyleSheet(f"#StepEditorContent {{ background-color: {colors.bg_base}; }}")

        # Source card (always present)
        self._source_card = SourceCard("")
        self._source_card.source_changed.connect(self._on_commit)
        self._content_layout.addWidget(self._source_card)

        # Steps container
        self._steps_widget = QWidget()
        self._steps_layout = QVBoxLayout(self._steps_widget)
        self._steps_layout.setContentsMargins(0, 0, 0, 0)
        self._steps_layout.setSpacing(0)
        self._steps_layout.setAlignment(Qt.AlignTop)
        self._content_layout.addWidget(self._steps_widget)
        
        # Tighten margin between Source and Steps
        self._steps_layout.setContentsMargins(0, 4, 0, 0)

        self._content_layout.addStretch()

        # Reorder indicator (a thin line showing where a drop will occur)
        # Parented to 'self' so we can move it freely over the layout
        self._reorder_indicator = QFrame(self)
        self._reorder_indicator.setObjectName("ReorderIndicator")
        self._reorder_indicator.setFixedHeight(2)
        self._reorder_indicator.setStyleSheet(f"background-color: {colors.accent_base};")
        self._reorder_indicator.hide()

        self.setAcceptDrops(True)

        # ---- Initial load ----
        self.project.history_updated.connect(self._refresh_autocomplete_cache)
        self.project.status_changed.connect(self._on_status_changed)
        
        self._refresh_autocomplete_cache()
        self._load_from_project()
        
        # Trigger initial status update with a small delay to allow visual transition from grey
        QTimer.singleShot(200, lambda: self._on_status_changed(self.project.kproject.get_all_statuses()))

    # ---- Public API ----

    def refresh(self):
        """Reload from the project state (e.g. after undo/redo)."""
        self._load_from_project()

    def _on_status_changed(self, statuses: dict):
        """Update visual feedback based on the variable's evaluation status."""
        status_obj = statuses.get(self.variable_name)
        if not status_obj:
            return

        status_str = status_obj.name # WAITING, PROCESSING, READY, ERROR
        
        # Check for logic errors (computed but empty/invalid)
        if status_str == "READY":
            kdata = self.project.get_value(self.variable_name)
            if not bool(kdata):
                status_str = "ERROR"

        if status_str == self._status:
            return
            
        self._status = status_str
        self._header.setProperty("status", status_str)
        self._title.setProperty("status", status_str)
        
        # Refresh styling
        self._header.style().unpolish(self._header)
        self._header.style().polish(self._header)
        self._title.style().unpolish(self._title)
        self._title.style().polish(self._title)
        
    def _refresh_autocomplete_cache(self):
        """Update the completer models when the history/context changes."""
        self._context_state = self.project.get_context_state()

        self._func_model.clear()
        self._mixed_model.clear()

        # Combine nodes + library for function list
        func_objects = self._context_state.get("node", []) + self._context_state.get("library", [])
        
        from kira.knodes.knode import KNode
        
        func_items = []
        for obj in func_objects:
            if not re.match(r'^[a-zA-Z_]\w*$', obj.name):
                continue
                
            display_name = obj.name
            insert_val = f"{obj.name}()"
            
            if isinstance(obj, KNode) and hasattr(obj, "input_names"):
                if obj.input_names:
                    display_name = f"{obj.name}({', '.join(obj.input_names)})"

            item = QStandardItem(display_name)
            item.setData(obj.name, Qt.UserRole)  # Keep plain name for func_input
            item.setData(2, Qt.UserRole + 1) # Priority 2 for functions
            
            icon_name = get_icon_name_for_type(obj.type)
            if icon_name == "database.svg":
                icon_name = "code.svg"
            item.setIcon(type_icon(icon_name))
            func_items.append(item)
            
            # Also append to mixed model
            item_copy = QStandardItem(display_name)
            item_copy.setData(insert_val, Qt.UserRole)
            item_copy.setData(2, Qt.UserRole + 1)
            item_copy.setIcon(type_icon(icon_name))
            self._mixed_model.appendRow(item_copy)

        for item in sorted(func_items, key=lambda i: i.text()):
            self._func_model.appendRow(item)

        # Add data variables to mixed model
        var_items = []
        for obj in self._context_state.get("data", []):
            item = QStandardItem(obj.name)
            item.setData(obj.name, Qt.UserRole)
            item.setData(1, Qt.UserRole + 1) # Priority 1 for data
            icon_name = get_icon_name_for_type(obj.type)
            item.setIcon(type_icon(icon_name))
            var_items.append(item)
            
        # Add constants
        for const_val in ["true", "false"]:
            item = QStandardItem(const_val)
            item.setData(const_val, Qt.UserRole)
            item.setData(1, Qt.UserRole + 1)
            item.setIcon(type_icon("check.svg"))
            var_items.append(item)

        for item in sorted(var_items, key=lambda i: i.text()):
            self._mixed_model.appendRow(item)

        # Apply to live widgets
        if hasattr(self, "_source_card") and hasattr(self._source_card, "set_completer_model"):
            self._source_card.set_completer_model(self._mixed_model)
        
        if hasattr(self, "_step_cards"):
            for card in self._step_cards:
                if hasattr(card, "set_models"):
                    card.set_models(self._func_model, self._mixed_model)

    # ---- Internal: Loading ----

    def _load_from_project(self):
        """Read the variable's code from KStateManager and populate the editor."""
        sm = self.project.kproject.state_manager
        if self.variable_name not in sm.variables:
            return

        code = sm.variables[self.variable_name].code
        target, source, step_strs = decompose_variable_code(code)
        self._source_text = source
        self._source_card.value = source

        # Build PipelineStep objects
        self._steps.clear()
        for s in step_strs:
            func_name, arg_strs = parse_step_string(s)
            # Look up parameter names from the function definition
            param_names, param_defaults = self._lookup_func_params(func_name)

            # Match arg_strs to param_names (skip first = piped input)
            step = PipelineStep(
                func_name=func_name,
                param_names=param_names,
                param_values=self._match_args(arg_strs, param_names, param_defaults),
                param_defaults=[param_defaults.get(n) for n in param_names],
            )
            self._steps.append(step)

        # Ensure trailing empty step
        if not self._steps or self._steps[-1].func_name:
            self._steps.append(PipelineStep())

        self._rebuild_step_cards()

    def _lookup_func_params(self, func_name: str) -> Tuple[List[str], dict]:
        """Look up a function's parameter names (minus the first piped arg) and defaults.

        Returns (param_names_without_first, {name: default_str}).
        """
        from kira.knodes.knode import KNode

        obj = self.project.kproject.context.get_object(func_name)
        if not isinstance(obj, KNode):
            return [], {}

        # Skip first input (the piped argument)
        all_names = obj.input_names
        param_names = all_names[1:] if len(all_names) > 1 else []

        # Default values
        defaults = {}
        for k, v in obj.default_inputs.items():
            if k in param_names:
                defaults[k] = str(v.value) if hasattr(v, "value") else str(v)

        return param_names, defaults

    @staticmethod
    def _match_args(
        arg_strs: List[str],
        param_names: List[str],
        param_defaults: dict
    ) -> List[str]:
        """Align provided argument strings to parameter names."""
        values: List[str] = []
        for i, name in enumerate(param_names):
            if i < len(arg_strs):
                values.append(arg_strs[i])
            elif name in param_defaults:
                values.append("")  # leave blank to use default
            else:
                values.append("")
        return values

    # ---- Internal: Rebuilding UI ----

    def _rebuild_step_cards(self):
        """Clear and rebuild all StepCard widgets from self._steps."""
        # Clear existing cards
        self._step_cards.clear()
        while self._steps_layout.count():
            item = self._steps_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for i, step in enumerate(self._steps):
            # Arrow connector
            arrow = _PipelineArrow()
            self._steps_layout.addWidget(arrow)

            card = StepCard(step, step_index=i)
            card.step_changed.connect(self._on_commit)
            card.step_deleted.connect(lambda idx=i: self._on_delete_step(idx))
            card.func_name_changed.connect(lambda name, focus, idx=i: self._on_func_name_set(idx, name, focus))
            card.set_models(self._func_model, self._mixed_model)
            self._step_cards.append(card)
            self._steps_layout.addWidget(card)

    # ---- Internal: User Actions ----


    def _on_delete_step(self, index: int):
        """Remove step at index and commit."""
        if 0 <= index < len(self._steps):
            self._steps.pop(index)
            # Ensure we still have an empty step if we just deleted the only one
            if not self._steps or self._steps[-1].func_name:
                self._steps.append(PipelineStep())
            self._rebuild_step_cards()
            self._on_commit()

    def _on_func_name_set(self, index: int, func_name: str, should_focus_params: bool = False):
        """User entered a function name for a blank step — populate params."""
        if 0 <= index < len(self._steps):
            param_names, param_defaults = self._lookup_func_params(func_name)
            self._steps[index] = PipelineStep(
                func_name=func_name,
                param_names=param_names,
                param_values=[""] * len(param_names),
                param_defaults=[param_defaults.get(n) for n in param_names],
            )
            # Add new trailing empty step if we just filled the last one
            if index == len(self._steps) - 1:
                self._steps.append(PipelineStep())

            self._rebuild_step_cards()
            
            # Focus transition: if requested (via Enter press)
            # we focus the first param of the rebuilt card.
            if should_focus_params and 0 <= index < len(self._step_cards):
                # Use singleShot to wait for layout/widget creation
                QTimer.singleShot(0, self._step_cards[index].focus_first_param)

    # ---- Internal: Drag and Drop ----

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-kira-step-index"):
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat("application/x-kira-step-index"):
            data = event.mimeData().data("application/x-kira-step-index")
            source_idx = int(data.data().decode())
            pos = event.position().toPoint()
            # Calculate where to show the indicator
            self._update_reorder_indicator(pos, source_idx)
            event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self._reorder_indicator.hide()

    def dropEvent(self, event):
        if event.mimeData().hasFormat("application/x-kira-step-index"):
            data = event.mimeData().data("application/x-kira-step-index")
            source_idx = int(data.data().decode())
            
            # Find target index from drop position
            pos = event.position().toPoint()
            target_idx = self._calculate_drop_index(pos)
            
            # Perform move if it's a real change
            # (Note: dropping a step at its current position or 
            #  one position after shouldn't trigger a move)
            if source_idx != target_idx and source_idx != target_idx - 1:
                self._move_step(source_idx, target_idx)
            
            self._reorder_indicator.hide()
            event.acceptProposedAction()

    def _update_reorder_indicator(self, pos, source_idx: int):
        """Place the indicator line between cards based on Y position."""
        target_idx = self._calculate_drop_index(pos)
        
        # Hide indicator if dropping here results in no move (no-op zone)
        if target_idx == source_idx or target_idx == source_idx + 1:
            self._reorder_indicator.hide()
            return

        self._reorder_indicator.show()
        
        from PySide6.QtCore import QPoint

        if target_idx < len(self._step_cards):
            card = self._step_cards[target_idx]
            # card's top in panel coordinates
            y = card.mapTo(self, QPoint(0, 0)).y()
        else:
            # Drop after the last step card
            if self._step_cards:
                last_card = self._step_cards[-1]
                y = last_card.mapTo(self, QPoint(0, 0)).y() + last_card.height()
            else:
                y = self._steps_widget.mapTo(self, QPoint(0, 0)).y()

        self._reorder_indicator.move(12, y - 1)
        self._reorder_indicator.setFixedWidth(self.width() - 24)
        self._reorder_indicator.raise_()

    def _calculate_drop_index(self, pos):
        """Find the insertion index based on current mouse position."""
        # Map pos to _steps_widget coordinates
        local_pos = self._steps_widget.mapFrom(self, pos)
        y = local_pos.y()
        
        # Iterate through cards and find the closest gap
        for i, card in enumerate(self._step_cards):
            geom = card.geometry()
            # If we are above the center of this card, we want index i
            if y < geom.center().y():
                return i
        
        # Otherwise, we are after the last card
        # Cap at len - 1 to ensure we never drop after the blank step
        return max(0, len(self._step_cards) - 1)

    def _move_step(self, source_idx, target_idx):
        """Move step from source_idx and insert before target_idx."""
        if source_idx < target_idx:
            target_idx -= 1
            
        step = self._steps.pop(source_idx)
        self._steps.insert(target_idx, step)
        
        # Clean up trailing empty steps (might have duplicates or misplaced one)
        # Ensure only one blank at the end
        self._steps = [s for s in self._steps if s.func_name]
        self._steps.append(PipelineStep())
        
        self._rebuild_step_cards()
        self._on_commit()

    # ---- Internal: Commit ----

    def _on_commit(self):
        """Recompose code from the editor state, validate, and fire event."""
        if self._committing:
            return
        self._committing = True

        try:
            source = self._source_card.value
            if not source:
                return

            # Gather steps
            steps_data: List[Tuple[str, List[str]]] = []
            for step in self._steps:
                if not step.func_name:
                    continue  # skip blank steps
                # Collect non-empty args
                args = []
                for val in step.param_values:
                    args.append(val if val else "")
                # Strip trailing empty args
                while args and not args[-1]:
                    args.pop()
                steps_data.append((step.func_name, args))

            code = compose_variable_code(self.variable_name, source, steps_data)

            # Validate: try to parse
            from kira.klanguage.ktokenizer import ktokenize, KTokenType
            from kira.klanguage.kast import kparse

            tokens = ktokenize(code)
            clean = [t for t in tokens if t.token_type != KTokenType.WHITESPACE]
            try:
                ast = kparse(clean)
            except SyntaxError as e:
                logger.warning(f"Parse error — not committing: {e} - code: {code}")
                return

            # Fire event
            from kproject.kevent import KEventTypes
            self.project.process_event(KEventTypes.AddVariable, self.variable_name, code)
            logger.info(f"Committed: {code}")

        finally:
            self._committing = False
