import os
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton,
    QMenuBar, QMenu, QSizePolicy
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QFont


class TitleBar(QWidget):
    """
    Custom title bar integrated with the OS title bar area.
    Contains: [App Icon] [Menu Bar] --- [Title] --- [Min][Max][Close]
    
    The parent window handles WM_NCHITTEST so drag, resize, and
    Windows Snap all work normally through native OS handling.
    """

    def __init__(self, parent_window):
        super().__init__(parent_window)
        self.parent_window = parent_window
        self.setObjectName("TitleBar")
        self.setFixedHeight(32)

        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self._setup_left_area()
        self._setup_center_area()
        self._setup_right_area()

        self.main_layout.addWidget(self.left_container)
        self.main_layout.addStretch(1)
        self.main_layout.addWidget(self.title_label)
        self.main_layout.addStretch(1)
        self.main_layout.addWidget(self.right_container)

        self.left_container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.right_container.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)

    # ------------------------------------------------------------------
    # Area builders
    # ------------------------------------------------------------------

    def _setup_left_area(self):
        self.left_container = QWidget()
        self.left_container.setObjectName("TitleLeftArea")
        self.left_layout = QHBoxLayout(self.left_container)
        self.left_layout.setContentsMargins(8, 0, 0, 0)
        self.left_layout.setSpacing(4)

        # App icon
        self.app_icon = QLabel()
        self.app_icon.setObjectName("AppIcon")
        self.app_icon.setFixedSize(20, 20)
        icon_path = os.path.join(os.path.dirname(__file__), "..", "icons", "package.svg")
        if os.path.exists(icon_path):
            self.app_icon.setPixmap(QIcon(icon_path).pixmap(16, 16))
        self.left_layout.addWidget(self.app_icon)

        # Menu bar lives inside the title bar
        self.menu_bar = QMenuBar()
        self.menu_bar.setObjectName("TitleMenuBar")
        self.menu_bar.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        # Pass mouse events through so hits in empty areas remain HTCAPTION
        self.left_layout.addWidget(self.menu_bar)

        self.edit_menu = QMenu("Edit", self)
        self.menu_bar.addMenu(self.edit_menu)

    def _setup_center_area(self):
        self.title_label = QLabel(self.parent_window.windowTitle())
        self.title_label.setObjectName("TitleLabel")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        # Transparent to mouse so the OS still sees HTCAPTION here
        self.title_label.setAttribute(Qt.WA_TransparentForMouseEvents)

    def _setup_right_area(self):
        self.right_container = QWidget()
        self.right_container.setObjectName("TitleRightArea")
        self.right_layout = QHBoxLayout(self.right_container)
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        self.right_layout.setSpacing(0)

        # Use Unicode symbols – no dependency on SVG icon files
        self.min_btn = self._make_btn("&#xE921;", "TitleControlBtn", self.parent_window.showMinimized)
        self.max_btn = self._make_btn("&#xE922;", "TitleControlBtn", self._toggle_maximize)
        self.close_btn = self._make_btn("&#xE8BB;", "CloseTitleBtn", self.parent_window.close)

        # Tooltip text
        self.min_btn.setToolTip("Minimize")
        self.max_btn.setToolTip("Maximize / Restore")
        self.close_btn.setToolTip("Close")

        self.right_layout.addWidget(self.min_btn)
        self.right_layout.addWidget(self.max_btn)
        self.right_layout.addWidget(self.close_btn)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _make_btn(self, html_entity: str, obj_name: str, callback) -> QPushButton:
        """Create a window-control button using a Segoe MDL2 / Segoe Fluent icon."""
        btn = QPushButton()
        btn.setObjectName(obj_name)
        btn.setFixedSize(46, 32)
        btn.setCursor(Qt.ArrowCursor)

        # Segoe MDL2 Assets gives us the proper Windows glyphs on Windows 10/11.
        # Fall back to plain Unicode on other platforms.
        import sys
        if sys.platform == "win32":
            # Decode HTML entity to char
            import html
            glyph = html.unescape(html_entity)
            font = QFont("Segoe MDL2 Assets", 10)
            btn.setFont(font)
            btn.setText(glyph)
        else:
            # Fallback symbols
            fallbacks = {"&#xE921;": "─", "&#xE922;": "□", "&#xE8BB;": "✕"}
            btn.setText(fallbacks.get(html_entity, "?"))

        btn.clicked.connect(callback)
        return btn

    def _toggle_maximize(self):
        if self.parent_window.isMaximized():
            self.parent_window.showNormal()
            import html
            self.max_btn.setText(html.unescape("&#xE922;"))   # maximize icon
        else:
            self.parent_window.showMaximized()
            import html
            self.max_btn.setText(html.unescape("&#xE923;"))   # restore icon

    def update_max_btn_icon(self):
        """Call this whenever the window maximize state changes."""
        import html
        if self.parent_window.isMaximized():
            self.max_btn.setText(html.unescape("&#xE923;"))
        else:
            self.max_btn.setText(html.unescape("&#xE922;"))
