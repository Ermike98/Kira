# Kira GUI Structure

This directory contains the GUI implementation for the Kira data analysis application using PySide6.

## Project Structure

```
gui/
├── __init__.py              # Package initialization
├── main_window.py           # Main application window with tabbed interface
├── homepage.py              # Homepage tab implementation
├── styles.py                # QSS styling definitions
├── panels/                  # Panel widgets
│   ├── __init__.py
│   ├── explorer_panel.py    # Top-left: Element explorer
│   ├── control_panel.py     # Bottom-left: Error messages and info
│   └── preview_panel.py     # Right: Element previews
└── previews/                # Preview widgets for different data types
    ├── __init__.py
    ├── base_preview.py      # Abstract base class for previews
    ├── table_preview.py     # Preview for KTable (pandas DataFrame)
    ├── literal_preview.py   # Preview for KLiteral
    └── node_preview.py      # Preview for KNode (functions, workflows)
```

## Components

### Main Window (`main_window.py`)
- Tabbed interface with a fixed Homepage tab (cannot be closed)
- Additional tabs can be added for editing/visualizing elements
- Applies global styling

### Homepage Tab (`homepage.py`)
- **Explorer Panel** (top-left): Lists all project elements as clickable buttons
- **Control Panel** (bottom-left): Displays error messages, execution logs, and other information
- **Preview Panel** (right): Shows previews of selected elements

### Preview System
The preview system uses a plugin-like architecture:
- `BasePreview`: Abstract base class that all previews inherit from
- Each preview type implements:
  - `update_preview(element)`: Updates the preview with element data
  - `can_preview(element)`: Checks if this preview can handle the element
- `PreviewPanel` automatically selects the appropriate preview widget based on element type

### Current Preview Types
1. **TablePreview**: For `KTable` (pandas DataFrame) - shows data in a table view
2. **LiteralPreview**: For `KLiteral` - shows the literal value and type
3. **NodePreview**: For `KNode` - shows node inputs, outputs, and type information

## Usage

Run the application:
```bash
python run_gui.py
```

Or import and use programmatically:
```python
from gui.main_window import MainWindow
from PySide6.QtWidgets import QApplication

app = QApplication([])
window = MainWindow()
window.show()
app.exec()
```

## Adding New Preview Types

To add a new preview type:

1. Create a new file in `gui/previews/` (e.g., `chart_preview.py`)
2. Inherit from `BasePreview`:
```python
from .base_preview import BasePreview

class ChartPreview(BasePreview):
    def update_preview(self, element):
        # Implement preview update logic
        pass
    
    def can_preview(self, element) -> bool:
        # Return True if this preview can handle the element
        return isinstance(element, Chart)
```

3. Register it in `preview_panel.py`:
```python
from ..previews.chart_preview import ChartPreview

# In _create_preview_widgets():
chart_preview = ChartPreview()
self._preview_widgets.append(chart_preview)
self._stacked_widget.addWidget(chart_preview)
```

## Future Enhancements

- Chart previews for visualization elements
- Error preview for failed KData elements
- Custom preview for workflows
- Drag-and-drop support in explorer
- Search/filter functionality in explorer

