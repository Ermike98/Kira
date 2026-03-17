from gui.utils import colors
from gui import style_system

LIGHT_THEME = f"""
/* Base Colors and Typography */
* {{
    font-family: 'Segoe UI', 'Roboto', 'Helvetica Neue', sans-serif;
    font-size: {style_system.font_small};
    color: {colors.slate_800};
}}

QMainWindow {{
    background-color: {colors.slate_50};
}}

/* Native Menu Bar — light theme */
QMenuBar {{
    background-color: {colors.slate_50};
    color: {colors.slate_900};
    border-bottom: {style_system.border_thin} solid {colors.slate_200};
    padding: {style_system.spacing_xxsmall} {style_system.spacing_xsmall};
    font-size: {style_system.font_small};
}}

QMenuBar::item {{
    background-color: transparent;
    color: {colors.slate_900};
    padding: {style_system.spacing_xsmall} {style_system.spacing_small};
    border-radius: {style_system.radius_medium};
    margin: {style_system.spacing_xxsmall} {style_system.spacing_none};
}}

QMenuBar::item:selected,
QMenuBar::item:pressed {{
    background-color: {colors.slate_200};
    color: {colors.slate_900};
}}

QMenu {{
    background-color: white;
    color: {colors.slate_900};
    border: {style_system.border_thin} solid {colors.slate_200};
    border-radius: {style_system.radius_large};
    padding: {style_system.spacing_xsmall};
}}

QMenu::item {{
    padding: {style_system.spacing_small} {style_system.spacing_xlarge} {style_system.spacing_small} {style_system.spacing_large};
    border-radius: {style_system.radius_medium};
    color: {colors.slate_800};
}}

QMenu::item:selected {{
    background-color: {colors.slate_100};
    color: {colors.slate_900};
}}

QMenu::item:disabled {{
    color: {colors.slate_400};
}}

QMenu::separator {{
    height: {style_system.border_thin};
    background: {colors.slate_200};
    margin: {style_system.spacing_xsmall} {style_system.spacing_small};
}}

/* Activity Bar */
#ActivityBar {{
    background-color: {colors.slate_900};
    border-right: {style_system.border_thin} solid {colors.slate_800};
    min-width: 48px;
    max-width: 48px;
}}

.ActivityButton {{
    background-color: transparent;
    border: none;
    border-radius: {style_system.radius_none};
    padding: {style_system.spacing_none};
    margin: {style_system.spacing_none};
}}

.ActivityButton:hover {{
    background-color: {colors.slate_800};
}}

.ActivityButton[active="true"] {{
    background-color: {colors.slate_700};
}}

/* ---- Sidebar ---- */
#Sidebar {{
    background-color: {colors.slate_50};
}}

/* Thin accent line between activity bar and sidebar */
#SidebarBorder {{
    background-color: {colors.slate_200};
    border: none;
}}

/* Large view title at the top ("Data Explorer", "WORKFLOWS") */
#SidebarHeader {{
    font-size: {style_system.font_medium};
    font-weight: 700;
    letter-spacing: 0.5px;
    padding: {style_system.spacing_medium} {style_system.spacing_medium} {style_system.spacing_small} {style_system.spacing_medium};
    color: {colors.slate_800};
    background: transparent;
}}

/* Sub-section label ("VARIABLES", "STATIC DATA") */
#SidebarSectionTitle {{
    font-size: {style_system.font_medium};
    font-weight: 700;
    letter-spacing: 0.4px;
    color: {colors.slate_400};
    padding-right: {style_system.spacing_xsmall};
}}

/* Horizontal rule next to sub-section title */
#SidebarSectionRule {{
    color: {colors.slate_200};
    background-color: {colors.slate_200};
    border: none;
    max-height: {style_system.border_thin};
}}

/* Item label text */
#SidebarItemLabel {{
    color: {colors.slate_700};
    font-size: {style_system.font_medium};
}}

/* Row hover + selection — applied on the QListWidget viewport */
QListWidget::item {{
    border: none;
    padding: {style_system.spacing_none};
}}

QListWidget::item:hover {{
    background-color: {colors.slate_100};
}}

QListWidget::item:selected {{
    background-color: {colors.sky_50};
}}

QListWidget::item:selected #SidebarItemLabel {{
    color: {colors.sky_700};
}}

/* Bottom Panel */
#BottomPanel {{
    background-color: {colors.slate_50};
    border-top: {style_system.border_thin} solid {colors.slate_200};
}}

#BottomPanel QTabBar::tab {{
    background-color: transparent;
    border: none;
    padding: {style_system.spacing_xsmall} {style_system.spacing_large};
    text-transform: uppercase;
    font-size: {style_system.font_xsmall};
    font-weight: 500;
    color: {colors.slate_500};
}}

#BottomPanel QTabBar::tab:selected {{
    color: {colors.slate_900};
    border-bottom: {style_system.border_medium} solid {colors.slate_900};
}}

/* Status Indicators */
.StatusDot {{
    border-radius: {style_system.radius_medium};
}}

.StatusDot[status="READY"] {{ background-color: {colors.green_500}; }}
.StatusDot[status="PROCESSING"] {{ background-color: {colors.sky_500}; }}
.StatusDot[status="WAITING"] {{ background-color: {colors.yellow_500}; }}
.StatusDot[status="ERROR"] {{ background-color: {colors.red_500}; }}
.StatusDot[status="HIDDEN"] {{ background-color: transparent; }}

/* Buttons */
QPushButton {{
    background-color: {colors.slate_100};
    border: {style_system.border_thin} solid {colors.slate_200};
    border-radius: {style_system.radius_medium};
    padding: {style_system.spacing_xsmall} {style_system.spacing_medium};
}}

QPushButton:hover {{
    background-color: {colors.slate_200};
}}

QPushButton#PrimaryButton {{
    background-color: {colors.sky_600};
    border-color: {colors.sky_700};
    color: white;
}}

QPushButton#PrimaryButton:hover {{
    background-color: {colors.sky_500};
}}

/* Tabs (Main Area) */
QTabWidget::pane {{
    border: none;
    background-color: white;
}}

QTabBar::tab {{
    background-color: {colors.slate_100};
    border: none;
    border-right: {style_system.border_thin} solid {colors.slate_200};
    padding: {style_system.spacing_none} {style_system.spacing_small};
    padding-bottom: {style_system.spacing_xxsmall};
    height: {style_system.spacing_xxlarge};
    color: {colors.slate_500};
    font-size: {style_system.font_medium};
}}

QTabBar::tab:selected {{
    background-color: white;
    color: {colors.slate_900};
    border-top: {style_system.border_thin} solid {colors.sky_500};
}}

QTabBar::close-button {{
    image: url("PLACEHOLDER_CLOSE_NEUTRAL");
    subcontrol-position: right verticalcenter;
    subcontrol-origin: margin;
    border-radius: {style_system.radius_medium};
}}

QTabBar::close-button:hover {{
    image: url("PLACEHOLDER_CLOSE_HOVER");
    background-color: {colors.red_500};
}}

QTabBar::close-button:pressed {{
    image: url("PLACEHOLDER_CLOSE_CLICK");
    background-color: {colors.red_700};
}}

/* Table View */
QTableView {{
    background-color: white;
    gridline-color: {colors.slate_100};
    border: none;
    selection-background-color: {colors.sky_100};
    selection-color: {colors.sky_900};
    font-size: {style_system.font_medium};
}}

QHeaderView::section {{
    background-color: {colors.slate_50};
    padding: {style_system.spacing_xsmall};
    border: none;
    border-right: {style_system.border_thin} solid {colors.slate_100};
    border-bottom: {style_system.border_thin} solid {colors.slate_100};
    font-weight: 600;
    color: {colors.slate_600};
}}

/* ScrollBars */
QScrollBar:vertical {{
    border: none;
    background: transparent;
    width: {style_system.spacing_small};
}}

QScrollBar::handle:vertical {{
    background: {colors.slate_300};
    min-height: 20px;
    border-radius: {style_system.radius_medium};
}}

QScrollBar::handle:vertical:hover {{
    background: {colors.slate_400};
}}

/* ---- DataView components ---- */

/* Info bar at the top of every data sub-view */
#DataInfoBar {{
    background-color: {colors.slate_50};
    border-bottom: {style_system.border_thin} solid {colors.slate_200};
}}

#DataInfoTitle {{
    font-size: {style_system.font_small};
    font-weight: 600;
    color: {colors.slate_800};
}}

#DataInfoMeta {{
    font-size: {style_system.font_xsmall};
    color: {colors.slate_400};
}}

/* LiteralView */
#LiteralTypeChip {{
    font-size: {style_system.font_xsmall};
    font-weight: 600;
    letter-spacing: 0.6px;
    color: {colors.sky_600};
    text-transform: uppercase;
    background-color: {colors.sky_50};
    border: {style_system.border_thin} solid {colors.sky_200};
    border-radius: {style_system.radius_medium};
    padding: {style_system.spacing_xxsmall} {style_system.spacing_large};
}}

#LiteralValue {{
    font-size: {style_system.font_xxxlarge};
    font-weight: 300;
    color: {colors.slate_900};
    letter-spacing: -1px;
}}

#LiteralNameHint {{
    font-size: {style_system.font_xsmall};
    color: {colors.slate_400};
}}

/* Error view */
#DataErrorLabel {{
    color: {colors.slate_500};
    font-size: {style_system.font_small};
}}
"""
