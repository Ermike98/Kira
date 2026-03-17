from typing import Dict, Any, List, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QHBoxLayout, QFrame
)
from PySide6.QtCore import Qt, Signal, QSize, QTimer
from PySide6.QtGui import QIcon

from gui.qt_project import QTProject
from gui.utils.svg_utils import icon_from_svg, recolor_svg
from gui import style_system
from gui.utils import colors

from kira.core.kobject import KTypeInfo
from kira.kdata.ktable import KTableTypeInfo
from kira.kdata.karray import KArrayTypeInfo
from kira.kdata.kliteral import KLiteralTypeInfo, KLiteralType
from kira.kdata.kcollection import KCollectionTypeInfo

def get_icon_name_for_type(type_info: KTypeInfo) -> str:
    """Maps Kira TypeInfo to a Feather icon name."""
    if isinstance(type_info, KTableTypeInfo):
        return "table.svg"
    if isinstance(type_info, KArrayTypeInfo):
        return "array.svg"
    if isinstance(type_info, KCollectionTypeInfo):
        return "box.svg"
    if isinstance(type_info, KLiteralTypeInfo):
        match type_info._lit_type:
            case KLiteralType.INTEGER | KLiteralType.NUMBER:
                return "hash.svg"
            case KLiteralType.DATE | KLiteralType.DATETIME:
                return "calendar.svg"
            case KLiteralType.BOOLEAN:
                return "check.svg"
            case KLiteralType.STRING:
                return "type.svg"
            case _:
                return "database.svg"
    return "database.svg"

def type_icon(icon_name: str) -> QIcon:
    """Generates a small slate coloured icon for the sidebar."""
    svg = recolor_svg(icon_name, stroke_color=colors.slate_500)
    return icon_from_svg(svg)


class SidebarItemWidget(QWidget):
    """
    Custom widget for a single sidebar row with a type icon and status dot.
    """
    def __init__(self, name: str, item_type: str, type_info: KTypeInfo = None, parent=None):
        super().__init__(parent)
        self._name = name
        self._item_type = item_type
        # If we have TypeInfo AND it matches a real type (not just generic), we have a real icon
        icon_name = get_icon_name_for_type(type_info) if type_info else "database.svg"
        self._has_real_icon = (type_info is not None) and (icon_name != "database.svg")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(
            style_system.spacing_large_i, 
            style_system.spacing_xsmall_i, 
            style_system.spacing_large_i, 
            style_system.spacing_xsmall_i
        )
        layout.setSpacing(style_system.spacing_small_i)

        # Status Dot
        self.status_dot = QFrame()
        self.status_dot.setFixedSize(7, 7)
        self.status_dot.setObjectName("StatusDot")
        
        if item_type == "Data":
            self.status_dot.setProperty("status", "HIDDEN")
        else:
            self.status_dot.setProperty("status", "WAITING")
            
        layout.addWidget(self.status_dot)

        # Type Icon
        self.icon_lbl = QLabel()
        self.icon_lbl.setFixedSize(14, 14)
        self.icon_lbl.setPixmap(type_icon(icon_name).pixmap(14, 14))
        layout.addWidget(self.icon_lbl)

        self.name_label = QLabel(name)
        self.name_label.setObjectName("SidebarItemLabel")
        layout.addWidget(self.name_label)
        layout.addStretch()

        self.setAttribute(Qt.WA_Hover)

    def set_status(self, status: str):
        """Updates the status dot color."""
        if self._item_type != "Data":
            self.status_dot.setProperty("status", status)
            self.status_dot.style().unpolish(self.status_dot)
            self.status_dot.style().polish(self.status_dot)

    def refresh_type_icon(self, project: QTProject):
        """Fetches the latest value from the project and updates the icon if possible."""
        kdata = project.get_value(self._name)
        from kira.kdata.kdata import KData as _KData
        if isinstance(kdata, _KData) and kdata.value is not None:
            type_info = kdata.type
            icon_name = get_icon_name_for_type(type_info)
            if icon_name != "database.svg":
                self.icon_lbl.setPixmap(type_icon(icon_name).pixmap(14, 14))
                self._has_real_icon = True

    @property
    def has_real_icon(self) -> bool:
        return self._has_real_icon


class _SectionHeader(QWidget):
    """Subtle sub-section separator: thin rule + title."""
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(
            style_system.spacing_large_i, 
            style_system.spacing_small_i, 
            style_system.spacing_large_i, 
            style_system.spacing_xsmall_i
        )
        layout.setSpacing(style_system.spacing_small_i)

        label = QLabel(title)
        label.setObjectName("SidebarSectionTitle")
        layout.addWidget(label)

        rule = QFrame()
        rule.setFrameShape(QFrame.HLine)
        rule.setObjectName("SidebarSectionRule")
        layout.addWidget(rule)


class Sidebar(QWidget):
    """
    Reactive sidebar partitioned by ActivityBar views.
    Layout: [vertical border | content]
    """
    element_selected = Signal(str, str)  # (type, name)

    def __init__(self, project: QTProject, parent=None):
        super().__init__(parent)
        self.project = project
        self.setObjectName("Sidebar")
        self.setFixedWidth(250)
        self.current_view = "Data"

        self._item_widgets: Dict[str, SidebarItemWidget] = {}
        self._last_version = ""

        self._setup_ui()
        self._connect_signals()
        
        # Adaptive polling timer
        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._check_version)
        self._poll_timer.start(1000) # Start with 1s

        self.refresh()

    def _setup_ui(self):
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._border = QFrame()
        self._border.setObjectName("SidebarBorder")
        self._border.setFixedWidth(1)
        outer.addWidget(self._border)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        outer.addWidget(content)

        self.header = QLabel("Data Explorer")
        self.header.setObjectName("SidebarHeader")
        content_layout.addWidget(self.header)

        self.list_widget = QListWidget()
        self.list_widget.setFrameShape(QFrame.NoFrame)
        self.list_widget.setSpacing(0)
        self.list_widget.itemSelectionChanged.connect(self._on_selection_changed)
        content_layout.addWidget(self.list_widget)

    def _connect_signals(self):
        # We still connect signals for immediate reactivity
        self.project.history_updated.connect(self.refresh)
        self.project.status_changed.connect(self._update_statuses)

    def set_view(self, view_id: str):
        self.current_view = view_id
        if self.current_view == "Data":
             self.header.setText("Data Explorer")
        else:
             self.header.setText(view_id)
        self.refresh()

    def refresh(self):
        self.list_widget.clear()
        self._item_widgets.clear()
        self._last_version = self.project.state_version

        sm = self.project.kproject.state_manager

        if self.current_view == "Data":
            self._populate_section("VARIABLES", sorted(sm.variables.keys()), "Variable")
            self._populate_section("STATIC DATA", self.project.kproject.get_data_names(), "Data")
        elif self.current_view == "Workflows":
            self._populate_section("USER WORKFLOWS", sorted(sm.workflows.keys()), "Workflow")

        self._update_statuses(self.project.kproject.get_all_statuses())

    def _populate_section(self, title: str, names: List[str], item_type: str):
        if not names:
            return

        header_item = QListWidgetItem()
        header_item.setFlags(Qt.NoItemFlags)
        header_item.setSizeHint(QSize(0, 30))
        self.list_widget.addItem(header_item)
        self.list_widget.setItemWidget(header_item, _SectionHeader(title))

        for name in names:
            item = QListWidgetItem()
            item.setSizeHint(QSize(0, 32))
            item.setData(Qt.UserRole,     item_type)
            item.setData(Qt.UserRole + 1, name)

            kdata = self.project.get_value(name)
            from kira.kdata.kdata import KData as _KData
            
            # Icons should only be set if the status is ready (for variables)
            # or if it's static data
            is_ready = False
            if item_type == "Data":
                is_ready = True
            else:
                status = self.project.kproject.get_status(name)
                if status and str(status.value) == "READY":
                    is_ready = True

            type_info = kdata.type if (is_ready and isinstance(kdata, _KData) and kdata.value is not None) else None

            widget = SidebarItemWidget(name, item_type, type_info)
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, widget)
            self._item_widgets[name] = widget

    def _check_version(self):
        """Periodic check for state version and status-based adaptive polling."""
        current_version = self.project.state_version
        
        # 1. Version check
        if current_version != self._last_version:
            self.refresh()
            return # refresh() updates _last_version

        # 2. Adaptive polling & status refresh
        statuses = self.project.kproject.get_all_statuses()
        is_processing = any(str(s.value) in ("PROCESSING", "WAITING") for s in statuses.values())
        
        # Update timer interval
        new_interval = 100 if is_processing else 1000
        if self._poll_timer.interval() != new_interval:
            self._poll_timer.setInterval(new_interval)

        # Refresh icons for uncomputed variables that are now READY
        self._update_statuses(statuses)

    def _update_statuses(self, statuses: Dict[str, Any]):
        for name, status_enum in statuses.items():
            if name in self._item_widgets:
                widget = self._item_widgets[name]
                status_str = str(status_enum.value)
                widget.set_status(status_str)
                
                if not widget.has_real_icon and status_str in ("READY", "ERROR"):
                    widget.refresh_type_icon(self.project)

    def _on_selection_changed(self):
        items = self.list_widget.selectedItems()
        if not items:
            return
        item = items[0]
        item_type = item.data(Qt.UserRole)
        name = item.data(Qt.UserRole + 1)
        if item_type and name:
            self.element_selected.emit(item_type, name)
