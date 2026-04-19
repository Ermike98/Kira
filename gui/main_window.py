import sys
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QTabWidget, QSplitter, QApplication,
    QMenuBar, QMenu
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction

from gui.qt_project import QTProject
from gui.components.sidebar import Sidebar
from gui.components.data_view import DataView
from gui.components.workflow_editor import WorkflowEditor
from gui.components.activity_bar import ActivityBar
from gui.components.bottom_panel import BottomPanel
from kproject.kevent import KEventTypes
from gui.style import LIGHT_THEME


class MainWindow(QMainWindow):
    """
    Main application window using the native OS title bar/frame.
    All window management (snap, resize, minimize, maximize, close)
    is handled by the OS — no custom title bar needed.
    """

    def __init__(self, project: QTProject):
        super().__init__()
        self.project = project
        self.setWindowTitle(f"Kira – {self.project.user_info.username}'s Workspace")
        self.resize(1280, 800)
        self.setMinimumSize(640, 400)

        self._setup_menu()
        self._setup_ui()
        self._apply_theme()
        self._connect_signals()
    
    def _apply_theme(self):
        from gui.utils.svg_utils import recolor_svg, get_svg_path
        
        # Neutral: Slate-400 stroke, no bg
        neutral_svg = recolor_svg("x.svg", stroke_color="#94a3b8")
        # Hover: White stroke (bg is handled by QSS)
        hover_svg = recolor_svg("x.svg", stroke_color="#ffffff")
        # Click: White stroke
        click_svg = recolor_svg("x.svg", stroke_color="#ffffff")
        
        theme = LIGHT_THEME.replace("PLACEHOLDER_CLOSE_NEUTRAL", get_svg_path(neutral_svg).replace("\\", "/"))
        theme = theme.replace("PLACEHOLDER_CLOSE_HOVER", get_svg_path(hover_svg).replace("\\", "/"))
        theme = theme.replace("PLACEHOLDER_CLOSE_CLICK", get_svg_path(click_svg).replace("\\", "/"))
        
        self.setStyleSheet(theme)

    # ------------------------------------------------------------------
    # Native menu bar (appears just below the OS title bar on Windows)
    # ------------------------------------------------------------------

    def _setup_menu(self):
        menu_bar = self.menuBar()

        # ---- File ----
        file_menu = menu_bar.addMenu("&File")
        file_menu.addSeparator()
        quit_action = QAction("&Quit", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # ---- Edit ----
        edit_menu = menu_bar.addMenu("&Edit")

        self.undo_action = QAction("&Undo", self)
        self.undo_action.setShortcut("Ctrl+Z")
        self.undo_action.triggered.connect(self.project.undo)
        edit_menu.addAction(self.undo_action)

        self.redo_action = QAction("&Redo", self)
        self.redo_action.setShortcut("Ctrl+Y")
        self.redo_action.triggered.connect(self.project.redo)
        edit_menu.addAction(self.redo_action)

        # ---- Help ----
        _help_menu = menu_bar.addMenu("&Help")  # placeholder for future items

    # ------------------------------------------------------------------
    # UI layout
    # ------------------------------------------------------------------

    def _setup_ui(self):
        root = QWidget()
        root.setObjectName("RootWidget")
        self.setCentralWidget(root)

        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Activity bar on the far left
        self.activity_bar = ActivityBar(self)
        root_layout.addWidget(self.activity_bar)

        # Main splitter: sidebar | content
        self.main_splitter = QSplitter(Qt.Horizontal)
        root_layout.addWidget(self.main_splitter)

        self.sidebar = Sidebar(self.project)
        self.main_splitter.addWidget(self.sidebar)

        # Content area: editor tabs + bottom panel
        self.content_container = QSplitter(Qt.Vertical)
        self.main_splitter.addWidget(self.content_container)

        self.content_tabs = QTabWidget()
        self.content_tabs.setTabsClosable(True)
        self.content_tabs.setMovable(True)
        self.content_tabs.setIconSize(QSize(16, 16))
        self.content_tabs.tabCloseRequested.connect(self._close_tab)
        self.content_container.addWidget(self.content_tabs)

        self.bottom_panel = BottomPanel()
        self.content_container.addWidget(self.bottom_panel)

        self.main_splitter.setStretchFactor(1, 1)
        self.content_container.setStretchFactor(0, 3)
        self.content_container.setStretchFactor(1, 1)

    def _connect_signals(self):
        self.activity_bar.view_changed.connect(self._on_view_changed)
        self.sidebar.element_selected.connect(self._open_element)
        self.sidebar.add_requested.connect(self._on_add_requested)
        self.project.error_occurred.connect(self.bottom_panel.log_error)
        self.project.status_changed.connect(self._update_tab_icons)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_view_changed(self, view_id: str):
        if self.sidebar.current_view == view_id:
            self.sidebar.setVisible(not self.sidebar.isVisible())
        else:
            self.sidebar.setVisible(True)
            self.sidebar.set_view(view_id)

    def _on_add_requested(self, item_type: str):
        if item_type in ("Variable", "Workflow"):
            view_id = "Data" if item_type == "Variable" else "Workflows"
            if self.sidebar.current_view != view_id:
                self.sidebar.set_view(view_id)
            if not self.sidebar.isVisible():
                self.sidebar.setVisible(True)
            self.sidebar.show_inline_input(item_type)

    def _open_element(self, type: str, name: str):
        from gui.components.sidebar import get_icon_name_for_type, type_icon
        from kira.kdata.kdata import KData as _KData

        for i in range(self.content_tabs.count()):
            if self.content_tabs.tabText(i) == name:
                self.content_tabs.setCurrentIndex(i)
                return

        if type == "Workflow":
            sm = self.project.kproject.state_manager
            if name in sm.workflows:
                code = sm.workflows[name].code
                editor = WorkflowEditor(self.project)
                editor.set_workflow(name, code)
                self.content_tabs.addTab(editor, type_icon("code.svg"), name)
                self.content_tabs.setCurrentWidget(editor)
        elif type == "Variable" or type == "Data":
            view = DataView(self.project, name)
            kdata = self.project.get_value(name)
            
            icon_name = "database.svg"
            if isinstance(kdata, _KData) and kdata.value is not None:
                view.set_kdata(name, kdata)
                icon_name = get_icon_name_for_type(kdata.type)
            
            if type == "Variable":
                # Split view: DataView (left) | StepEditorPanel (right)
                from gui.components.step_editor import StepEditorPanel
                splitter = QSplitter(Qt.Horizontal)
                splitter.addWidget(view)
                step_editor = StepEditorPanel(self.project, name)
                splitter.addWidget(step_editor)
                splitter.setStretchFactor(0, 3)  # DataView gets more space
                splitter.setStretchFactor(1, 2)
                self.content_tabs.addTab(splitter, type_icon(icon_name), name)
                self.content_tabs.setCurrentWidget(splitter)
            else:
                self.content_tabs.addTab(view, type_icon(icon_name), name)
                self.content_tabs.setCurrentWidget(view)

    def _close_tab(self, index: int):
        widget = self.content_tabs.widget(index)
        self.content_tabs.removeTab(index)
        widget.deleteLater()

    def _update_tab_icons(self, statuses: dict):
        """Reactively updates icons for open tabs based on their evaluation status/type."""
        from gui.components.sidebar import get_icon_name_for_type, type_icon
        from kira.kdata.kdata import KData as _KData

        for i in range(self.content_tabs.count()):
            name = self.content_tabs.tabText(i)
            if name in statuses:
                status = statuses[name]
                # We only try to update the icon if the variable is READY
                if str(status.value) == "READY":
                    kdata = self.project.get_value(name)
                    if isinstance(kdata, _KData) and kdata.value is not None:
                        icon_name = get_icon_name_for_type(kdata.type)
                        # Only update if it's a real specialized icon
                        if icon_name != "database.svg":
                            self.content_tabs.setTabIcon(i, type_icon(icon_name))
                elif str(status.value) == "ERROR":
                    self.content_tabs.setTabIcon(i, type_icon("alert-triangle.svg"))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run_gui(project_or_kproject):
    from gui.qt_project import QTProject
    from kproject.kproject import KProject
    
    app = QApplication.instance() or QApplication(sys.argv)
    
    if isinstance(project_or_kproject, KProject):
        project = QTProject(project_or_kproject)
    else:
        project = project_or_kproject
        
    window = MainWindow(project)
    window.show()
    return app, window
