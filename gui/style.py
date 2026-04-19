from gui.utils import colors
from gui import style_system

LIGHT_THEME = f"""
/* Base Colors and Typography */
* {{
    font-family: 'Segoe UI', 'Roboto', 'Helvetica Neue', sans-serif;
    font-size: {style_system.font_small};
    color: {colors.text_primary};
}}

QMainWindow {{
    background-color: {colors.bg_base};
}}

/* Native Menu Bar — light theme */
QMenuBar {{
    background-color: {colors.bg_base};
    color: {colors.text_primary};
    border-bottom: {style_system.border_thin} solid {colors.border_light};
    padding: {style_system.spacing_xxsmall} {style_system.spacing_xsmall};
    font-size: {style_system.font_small};
}}

QMenuBar::item {{
    background-color: transparent;
    color: {colors.text_primary};
    padding: {style_system.spacing_xsmall} {style_system.spacing_small};
    border-radius: {style_system.radius_medium};
    margin: {style_system.spacing_xxsmall} {style_system.spacing_none};
}}

QMenuBar::item:selected,
QMenuBar::item:pressed {{
    background-color: {colors.border_light};
    color: {colors.text_primary};
}}

QMenu {{
    background-color: {colors.bg_panel};
    color: {colors.text_primary};
    border: {style_system.border_thin} solid {colors.border_light};
    border-radius: {style_system.radius_large};
    padding: {style_system.spacing_xsmall};
}}

QMenu::item {{
    padding: {style_system.spacing_small} {style_system.spacing_xlarge} {style_system.spacing_small} {style_system.spacing_large};
    border-radius: {style_system.radius_medium};
    color: {colors.text_primary};
}}

QMenu::item:selected {{
    background-color: {colors.bg_surface};
    color: {colors.text_primary};
}}

QMenu::item:disabled {{
    color: {colors.text_tertiary};
}}

QMenu::separator {{
    height: {style_system.border_thin};
    background: {colors.border_light};
    margin: {style_system.spacing_xsmall} {style_system.spacing_small};
}}

/* Activity Bar */
#ActivityBar {{
    background-color: {colors.text_primary};
    border-right: {style_system.border_thin} solid {colors.text_primary};
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
    background-color: {colors.text_primary};
}}

.ActivityButton[active="true"] {{
    background-color: {colors.text_secondary};
}}

/* ---- Sidebar ---- */
#Sidebar {{
    background-color: {colors.bg_base};
}}

/* Thin accent line between activity bar and sidebar */
#SidebarBorder {{
    background-color: {colors.border_light};
    border: none;
}}

/* Large view title at the top ("Data Explorer", "WORKFLOWS") */
#SidebarHeader {{
    font-size: {style_system.font_medium};
    font-weight: 700;
    letter-spacing: 0.5px;
    padding: {style_system.spacing_medium} {style_system.spacing_medium} {style_system.spacing_small} {style_system.spacing_medium};
    color: {colors.text_primary};
    background: transparent;
}}

/* Sub-section label ("VARIABLES", "STATIC DATA") */
#SidebarSectionTitle {{
    font-size: {style_system.font_medium};
    font-weight: 700;
    letter-spacing: 0.4px;
    color: {colors.text_tertiary};
    padding-right: {style_system.spacing_xsmall};
}}

/* Horizontal rule next to sub-section title */
#SidebarSectionRule {{
    color: {colors.border_light};
    background-color: {colors.border_light};
    border: none;
    max-height: {style_system.border_thin};
}}

/* Item label text */
#SidebarItemLabel {{
    color: {colors.text_primary};
    font-size: {style_system.font_medium};
}}

/* Row hover + selection — applied on the QListWidget viewport */
QListWidget::item {{
    border: none;
    padding: {style_system.spacing_none};
}}

QListWidget::item:hover {{
    background-color: {colors.bg_surface};
}}

QListWidget::item:selected {{
    background-color: {colors.accent_light};
}}

QListWidget::item:selected #SidebarItemLabel {{
    color: {colors.accent_active};
}}

/* Bottom Panel */
#BottomPanel {{
    background-color: {colors.bg_base};
    border-top: {style_system.border_thin} solid {colors.border_light};
}}

#BottomPanel QTabBar::tab {{
    background-color: transparent;
    border: none;
    padding: {style_system.spacing_xsmall} {style_system.spacing_large};
    text-transform: uppercase;
    font-size: {style_system.font_xsmall};
    font-weight: 500;
    color: {colors.text_secondary};
}}

#BottomPanel QTabBar::tab:selected {{
    color: {colors.text_primary};
    border-bottom: {style_system.border_medium} solid {colors.text_primary};
}}

/* Status Indicators */
.StatusDot {{
    border-radius: {style_system.radius_medium};
}}

.StatusDot[status="READY"] {{ background-color: {colors.status_ready}; }}
.StatusDot[status="PROCESSING"] {{ background-color: {colors.accent_base}; }}
.StatusDot[status="WAITING"] {{ background-color: {colors.status_waiting}; }}
.StatusDot[status="ERROR"] {{ background-color: {colors.status_error}; }}
.StatusDot[status="HIDDEN"] {{ background-color: transparent; }}

/* Buttons */
QPushButton {{
    background-color: {colors.bg_surface};
    border: {style_system.border_thin} solid {colors.border_light};
    border-radius: {style_system.radius_medium};
    padding: {style_system.spacing_xsmall} {style_system.spacing_medium};
}}

QPushButton:hover {{
    background-color: {colors.border_light};
}}

QPushButton#PrimaryButton {{
    background-color: {colors.accent_hover};
    border-color: {colors.accent_active};
    color: white;
}}

QPushButton#PrimaryButton:hover {{
    background-color: {colors.accent_base};
}}

/* Tabs (Main Area) */
QTabWidget::pane {{
    border: none;
    background-color: {colors.bg_panel};
}}

QTabBar::tab {{
    background-color: {colors.bg_surface};
    border: none;
    border-right: {style_system.border_thin} solid {colors.border_light};
    padding: {style_system.spacing_none} {style_system.spacing_small};
    padding-bottom: {style_system.spacing_xxsmall};
    height: {style_system.spacing_xxlarge};
    color: {colors.text_secondary};
    font-size: {style_system.font_medium};
}}

QTabBar::tab:selected {{
    background-color: {colors.bg_panel};
    color: {colors.text_primary};
    border-top: {style_system.border_thin} solid {colors.accent_base};
}}

QTabBar::close-button {{
    image: url("PLACEHOLDER_CLOSE_NEUTRAL");
    subcontrol-position: right verticalcenter;
    subcontrol-origin: margin;
    border-radius: {style_system.radius_medium};
}}

QTabBar::close-button:hover {{
    image: url("PLACEHOLDER_CLOSE_HOVER");
    background-color: {colors.status_error};
}}

QTabBar::close-button:pressed {{
    image: url("PLACEHOLDER_CLOSE_CLICK");
    background-color: {colors.danger_hover};
}}

/* Table View */
QTableView {{
    background-color: {colors.bg_panel};
    alternate-background-color: {colors.bg_surface};
    gridline-color: {colors.border_light};
    border: none;
    selection-background-color: {colors.accent_light};
    selection-color: {colors.text_primary};
    font-size: {style_system.font_medium};
    outline: none;
}}

QHeaderView::section {{
    background-color: {colors.bg_base};
    padding: {style_system.spacing_xsmall};
    border: none;
    border-right: {style_system.border_thin} solid {colors.border_light};
    border-bottom: {style_system.border_thin} solid {colors.border_light};
    font-weight: 600;
    color: {colors.text_secondary};
}}

QTableCornerButton::section {{
    background-color: {colors.bg_base};
    border: none;
    border-right: {style_system.border_thin} solid {colors.border_light};
    border-bottom: {style_system.border_thin} solid {colors.border_light};
}}

/* ScrollBars */
QScrollBar:vertical {{
    border: none;
    background: transparent;
    width: {style_system.spacing_small};
}}

QScrollBar::handle:vertical {{
    background: {colors.border_medium};
    min-height: 20px;
    border-radius: {style_system.radius_medium};
}}

QScrollBar::handle:vertical:hover {{
    background: {colors.text_tertiary};
}}

/* ---- DataView components ---- */

/* Info bar at the top of every data sub-view */
#DataInfoBar {{
    background-color: {colors.bg_base};
    border-bottom: {style_system.border_thin} solid {colors.border_light};
}}

#DataInfoTitle {{
    font-size: {style_system.font_small};
    font-weight: 600;
    color: {colors.text_primary};
}}

#DataInfoMeta {{
    font-size: {style_system.font_xsmall};
    color: {colors.text_tertiary};
}}

/* LiteralView */
#LiteralTypeChip {{
    font-size: {style_system.font_xsmall};
    font-weight: 600;
    letter-spacing: 0.6px;
    color: {colors.accent_hover};
    text-transform: uppercase;
    background-color: {colors.accent_light};
    border: {style_system.border_thin} solid {colors.accent_border};
    border-radius: {style_system.radius_medium};
    padding: {style_system.spacing_xxsmall} {style_system.spacing_large};
}}

#LiteralValue {{
    font-size: {style_system.font_xxxlarge};
    font-weight: 300;
    color: {colors.text_primary};
    letter-spacing: -1px;
}}

#LiteralNameHint {{
    font-size: {style_system.font_xsmall};
    color: {colors.text_tertiary};
}}

/* Error view */
#DataErrorLabel {{
    color: {colors.text_secondary};
    font-size: {style_system.font_small};
}}

/* ---- Step Editor (Pipeline Editor) ---- */

#StepEditorPanel {{
    background-color: {colors.bg_base};
    border-left: {style_system.border_thin} solid {colors.border_light};
}}

#StepEditorHeader {{
    background-color: {colors.bg_base};
    border-bottom: {style_system.border_thin} solid {colors.border_light};
}}

#StepEditorHeader[status="READY"] {{
    background-color: {colors.bg_status_ready};
    border-bottom: {style_system.border_medium} solid {colors.border_status_ready};
}}

#StepEditorHeader[status="PROCESSING"] {{
    background-color: {colors.bg_status_processing};
    border-bottom: {style_system.border_medium} solid {colors.border_status_processing};
}}

#StepEditorHeader[status="ERROR"] {{
    background-color: {colors.bg_status_error};
    border-bottom: {style_system.border_medium} solid {colors.border_status_error};
}}

#StepEditorTitle {{
    font-size: {style_system.font_medium};
    font-weight: 700;
    color: {colors.text_primary};
    letter-spacing: 0.3px;
    padding: 2px 8px;
    border-radius: {style_system.radius_medium};
}}

#StepEditorTitle[status="READY"] {{
    background: {colors.bg_status_ready};
    color: {colors.text_primary};
}}

#StepEditorTitle[status="PROCESSING"] {{
    background: {colors.bg_status_processing};
    color: {colors.text_primary};
}}

#StepEditorTitle[status="ERROR"] {{
    background: {colors.bg_status_error};
    color: {colors.text_primary};
}}

/* Source input styled as a minimalist box (replaces the card container) */
#SourceCard {{
    background-color: transparent;
    border: none;
    margin-bottom: {style_system.spacing_xxsmall};
}}

#StepSourceInput {{
    background-color: {colors.bg_panel};
    border: {style_system.border_thin} solid {colors.border_light};
    border-radius: {style_system.radius_large};
    padding: {style_system.spacing_small} {style_system.spacing_medium};
    font-size: {style_system.font_small};
    color: {colors.text_primary};
}}

#StepSourceInput:hover {{
    border-color: {colors.border_medium};
}}

#StepSourceInput:focus {{
    border-color: {colors.accent_focus};
    outline: none;
}}

/* Step Card */
#StepCard {{
    background-color: {colors.bg_panel};
    border: {style_system.border_thin} solid {colors.border_light};
    border-radius: {style_system.radius_large};
}}

#StepCard:hover {{
    border-color: {colors.border_medium};
}}

#StepBadge {{
    font-size: {style_system.font_xsmall};
    font-weight: 600;
    color: {colors.text_tertiary};
}}

#StepFuncName {{
    font-size: {style_system.font_small};
    font-weight: 700;
    color: {colors.text_primary};
}}

#StepFuncInput {{
    font-size: {style_system.font_small};
    padding: {style_system.spacing_xxsmall} {style_system.spacing_xsmall};
    border: {style_system.border_thin} solid {colors.border_light};
    border-radius: {style_system.radius_medium};
    background-color: transparent;
}}

#StepFuncInput:focus {{
    border-color: {colors.accent_focus};
    background-color: {colors.bg_panel};
}}

#StepDragHandle {{
    font-size: {style_system.font_large};
    color: {colors.border_medium};
    padding: 0px {style_system.spacing_xxsmall};
}}

#StepDeleteButton {{
    background-color: transparent;
    border: none;
    border-radius: {style_system.radius_medium};
    font-size: {style_system.font_medium};
    font-weight: 700;
    color: {colors.text_tertiary};
    padding: 0px;
}}

#StepDeleteButton:hover {{
    background-color: {colors.danger_light};
    color: {colors.status_error};
}}

/* Step parameter row */
#StepParamLabel {{
    font-size: {style_system.font_small};
    color: {colors.text_secondary};
    font-weight: 500;
}}

#StepParamInput {{
    font-size: {style_system.font_small};
    padding: {style_system.spacing_xsmall} {style_system.spacing_small};
    border: {style_system.border_thin} solid {colors.border_light};
    border-radius: {style_system.radius_medium};
    background-color: transparent;
    color: {colors.text_primary};
}}

#StepParamInput:focus {{
    background-color: {colors.bg_panel};
    border: {style_system.border_thin} solid {colors.accent_focus};
    outline: none;
}}


/* Add step button */
#AddStepButton {{
    background-color: transparent;
    border: {style_system.border_thin} dashed {colors.border_medium};
    border-radius: {style_system.radius_large};
    padding: {style_system.spacing_small} {style_system.spacing_large};
    color: {colors.text_secondary};
    font-size: {style_system.font_small};
    font-weight: 600;
    margin-top: {style_system.spacing_small};
}}

#AddStepButton:hover {{
    background-color: {colors.accent_light};
    border-color: {colors.accent_hover};
    color: {colors.accent_hover};
}}

/* Pipeline arrow connector */
#PipelineArrow {{
    font-size: {style_system.font_medium};
    color: {colors.border_medium};
}}

/* Autocomplete Popup */
QListView#AutocompletePopup {{
    background-color: {colors.bg_panel};
    border: {style_system.border_thin} solid {colors.border_light};
    border-radius: {style_system.radius_medium};
    outline: none;
    font-size: {style_system.font_small};
    padding: {style_system.spacing_xxsmall};
}}

QListView#AutocompletePopup::item {{
    padding: {style_system.spacing_xsmall} {style_system.spacing_small};
    border-radius: {style_system.radius_small};
    color: {colors.text_primary};
}}

QListView#AutocompletePopup::item:hover,
QListView#AutocompletePopup::item:selected {{
    background-color: {colors.accent_light};
    color: {colors.accent_active};
}}
"""
