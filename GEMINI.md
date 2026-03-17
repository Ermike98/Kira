# Kira Project - Core State Architecture (GEMINI.md)

This document provides a deep-dive into the `kproject` core architecture. It describes the internal state management, reactive execution model, and persistence strategy designed for the Kira application.

---

## 1. Core Philosophy: Event Sourcing & State Reconstruction

Kira does **not** store a traditional "snapshot" of the application state. Instead, it uses **Event Sourcing**. Every user action (adding a variable, updating a workflow, etc.) is recorded as a `KEvent`.

### **Why Event Sourcing?**
1.  **Perfect Consistency**: Replaying events from scratch always results in the same state.
2.  **Robust Undo/Redo**: History navigation is just replaying up to a specific point.
3.  **Audit Trail**: The entire project history is stored in a linear log.

### **State Reconstruction Pattern**
When navigating history (Undo/Redo/Restore), `KProject` performs a **Full Reconstruction**:
1.  It stops the background evaluator.
2.  It re-instantiates the `KContext`, `KStateManager`, and `KEvaluator`.
3.  It replays all events in the log up to the target version.
*Note: While slower than "inverse events", this ensures high correctness in a complex dependency-heavy environment.*

---

## 2. Component Responsibilities

### **A. KProject (The Orchestrator)**
`kproject/kproject.py`
The "Brain" of the system. It is the only component the UI should interact with directly.
- **Orchestration**: Dispatches events to Persistence, State, and Evaluation managers in the correct sequence.
- **State Versioning**: Uses **SHA-256 Hash Chaining**. Each state is identified by a hash: `new_hash = sha256(prev_hash + current_event_id)`.
- **History Pointer**: Tracks `_current_index` to know where in the event log the application currently sits.
- **Divergence Logic**: If a new event is added while the pointer is in the middle of history (after an Undo), it **truncates** the "future" events to create a new branch.

### **B. KPersistenceManager (The Historian)**
`kproject/kpersistence_manager.py`
Manages the SQLite-backed storage (`.kira` files).
- **Event Log**: Stores sequential events in an `events` table.
- **Heavy Data Handling (Blobs)**: `KData` (tables, large arrays) are **not** stored in the event body. They are stored in `ktable_storage` keyed by a content-hash (`blob_id`). 
- **Efficiency**: 
    - **Lazy Persistence**: Operates in memory for unsaved projects.
    - **Data Caching**: Keeps memory references to loaded `KData` to avoid redundant disk I/O.
    - **Truncation**: Supports physical deletion of rows from SQLite to match the `KProject` divergence model.

### **C. KEvaluator (The Engine)**
`kproject/kevaluator.py`
A non-blocking background worker that executes the Kira DSL.
- **Threaded Execution**: Runs a daemon thread that pulls variables from a FIFO queue.
- **Reactive Dependency Tracking**: When an event affects a variable, it uses BFS (Breadth-First Search) via `KStateManager` to find all downstream dependents and adds them to the work queue.
- **Status Tracking**: Maintains a thread-safe map of variable statuses (`WAITING`, `PROCESSING`, `READY`, `ERROR`).
- **Safety**: Supports `stop()` to cleanly terminate the worker thread during state reconstruction.

### **D. KStateManager (The Architect)**
`kproject/kstate_manager.py`
Manages the structural metadata of the project.
- **AST Mapping**: Maps variable names to their parsed Abstract Syntax Trees.
- **Dependency Graph**: Tracks which variables/workflows depend on which symbols.
- **Compiled Objects**: Stores the `KNodeInstance` and `KNode` objects used by the evaluator.

---

## 3. Handling Heavy Data (KData)

Kira distinguishes between **Metadata** and **Heavy Data**.

1.  **Metadata (KEvent)**: Small strings, numbers, or code. Stored directly in the `body` of a `KEvent`.
2.  **Heavy Data (KData)**: Large tables or dataframes.
    -   When `AddData` occurs, the UI passes the `KData` object to `KPersistenceManager`.
    -   `KPersistenceManager` serializes the data to a binary format (e.g., Parquet/Binary) and stores it in the SQLite blob table.
    -   The `KEvent` only records the *target name* and *blob ID*.
    -   During reconstruction, `KProject` requests the data by name from `KPersistenceManager`, which either returns the cached memory instance or de-serializes it from disk.

---

## 4. Edge Cases & Safety

### **History Divergence**
If the user:
1.  Creates Event A, B, C.
2.  Undoes to Event A.
3.  Creates Event D.
**Result**: Events B and C are deleted from memory and **permanently removed from the SQLite file**. Event D becomes the new successor to A.

### **Thread Safety**
-   `KContext` and `KEvaluator` use Locks (`threading.Lock`) to ensure the UI can query values (Pull architecture) while the background thread is writing them.
-   `KProject` ensures the evaluator is stopped before any state reconstruction begins.

### **Dependency Cycles**
Currently, the system assumes a Directed Acyclic Graph (DAG). Users should avoid circular references (e.g., `A = B` and `B = A`), as the BFS will currently loop or overflow depending on depth checks (to be implemented).

---

## 5. UI Integration Guidelines

The UI should not "push" updates to the core or manipulate `KProject` internal lists. Instead:
1.  **Command**: UI sends a command (e.g., `add_variable`) via the `QTProject` wrapper.
2.  **Event Generation**: `QTProject` encapsulates this as a `KEvent` with current `UserInfo`.
3.  **Core Processing**: `KProject` processes the event, triggering persistence and evaluation.
4.  **Reactivity**: UI components subscribe to `QTProject` signals (e.g., `status_changed`, `history_updated`) to refresh their views.

---

## 6. UI Architecture & Reactive Bridge

The Kira UI is a reactive observer of the event-sourced core, centered around the `QTProject` bridge and a unified design system.

### **A. QTProject (The Bridge)**
`gui/qt_project.py`
The single source of truth for the PySide6 application.
- **Signal Dispatch**: Translates core state changes into Qt signals.
- **Polling Loop**: A high-frequency `QTimer` detects status updates from the background `KEvaluator`.
- **Event Orchestration**: Encapsulates user commands as `KEvent` objects with enriched meta-data.

### **B. Premium Style System**
`gui/style_system.py` & `gui/style.py`
Kira uses a **token-based design system** to ensure consistency and easy scaling.
- **Centralized Tokens**: Every visual constant (fonts, spacing, radii, borders) is defined as a token.
- **Dual Representation**: Tokens exist as CSS strings (for QSS) and raw integers (for layout logic), preventing brittle parsing.
- **Standardized Units**: A strict **pixel-based (`px`)** standard ensures reliable rendering across platforms.
- **Aesthetics**: Premium light theme using the `slate` and `sky` color families with rounded corners and subtle borders.

### **C. Component-Based Visualization Layer**
The interface is divided into specialized, semi-autonomous layers:

#### **1. Visual Workflow Editor (Graphics Stack)**
`gui/components/node_editor.py`
Built on the **Qt Graphics View Framework**, it provides a high-density canvas for visual programming.
- **Reactive Grids**: A coordinate-based system for node placement and Bezier-curve connectivity.
- **Transformation Handling**: Intelligent viewport logic ensuring boundary panels remain zoom-invariant while the main graph scales.

#### **2. Data Visualization (`DataView`)**
`gui/components/data_view.py`
Adapts to the underlying `KData` type:
- **LiteralView**: A centered "Card" for scalar values. Uses **Proportional Scaling** where the entire card (padding, fonts, radii) scales during zoom.
- **ArrayView & TableView**: High-performance spreadsheet components for Numpy and Pandas data, featuring interactive font scaling and standardized padding.

#### **3. Sidebar & Project Explorer**
`gui/components/sidebar.py`
A reactive bridge to the project's symbol table, providing a tree-based navigation of variables, data, and workflows.

---

## 7. Kira DSL (klanguage) Architecture

The Kira Domain Specific Language (DSL) is a custom scriptable layer that allows users to define variables, transformations, and workflows. It is designed to be reactive, readable, and easily extensible.

### **A. Tokenization (ktokenizer.py)**
The `ktokenizer` converts raw string expressions into a linear stream of `KToken` objects.
- **Support**: Identifies literals (numbers, strings), symbols (variable names), operators (`+`, `-`, `*`, `/`, `^`, `==`, `!=`, etc.), and brackets.
- **Pipe Operator (`|>`)**: Specialized support for function chaining.
- **Keywords**: Reserved words like `workflow` and `return`.

### **B. Abstract Syntax Tree (kast.py)**
The language uses a **Recursive Descent Parser** to build a hierarchical AST from the token stream.
- **Precedence Hierarchy**: Strictly defined operator precedence (Arithmetic > Comparison > Logic > Pipe > Assignment).
- **Desugaring Pattern**: Complex operators are often transformed (desugared) into simpler forms during parsing.
    - **Pipe Desugaring**: `f(a, b) |> g(c)` is transformed into `g(f(a, b), c)` at the AST level, ensuring the rest of the engine only sees standard function calls.
- **Nodes**: Defines structure for `AstCall`, `AstSymbol`, `AstLiteral`, `AstAssignment`, and `AstWorkflow`.

### **C. Program Builder (kbuilder.py)**
The Builder bridges the gap between the static AST and the runtime `KObject` model.
- **Translation**: Converts AST nodes into executable `KNodeInstance` objects or static `KData` objects.
- **Workflow Registration**: Transforms `AstWorkflow` definitions into `KWorkflow` objects capable of being executed or nested.
- **Symbol Linking**: Resolves variable names into `KSymbol` references that the `KEvaluator` can track in the dependency graph.

### **D. Language Features**
- **Implicit Identity**: Simple symbol assignments (e.g., `y = x`) are wrapped in "identity nodes" to maintain reactive consistency.
- **Dynamic Property Access**: Supports dot-notation (e.g., `df.column`) which is translated to `getattr` calls in the core.
- **Functional Shorthand**: Symbols can be treated as functions in the right-hand side of a pipe (e.g., `x |> f` becomes `f(x)`).
