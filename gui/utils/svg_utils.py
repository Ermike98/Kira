"""
gui/utils/svg_utils.py
----------------------
Utility helpers for recoloring Feather-style SVG icons at runtime.

All icons in gui/icons/ share the same Feather structure:
  <svg ... fill="none" stroke="currentColor" ...>

We recolor by string-replacing `currentColor`, then write the result to a
small temp file so that Qt can load it as a *native vector* QIcon (no
rasterization at a fixed pixel size, scales perfectly at any DPI).
"""

from __future__ import annotations

import os
import re
import tempfile
import atexit
from typing import Optional

from PySide6.QtGui import QIcon


_ICONS_DIR = os.path.join(os.path.dirname(__file__), "..", "icons")

# Cache: modified SVG text → temp file path, so we don't write the same
# content more than once per session.
_svg_cache: dict[str, str] = {}

# Collect temp paths so we can clean up on exit.
_temp_files: list[str] = []


@atexit.register
def _cleanup_temp_icons():
    for path in _temp_files:
        try:
            os.remove(path)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------

def _read_svg(icon_name: str) -> str:
    path = os.path.join(_ICONS_DIR, icon_name)
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def _svg_to_icon(svg_text: str) -> QIcon:
    """
    Write *svg_text* to a temp .svg file (or reuse one from cache) and
    return ``QIcon(path)`` so Qt loads it as a native vector icon.
    """
    if svg_text in _svg_cache:
        return QIcon(_svg_cache[svg_text])

    fd, path = tempfile.mkstemp(suffix=".svg", prefix="kira_icon_")
    _temp_files.append(path)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(svg_text)

    _svg_cache[svg_text] = path
    return QIcon(path)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def recolor_svg(
    icon_name: str,
    stroke_color: str,
    background_color: Optional[str] = None,
    background_radius: int = 6,
) -> str:
    """
    Return SVG text with the stroke recolored and an optional background rect.

    Parameters
    ----------
    icon_name        : filename inside gui/icons/, e.g. ``"database.svg"``
    stroke_color     : any CSS color string for the icon lines, e.g. ``"#334155"``
    background_color : optional fill for a rounded rect behind the icon.
                       Pass ``None`` to leave the background transparent.
    background_radius: corner radius of the background rect (default 6).
    """
    svg = _read_svg(icon_name)

    # Replace stroke="currentColor" with the desired colour
    svg = svg.replace('stroke="currentColor"', f'stroke="{stroke_color}"')

    # Optionally inject a background <rect> right after the opening <svg> tag
    if background_color:
        vb_match = re.search(r'viewBox=["\']([^"\']+)["\']', svg)
        if vb_match:
            parts = vb_match.group(1).split()
            vb_w, vb_h = float(parts[2]), float(parts[3])
        else:
            vb_w = vb_h = 24.0

        bg_rect = (
            f'<rect x="0" y="0" width="{vb_w}" height="{vb_h}" '
            f'rx="{background_radius}" ry="{background_radius}" '
            f'fill="{background_color}" stroke="none"/>'
        )
        svg = re.sub(r'(<svg[^>]*>)', rf'\1{bg_rect}', svg, count=1)

    return svg


def icon_from_svg(svg_text: str) -> QIcon:
    """
    Convert an SVG string (as returned by :func:`recolor_svg`) to a ``QIcon``
    by writing it to a temp file.  Qt renders it as a native vector so it
    looks sharp at any size or DPI.
    """
    return _svg_to_icon(svg_text)


def activity_icon(
    icon_name: str,
    *,
    active: bool = False,
    normal_stroke: str = "#1e293b",      # slate_800 — dark stroke, no bg
    active_stroke: str = "#f8fafc",      # slate_50  — light stroke, bg via QSS
) -> QIcon:
    """
    Return the correct activity-bar icon variant as a vector QIcon.

    Normal → dark stroke, transparent background (button bg from QSS)
    Active → light stroke, transparent background (button bg from QSS)

    The button background colour is set entirely in QSS so it fills the
    full 48×48 square rather than just the SVG viewBox area.
    """
    stroke = active_stroke if active else normal_stroke
    svg = recolor_svg(icon_name, stroke_color=stroke, background_color=None)
    return icon_from_svg(svg)
def get_svg_path(svg_text: str) -> str:
    """
    Ensure *svg_text* is written to a temp file and return its absolute path.
    Useful for QSS 'image: url(...)' styling.
    """
    if svg_text not in _svg_cache:
        # Side effect: populates cache
        _svg_to_icon(svg_text)
    return _svg_cache[svg_text]
