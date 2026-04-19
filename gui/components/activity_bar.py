import os  # noqa: F401 — kept for potential path operations
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QButtonGroup
from PySide6.QtCore import Qt, Signal, QSize

from gui.utils.svg_utils import activity_icon


class ActivityBar(QWidget):
    """
    Vertical bar on the far left of the application.
    Contains icons to toggle different sidebar panels.

    Icon colours:
      • Normal  → dark stroke (zinc_800) on transparent background
      • Active  → light stroke (zinc_50) on dark rounded background (zinc_700)
    """
    view_changed = Signal(str)  # Emits the view id of the selected button

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ActivityBar")
        self.setFixedWidth(48)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.setAlignment(Qt.AlignTop)

        self.group = QButtonGroup(self)
        self.group.setExclusive(True)

        self._setup_buttons()
        self.layout.addStretch()
        self._setup_bottom_buttons()

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _setup_buttons(self):
        self.data_btn = self._create_button("Data", "database.svg", "Data")
        self.layout.addWidget(self.data_btn)

        self.workflow_btn = self._create_button("Workflows", "terminal.svg", "Workflows")
        self.layout.addWidget(self.workflow_btn)

        # Default active button
        self._set_active(self.data_btn)

    def _setup_bottom_buttons(self):
        self.settings_btn = self._create_button("Settings", "settings.svg", "Settings")
        self.layout.addWidget(self.settings_btn)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _create_button(self, name: str, icon_name: str, view_id: str) -> QPushButton:
        btn = QPushButton()
        btn.setCheckable(True)
        btn.setFixedSize(48, 48)
        btn.setToolTip(name)
        btn.setProperty("view_id", view_id)
        btn.setProperty("icon_name", icon_name)   # store for re-render on toggle
        btn.setCursor(Qt.PointingHandCursor)

        # Apply normal-state icon
        btn.setIcon(activity_icon(icon_name, active=False))
        btn.setIconSize(QSize(32, 32))

        btn.clicked.connect(self._on_button_clicked)
        btn.setProperty("class", "ActivityButton")
        self.group.addButton(btn)
        return btn

    def _set_active(self, active_btn: QPushButton):
        """Update icons, checked state, and QSS property for all buttons."""
        for btn in self.group.buttons():
            is_active = (btn is active_btn)
            icon_name = btn.property("icon_name")
            btn.setChecked(is_active)
            btn.setProperty("active", is_active)
            btn.setIcon(activity_icon(icon_name, active=is_active))
            # Force Qt to re-evaluate QSS selectors for this widget
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_button_clicked(self):
        btn = self.sender()
        if btn.isChecked():
            self._set_active(btn)
            self.view_changed.emit(btn.property("view_id"))
