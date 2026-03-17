# Kira GUI Architecture

This document provides a detailed technical overview of the Kira Graphical User Interface (GUI), its component architecture, design decisions, and the evolution from a text-based system to a visual node-based editor.

---

## 1. Overview: The Reactive Paradigm

The Kira GUI is designed as a **reactive layer** over the event-sourced core (`KProject`). It does not manipulate state directly; instead, it observes the core state through a specialized bridge and dispatches commands via events.

### The Bridge: `QTProject`
`gui/qt_project.py`
The `QTProject` class is a `QObject` wrapper that acts as the "glue" between the Python-based core and the PySide6 UI.
- **Signal Dispatch**: Converts core state changes (AddData, Error) into Qt Signals for UI components.
- **Reactivity via Polling**: Runs a high-frequency `QTimer` (default 100ms) to poll the `KEvaluator` for variable status changes (`READY`, `PROCESSING`, `ERROR`).
- **Event Orchestration**: Provides a simplified API (`process_event`) that encapsulates user info and timestamps before sending events to `KProject`.

---

## 2. Structure & Component Hierarchy

The UI follows a classic integrated development environment (IDE) layout, optimized for high-density data and code visualization.

### A. Layout Orchestration (`MainWindow`)
`gui/main_window.py`
- **Activity Bar**: A vertical strip of mode selectors (Explorer, Search, History).
- **Sidebar**: A dynamic tree view managed by `Sidebar` and `QTProject`, showing variables, data, and workflows.
- **Content Tabs**: A central `QTabWidget` that hosts specialized editors (Node Editor, Data View).
- **Bottom Panel**: A tabbed space for logs and background process statuses.

### B. Visual Workflow Editor (The Graphics Stack)
`gui/components/node_editor.py` & `gui/components/node_items.py`

This is the most complex part of the Kira UI, built using the **Qt Graphics View Framework**.

#### 1. The Canvas (`NodeScene` & `NodeView`)
- **NodeScene**: A persistent coordinate space where all graphical items reside. Implements a reactive grid and manages the item lifecycle.
- **NodeView**: The "camera" looking at the scene. It handles sophisticated viewport logic:
    - **Transformation Anchor**: Anchored under the mouse for natural zooming.
    - **Panning**: Implemented via custom mouse tracking (`Qt.ClosedHandCursor`).
    - **Boundary Anchoring**: A specialized system that keeps Workflow Boundaries fixed to the viewport edges regardless of where the user pans.

#### 2. The Node Items (`WorkflowNodeItem`)
Nodes are custom `QGraphicsRectItem` subclasses with a distinct visual anatomy:
- **Header**: Displays the `KNode` type (e.g., `Mean`, `Filter`).
- **Instance Label**: An editable `QGraphicsTextItem` below the node for local variable naming.
- **Ports (`PortItem`)**: Reactive "dots" that handle hover effects and act as anchors for connections.

#### 3. The Connectivity Engine (`ConnectionItem`)
Connections are **Bezier curves** (`QPainterPath.cubicTo`) that link ports.
- **Source-to-Sink Rule**: Standardizes flow logic. Output dots are "Sources" (Fan-out supported); Input dots are "Sinks" (Single-connection limit).
- **Dynamic Tracking**: Nodes set the `ItemSendsScenePositionChanges` flag, forcing connections to recalculate their paths in real-time as nodes are moved.

### C. Data Visualization Layer (`DataView`)
`gui/components/data_view.py`
The visualization layer adapts to the data type being inspected:
- **LiteralView (Strings, Numbers)**: A centered "Rounded Card" that uses **Proportional Scaling** for zoom. It features a bottom-aligned header (Name & Type sits on the baseline) and a full-width separator line that spans from border to border.
- **ArrayView (Numpy)**: A zoom-capable table designed for 1D/2D arrays. Supports **Ctrl + Mouse Wheel zoom** with proportional scaling of both text and row heights.
- **TableView (Pandas)**: A high-performance spreadsheet view with interactive font scaling and a standardized **medium (16px)** default font size.

---

## 3. Design Decisions & Styling

### Premium Aesthetics & Style System
`gui/style_system.py` & `gui/style.py`
Kira uses a custom design system implementation designed for a **Premium Light Theme**.
- **Centralized Tokens**: Every visual constant (fonts, spacing, radii, borders) is defined in `style_system.py`.
- **Dual Representation**: Tokens are stored as both CSS-ready strings (e.g., `font_medium = "16px"`) and raw integers (e.g., `font_medium_i = 16`). This removes the need for brittle string parsing in layout logic.
- **Color Palette**: Based on the `slate` and `sky` color families (Tailwind-inspired) for a modern, calm look.
- **Standardized Units**: The system has transitioned from varying `pt` sizes to a strict **pixel-based (`px`)** standard to ensure consistent cross-platform rendering.
- **Components Styling**: Rounded corners follow a defined hierarchy (`radius_small` to `radius_xlarge`), providing a cohesive software-as-a-service (SaaS) feel.

### Zoom-Invariant Overlays
A key decision was making boundary panels (`WorkflowBoundaryItem`) ignore scene transformations (`ItemIgnoresTransformations`). This ensures that the global Workflow Inputs/Outputs are always readable and accessible, regardless of the zoom level, creating a "HUD" (Heads-Up Display) effect for the workflow.

---

## 4. Issues Encountered & Technical Solutions

### Issue 1: "Flying" Context Panels during Zoom
**Problem**: When zooming out to see a large graph, the Workflow Input/Output panels would shrink into illegibility or move off-screen.
**Solution**: We set the `ItemIgnoresTransformations` flag on boundaries and implemented a `_update_boundaries` listener in the `NodeView`. This manually repositions the panels to the viewport edges whenever the scrollbars or zoom level change.

### Issue 2: Improper Connection Fan-in
**Problem**: Users could connect multiple outputs to a single input, causing logical ambiguity in the DSL.
**Solution**: Enforced a "Strict Sink" rule in `mouseReleaseEvent`. If a connection is dropped on an occupied input port, the previous connection is automatically removed and replaced by the new one.

### Issue 3: Line Disconnection on Move
**Problem**: Moving a node left the Bezier curves floating in mid-air.
**Solution**: Enabled `ItemSendsScenePositionChanges` on `WorkflowNodeItem`. This triggers the `itemChange` notification at the item level, allowing the node to iterate through its ports and signal its connected lines to call `update_path()`.

### Issue 4: Circular Class References
**Problem**: `PortItem` needs `ConnectionItem` and vice-versa, causing `NameError` during initialization.
**Solution**: Used **String Forward References** (e.g., `start_port: 'PortItem'`) and moved critical logic into a unified `node_items.py` file to manage the initialization order correctly.

### Issue 5: Non-Proportional Scaling in Zoom Views
**Problem**: Traditional zoom (e.g., `setPointSize`) only scaled text, leaving container paddings and borders fixed, which looked unbalanced at high zoom levels.
**Solution**: Implemented a **Proportional Scaling System** in `LiteralView`. We use a base `_scale` factor that multiplies all parameters (fonts, padding, radii) in a single `_update_style` call. This ensures the entire component expands/shrinks as a unified graphic item.

---

## 5. Metadata Integration

The UI dynamically discovers its own schema. When a node is created via the search overlay, the editor:
1. Queries the `KProject` for the `KNode` definition.
2. Inspects `knode.input_names` and `knode.output_names`.
3. Dynamically instantiates the correct number of ports on the visual item.
This ensures the GUI is always perfectly synchronized with the underlying Python/DSL logic without manual configuration.
