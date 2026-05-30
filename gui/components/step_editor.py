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
import os
import re
import logging
from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Callable, TYPE_CHECKING

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QFrame, QScrollArea, QPushButton,
    QListWidget, QListWidgetItem, QAbstractItemView,
    QSizePolicy, QCompleter, QListView
)
from PySide6.QtCore import Qt, Signal, QSize, QTimer, QSortFilterProxyModel, QModelIndex, QMimeData
from PySide6.QtGui import QFont, QStandardItemModel, QStandardItem, QDrag, QPixmap, QPainter, QIcon
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
#  2. Data Classes & Constants                                                #
# ---------------------------------------------------------------------------#

OPERATOR_NAMES = {
    "+", "-", "*", "/", "^", "==", "!=", ">", "<", ">=", "<=",
    "and", "or", "not", "unary_-", "unary_!",
    "identity",
}


@dataclass
class PipelineStep:
    """Single source of truth for a pipeline step."""
    raw_expression: str = ""


# ---------------------------------------------------------------------------#
#  3. Expression Card                                                         #
# ---------------------------------------------------------------------------#

class ExpressionCard(QFrame):
    """Unified card for any pipeline expression (source or piped step).

    Two modes: collapsed (raw text input) and expanded (func name + param rows).
    """

    expression_changed = Signal()
    step_deleted = Signal()

    def __init__(
        self,
        expression: str = "",
        is_source: bool = False,
        step_index: int = 0,
        resolve_fn: Optional[Callable] = None,
        parent=None
    ):
        super().__init__(parent)
        self.setObjectName("ExpressionCard")
        self._is_source = is_source
        self._step_index = step_index
        self._resolve_fn = resolve_fn or (lambda name: None)

        self._expanded = False
        self._expandable = False

        # Derived state (valid when expanded)
        self._func_name = ""
        self._param_names: List[str] = []
        self._param_values: List[str] = []
        self._param_defaults: List[Optional[str]] = []
        self._n_expected_params = 0

        self._param_inputs: List[QLineEdit] = []
        self._func_model: Optional[QStandardItemModel] = None
        self._mixed_model: Optional[QStandardItemModel] = None
        self._suppress_signals = False

        # ---- Build UI ----
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(12, 10, 12, 10)
        self._main_layout.setSpacing(6)

        header = QHBoxLayout()
        header.setSpacing(8)

        # Drag handle
        self._drag_handle = QLabel("≡")
        self._drag_handle.setObjectName("StepDragHandle")
        self._drag_handle.setCursor(Qt.OpenHandCursor)
        if not is_source:
            self._drag_handle.setFixedWidth(20)
        header.addWidget(self._drag_handle)
        if is_source:
            self._drag_handle.hide()

        # Collapsed input
        self._collapsed_input = QLineEdit(expression)
        self._collapsed_input.setObjectName("StepCollapsedInput")
        ph = "e.g. Sales_Table, load_csv(\"path\")" if is_source else "function name…"
        self._collapsed_input.setPlaceholderText(ph)
        self._collapsed_input.editingFinished.connect(self._on_collapsed_blur)
        self._collapsed_input.returnPressed.connect(self._on_collapsed_return)
        header.addWidget(self._collapsed_input)

        # Func name input (expanded mode)
        self._func_input = QLineEdit()
        self._func_input.setObjectName("StepFuncInput")
        self._func_input.setPlaceholderText("function name…")
        self._func_input.editingFinished.connect(self._on_func_name_blur)
        self._func_input.returnPressed.connect(self._on_func_name_return)
        self._func_input.hide()
        header.addWidget(self._func_input)

        # Chevron toggle
        self._expand_btn = QPushButton()
        self._expand_btn.setObjectName("StepExpandButton")
        self._expand_btn.setFixedSize(20, 20)
        self._expand_btn.setCursor(Qt.PointingHandCursor)
        self._expand_btn.clicked.connect(self._on_chevron_click)
        header.addWidget(self._expand_btn)

        # Delete / Reset button
        self._del_btn = QPushButton("×")
        self._del_btn.setObjectName("StepDeleteButton")
        self._del_btn.setFixedSize(24, 24)
        self._del_btn.setCursor(Qt.PointingHandCursor)
        self._del_btn.clicked.connect(self._on_delete)
        header.addWidget(self._del_btn)

        if not expression and not is_source:
            self._del_btn.hide()
            self._drag_handle.hide()

        self._main_layout.addLayout(header)

        # Params container
        self._params_container = QWidget()
        self._params_layout = QVBoxLayout(self._params_container)
        # Shift parameter labels rightward by drag handle width + layout spacing (if non-source)
        # and add an extra 5px to align with the text inset (padding + border) of the QLineEdit
        left_margin = 5 if is_source else (20 + 8 + 5)
        self._params_layout.setContentsMargins(left_margin, 4, 0, 0)
        self._params_layout.setSpacing(4)
        self._main_layout.addWidget(self._params_container)
        self._params_container.hide()

        # Initial state
        self._check_expandable()
        self._update_chevron_icon()

        if expression and self._expandable:
            self._set_expanded(True)

    # ---- Properties ----

    @property
    def expression(self) -> str:
        if self._expanded:
            return self._recompose_from_params()
        return self._collapsed_input.text().strip()

    @property
    def is_blank(self) -> bool:
        return not self._collapsed_input.text().strip() and not self._expanded

    @property
    def step_index(self) -> int:
        return self._step_index

    @step_index.setter
    def step_index(self, v: int):
        self._step_index = v

    # ---- Public API ----

    def set_expression(self, expr: str, auto_expand: bool = True):
        self._suppress_signals = True
        self._collapsed_input.setText(expr)
        self._check_expandable()
        self._update_chevron_icon()
        if auto_expand and expr and self._expandable:
            self._set_expanded(True)
        else:
            self._set_expanded(False)
        self._suppress_signals = False

    def set_models(self, func_model: QStandardItemModel, mixed_model: QStandardItemModel):
        self._func_model = func_model
        self._mixed_model = mixed_model
        if not self._collapsed_input.completer():
            attach_word_completer(self._collapsed_input, mixed_model)
        if not self._func_input.completer():
            attach_word_completer(self._func_input, func_model)
        for inp in self._param_inputs:
            if not inp.completer():
                attach_word_completer(inp, mixed_model)

    def focus_first_param(self):
        if self._param_inputs:
            self._param_inputs[0].setFocus()
            self._param_inputs[0].selectAll()
        elif self._expanded:
            self._func_input.setFocus()

    # ---- Internal: Expandability ----

    def _check_expandable(self):
        text = self._collapsed_input.text().strip()
        if not text:
            self._expandable = False
            return
        func_name, _ = parse_step_string(text)
        if not func_name or func_name in OPERATOR_NAMES:
            self._expandable = False
            return
        result = self._resolve_fn(func_name)
        self._expandable = result is not None

    # ---- Internal: Expand / Collapse ----

    def _set_expanded(self, expanded: bool):
        if expanded and not self._expandable:
            return
        self._expanded = expanded

        if expanded:
            text = self._collapsed_input.text().strip()
            func_name, arg_strs = parse_step_string(text)
            self._func_name = func_name

            result = self._resolve_fn(func_name)
            if result:
                all_names, defaults_dict = result
                # For piped steps hide the first param
                if not self._is_source and len(all_names) > 0:
                    display_names = all_names[1:]
                else:
                    display_names = list(all_names)

                self._param_names = list(display_names)
                self._n_expected_params = len(self._param_names)
                self._param_defaults = [defaults_dict.get(n) for n in self._param_names]

                self._param_values = []
                for i in range(len(self._param_names)):
                    if i < len(arg_strs):
                        self._param_values.append(arg_strs[i])
                    else:
                        self._param_values.append("")

                # Extra args beyond expected
                if len(arg_strs) > len(self._param_names):
                    for extra_val in arg_strs[len(self._param_names):]:
                        self._param_names.append("")
                        self._param_values.append(extra_val)
                        self._param_defaults.append(None)

            self._collapsed_input.hide()
            self._func_input.setText(func_name)
            self._func_input.show()
            self._build_param_inputs()
            self._params_container.show()
        else:
            if self._func_name:
                self._collapsed_input.setText(self._recompose_from_params())
            self._func_input.hide()
            self._collapsed_input.show()
            self._params_container.hide()

        self.setProperty("expanded", str(expanded).lower())
        self.style().unpolish(self)
        self.style().polish(self)
        self._update_chevron_icon()

    def _update_chevron_icon(self):
        icons_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "icons")
        if self._expanded:
            icon_path = os.path.join(icons_dir, "chevron-down.svg")
        else:
            icon_path = os.path.join(icons_dir, "chevron-right.svg")
        self._expand_btn.setIcon(QIcon(icon_path))

        can_interact = self._expandable or self._expanded
        self._expand_btn.setEnabled(can_interact)
        self._expand_btn.setProperty("expandable", "true" if can_interact else "false")
        self._expand_btn.style().unpolish(self._expand_btn)
        self._expand_btn.style().polish(self._expand_btn)

    def _on_chevron_click(self):
        if self._expanded:
            self._set_expanded(False)
            self._check_expandable()
            self._update_chevron_icon()
            self._emit_change()
        elif self._expandable:
            self._set_expanded(True)

    # ---- Internal: Build Params ----

    def _build_param_inputs(self):
        self._param_inputs.clear()
        while self._params_layout.count():
            item = self._params_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                sub = item.layout()
                while sub.count():
                    si = sub.takeAt(0)
                    if si.widget():
                        si.widget().deleteLater()

        # Calculate dynamic width for labels based on the longest param name
        max_label_width = 0
        fm = self.fontMetrics()
        for name in self._param_names:
            if name:
                w = fm.horizontalAdvance(name)
                if w > max_label_width:
                    max_label_width = w
        if max_label_width > 0:
            max_label_width += 12  # Add padding for visual breathing room

        for i, (name, value, default) in enumerate(zip(
            self._param_names, self._param_values, self._param_defaults
        )):
            is_extra = i >= self._n_expected_params
            row = QHBoxLayout()
            row.setSpacing(8)

            if name:
                lbl = QLabel(name)
                lbl.setObjectName("StepParamLabel")
                lbl.setFixedWidth(max_label_width)
                lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                row.addWidget(lbl)
            else:
                spacer = QWidget()
                spacer.setFixedWidth(max_label_width)
                row.addWidget(spacer)

            inp = QLineEdit(value)
            inp.setObjectName("StepParamInputExtra" if is_extra else "StepParamInput")
            if default is not None and not is_extra:
                inp.setPlaceholderText(f"default: {default}")
            inp.editingFinished.connect(lambda idx=i: self._on_param_blur(idx))
            inp.returnPressed.connect(lambda idx=i: self._on_param_return(idx))
            row.addWidget(inp)

            self._param_inputs.append(inp)
            self._params_layout.addLayout(row)

        if self._mixed_model:
            for inp in self._param_inputs:
                if not inp.completer():
                    attach_word_completer(inp, self._mixed_model)

    # ---- Internal: Event Handlers ----

    def _on_collapsed_return(self):
        text = self._collapsed_input.text().strip()
        if not text:
            return
        self._check_expandable()
        self._update_chevron_icon()
        if self._expandable:
            self._set_expanded(True)
            QTimer.singleShot(0, self.focus_first_param)
        else:
            self._emit_change()

    def _on_collapsed_blur(self):
        self._check_expandable()
        self._update_chevron_icon()
        self._emit_change()

    def _on_func_name_return(self):
        new_name = self._func_input.text().strip()
        if new_name and new_name != self._func_name:
            self._change_function(new_name)
        elif self._param_inputs:
            self._param_inputs[0].setFocus()
            self._param_inputs[0].selectAll()

    def _on_func_name_blur(self):
        new_name = self._func_input.text().strip()
        if new_name and new_name != self._func_name:
            self._change_function(new_name)

    def _change_function(self, new_name: str):
        _, old_args = parse_step_string(self._recompose_from_params())
        result = self._resolve_fn(new_name)

        if result and new_name not in OPERATOR_NAMES:
            self._func_name = new_name
            all_names, defaults_dict = result
            if not self._is_source and len(all_names) > 0:
                display_names = all_names[1:]
            else:
                display_names = list(all_names)

            self._param_names = list(display_names)
            self._n_expected_params = len(self._param_names)
            self._param_defaults = [defaults_dict.get(n) for n in self._param_names]

            self._param_values = []
            for i in range(len(self._param_names)):
                if i < len(old_args):
                    self._param_values.append(old_args[i])
                else:
                    self._param_values.append("")

            if len(old_args) > len(self._param_names):
                for extra_val in old_args[len(self._param_names):]:
                    self._param_names.append("")
                    self._param_values.append(extra_val)
                    self._param_defaults.append(None)

            self._func_input.setText(new_name)
            self._build_param_inputs()
            self._emit_change()
            QTimer.singleShot(0, self.focus_first_param)
        else:
            self._func_name = new_name
            recomposed = self._recompose_from_params()
            self._collapsed_input.setText(recomposed)
            self._func_name = ""
            self._set_expanded(False)
            self._check_expandable()
            self._update_chevron_icon()
            self._emit_change()

    def _on_param_blur(self, index: int):
        if index < len(self._param_inputs):
            value = self._param_inputs[index].text().strip()
            # Extra arg cleared -> remove it
            if index >= self._n_expected_params and not value:
                self._param_names.pop(index)
                self._param_values.pop(index)
                self._param_defaults.pop(index)
                self._build_param_inputs()
                self._emit_change()
            elif index < len(self._param_values):
                self._param_values[index] = value
                self._emit_change()

    def _on_param_return(self, index: int):
        if index < len(self._param_inputs) and index < len(self._param_values):
            self._param_values[index] = self._param_inputs[index].text().strip()
        if index < len(self._param_inputs) - 1:
            self._param_inputs[index + 1].setFocus()
            self._param_inputs[index + 1].selectAll()
        else:
            self._emit_change()

    def _on_delete(self):
        if self._is_source:
            self._collapsed_input.setText("")
            self._set_expanded(False)
            self._func_name = ""
            self._param_names.clear()
            self._param_values.clear()
            self._param_defaults.clear()
            self._check_expandable()
            self._update_chevron_icon()
            self._emit_change()
        else:
            self.step_deleted.emit()

    def _emit_change(self):
        if not self._suppress_signals:
            self.expression_changed.emit()

    # ---- Internal: Recomposition ----

    def _recompose_from_params(self) -> str:
        if not self._func_name:
            return ""
        args = []
        for i, val in enumerate(self._param_values):
            if val:
                args.append(val)
            elif i < self._n_expected_params:
                args.append("")
        while args and not args[-1]:
            args.pop()
        if args:
            return f"{self._func_name}({', '.join(args)})"
        return f"{self._func_name}()"

    # ---- Drag support ----

    def mousePressEvent(self, event):
        if (event.button() == Qt.LeftButton and
            not self._is_source and
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


# ---------------------------------------------------------------------------#
#  4. Pipeline Arrow (visual connector)                                       #
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
#  5. Step Editor Panel                                                     #
# ---------------------------------------------------------------------------#


class StepEditorPanel(QWidget):
    """Full pipeline editor panel.

    Shows a list of ExpressionCards with drag-and-drop reordering.
    Index 0 is the source, the rest are piped steps.
    """

    def __init__(self, project: QTProject, variable_name: str, parent=None):
        super().__init__(parent)
        self.project = project
        self.variable_name = variable_name
        self.setObjectName("StepEditorPanel")

        self._steps: List[PipelineStep] = []
        self._cards: List[ExpressionCard] = []
        self._committing = False
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

        # Steps container
        self._steps_widget = QWidget()
        self._steps_layout = QVBoxLayout(self._steps_widget)
        self._steps_layout.setContentsMargins(0, 0, 0, 0)
        self._steps_layout.setSpacing(0)
        self._steps_layout.setAlignment(Qt.AlignTop)
        self._content_layout.addWidget(self._steps_widget)

        self._content_layout.addStretch()

        # Reorder indicator
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

        QTimer.singleShot(200, lambda: self._on_status_changed(self.project.kproject.get_all_statuses()))

    # ---- Public API ----

    def refresh(self):
        self._load_from_project()

    def _on_status_changed(self, statuses: dict):
        status_obj = statuses.get(self.variable_name)
        if not status_obj:
            return
        status_str = status_obj.name
        if status_str == "READY":
            kdata = self.project.get_value(self.variable_name)
            if not bool(kdata):
                status_str = "ERROR"
        if status_str == self._status:
            return
        self._status = status_str
        self._header.setProperty("status", status_str)
        self._title.setProperty("status", status_str)
        self._header.style().unpolish(self._header)
        self._header.style().polish(self._header)
        self._title.style().unpolish(self._title)
        self._title.style().polish(self._title)

    def _refresh_autocomplete_cache(self):
        self._context_state = self.project.get_context_state()
        self._func_model.clear()
        self._mixed_model.clear()

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
            item.setData(obj.name, Qt.UserRole)
            item.setData(2, Qt.UserRole + 1)
            icon_name = get_icon_name_for_type(obj.type)
            if icon_name == "database.svg":
                icon_name = "code.svg"
            item.setIcon(type_icon(icon_name))
            func_items.append(item)

            item_copy = QStandardItem(display_name)
            item_copy.setData(insert_val, Qt.UserRole)
            item_copy.setData(2, Qt.UserRole + 1)
            item_copy.setIcon(type_icon(icon_name))
            self._mixed_model.appendRow(item_copy)

        for item in sorted(func_items, key=lambda i: i.text()):
            self._func_model.appendRow(item)

        var_items = []
        for obj in self._context_state.get("data", []):
            item = QStandardItem(obj.name)
            item.setData(obj.name, Qt.UserRole)
            item.setData(1, Qt.UserRole + 1)
            icon_name = get_icon_name_for_type(obj.type)
            item.setIcon(type_icon(icon_name))
            var_items.append(item)

        for const_val in ["true", "false"]:
            item = QStandardItem(const_val)
            item.setData(const_val, Qt.UserRole)
            item.setData(1, Qt.UserRole + 1)
            item.setIcon(type_icon("check.svg"))
            var_items.append(item)

        for item in sorted(var_items, key=lambda i: i.text()):
            self._mixed_model.appendRow(item)

        if hasattr(self, "_cards"):
            for card in self._cards:
                card.set_models(self._func_model, self._mixed_model)

    # ---- Internal: Loading ----

    def _load_from_project(self):
        sm = self.project.kproject.state_manager
        if self.variable_name not in sm.variables:
            return

        code = sm.variables[self.variable_name].code
        target, source, step_strs = decompose_variable_code(code)

        self._steps = [PipelineStep(raw_expression=source)]
        for s in step_strs:
            self._steps.append(PipelineStep(raw_expression=s))

        # Trailing empty step
        self._steps.append(PipelineStep())

        self._rebuild_cards()

    def _resolve_function(self, func_name: str) -> Optional[Tuple[List[str], dict]]:
        """Look up function params. Returns None if not expandable."""
        if not func_name or func_name in OPERATOR_NAMES:
            return None
        from kira.knodes.knode import KNode
        obj = self.project.kproject.context.get_object(func_name)
        if not isinstance(obj, KNode):
            return None
        param_names = list(obj.input_names)
        defaults = {}
        for k, v in obj.default_inputs.items():
            if k in param_names:
                defaults[k] = str(v.value) if hasattr(v, "value") else str(v)
        return param_names, defaults

    # ---- Internal: Rebuilding UI ----

    def _rebuild_cards(self):
        self._cards.clear()
        while self._steps_layout.count():
            item = self._steps_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for i, step in enumerate(self._steps):
            is_source = (i == 0)

            if i > 0:
                arrow = _PipelineArrow()
                self._steps_layout.addWidget(arrow)

            card = ExpressionCard(
                expression=step.raw_expression,
                is_source=is_source,
                step_index=i,
                resolve_fn=self._resolve_function,
            )
            card.expression_changed.connect(self._on_commit)
            card.step_deleted.connect(lambda idx=i: self._on_delete_step(idx))
            card.set_models(self._func_model, self._mixed_model)
            self._cards.append(card)
            self._steps_layout.addWidget(card)

    # ---- Internal: User Actions ----

    def _on_delete_step(self, index: int):
        if 0 <= index < len(self._steps):
            self._steps.pop(index)
            if not self._steps or self._steps[-1].raw_expression:
                self._steps.append(PipelineStep())
            self._rebuild_cards()
            self._on_commit()

    # ---- Internal: Drag and Drop ----

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-kira-step-index"):
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat("application/x-kira-step-index"):
            data = event.mimeData().data("application/x-kira-step-index")
            source_idx = int(data.data().decode())
            pos = event.position().toPoint()
            self._update_reorder_indicator(pos, source_idx)
            event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self._reorder_indicator.hide()

    def dropEvent(self, event):
        if event.mimeData().hasFormat("application/x-kira-step-index"):
            data = event.mimeData().data("application/x-kira-step-index")
            source_idx = int(data.data().decode())
            pos = event.position().toPoint()
            target_idx = self._calculate_drop_index(pos)
            if source_idx != target_idx and source_idx != target_idx - 1:
                self._move_step(source_idx, target_idx)
            self._reorder_indicator.hide()
            event.acceptProposedAction()

    def _update_reorder_indicator(self, pos, source_idx: int):
        target_idx = self._calculate_drop_index(pos)
        if target_idx == source_idx or target_idx == source_idx + 1:
            self._reorder_indicator.hide()
            return
        self._reorder_indicator.show()
        from PySide6.QtCore import QPoint
        if target_idx < len(self._cards):
            card = self._cards[target_idx]
            y = card.mapTo(self, QPoint(0, 0)).y()
        else:
            if self._cards:
                last_card = self._cards[-1]
                y = last_card.mapTo(self, QPoint(0, 0)).y() + last_card.height()
            else:
                y = self._steps_widget.mapTo(self, QPoint(0, 0)).y()
        self._reorder_indicator.move(12, y - 1)
        self._reorder_indicator.setFixedWidth(self.width() - 24)
        self._reorder_indicator.raise_()

    def _calculate_drop_index(self, pos):
        local_pos = self._steps_widget.mapFrom(self, pos)
        y = local_pos.y()
        # Skip source card (index 0) — not droppable before it
        for i, card in enumerate(self._cards):
            if i == 0:
                continue
            geom = card.geometry()
            if y < geom.center().y():
                return i
        return max(1, len(self._cards) - 1)

    def _move_step(self, source_idx, target_idx):
        # Don't move the source
        if source_idx == 0 or target_idx == 0:
            return
        if source_idx < target_idx:
            target_idx -= 1
        step = self._steps.pop(source_idx)
        self._steps.insert(target_idx, step)
        self._steps = [self._steps[0]] + [s for s in self._steps[1:] if s.raw_expression]
        self._steps.append(PipelineStep())
        self._rebuild_cards()
        self._on_commit()

    # ---- Internal: Commit ----

    def _on_commit(self):
        if self._committing:
            return
        self._committing = True

        try:
            # Sync steps from cards
            for i, card in enumerate(self._cards):
                if i < len(self._steps):
                    self._steps[i] = PipelineStep(raw_expression=card.expression)

            source_expr = self._steps[0].raw_expression if self._steps else ""
            if not source_expr:
                return

            # Build code directly
            code = f"{self.variable_name} = {source_expr}"
            for step in self._steps[1:]:
                expr = step.raw_expression
                if expr:
                    code += f" |> {expr}"

            # Validate
            from kira.klanguage.ktokenizer import ktokenize, KTokenType
            from kira.klanguage.kast import kparse

            tokens = ktokenize(code)
            clean = [t for t in tokens if t.token_type != KTokenType.WHITESPACE]
            try:
                ast = kparse(clean)
            except SyntaxError as e:
                logger.warning(f"Parse error — not committing: {e} - code: {code}")
                return

            from kproject.kevent import KEventTypes
            self.project.process_event(KEventTypes.AddVariable, self.variable_name, code)
            logger.info(f"Committed: {code}")

            # Ensure trailing empty card
            has_trailing = self._steps and not self._steps[-1].raw_expression
            if not has_trailing:
                self._steps.append(PipelineStep())
                self._rebuild_cards()

        finally:
            self._committing = False

