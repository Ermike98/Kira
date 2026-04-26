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
- **Status Updates**: Updates variable statuses via `KStatusBus` (see below). `KEvaluator` itself does **not** store statuses — it delegates entirely to the bus.
- **Safety**: Supports `stop()` to cleanly terminate the worker thread during state reconstruction.

### **D. KStatusBus (The Status Hub)**
`kproject/kstatus_bus.py`
Thread-safe, centralized event bus for variable status management.
- **Single Source of Truth**: Owns the `_variable_statuses` dictionary and the associated `threading.Lock`.
- **Status Lifecycle**: Variables move through `WAITING` → `PROCESSING` → `READY` | `ERROR`.
- **Pub/Sub**: Components subscribe to `KStatusEvent.VARIABLE_STATUS_CHANGED` to receive `(name, status)` callbacks when status changes.
- **Used By**: `KEvaluator` calls `set_status()` during evaluation; `KProject` exposes `get_status()` to the UI; `QTProject` subscribes for reactive UI updates.

### **E. KStateManager (The Architect)**
`kproject/kstate_manager.py`
Manages the structural metadata of the project.
- **AST Mapping**: Maps variable names to their parsed Abstract Syntax Trees.
- **Dependency Graph**: Tracks which variables/workflows depend on which symbols.
- **Compiled Objects**: Stores the `KNodeInstance` and `KNode` objects used by the evaluator.

---

## 3. Data Model

Kira has a layered data model built around `KObject` → `KData` → `KDataValue`.

### **A. KData (The Container)**
`kira/kdata/kdata.py`
A named container holding an optional `KDataValue` and/or `KException`:
- `value != None, error is None` → success
- `value is None, error != None` → error
- `value != None, error != None` → success with warning

### **B. KDataValue Types**
| Type | File | Description |
|------|------|-------------|
| `KLiteral` | `kira/kdata/kliteral.py` | Scalar values (int, float, str, bool, date, datetime). Uses `KLiteralType` enum and numpy types for standardization. |
| `KArray` | `kira/kdata/karray.py` | Homogeneous series backed by `pd.Series`. Infers `KLiteralType` from data. Also supports heterogeneous arrays of `KDataValue` objects (lit_type `COLLECTION`). |
| `KTable` | `kira/kdata/ktable.py` | Tabular data backed by `pd.DataFrame`. |
| `KCollection` | `kira/kdata/kcollection.py` | A named bag of `KData` objects. Used for multi-output nodes and multi-variadic argument grouping. |
| `KErrorValue` | `kira/kdata/kerrorvalue.py` | Wraps a `KException` as a `KDataValue`. Used to propagate errors through data structures (e.g., inside a KArray) without aborting evaluation. |

### **C. KLiteralType Enum**
`kira/kdata/kliteral.py`
Defines the scalar/element type taxonomy:
`ANY`, `INTEGER`, `NUMBER`, `STRING`, `BOOLEAN`, `DATE`, `DATETIME`, `COLLECTION`.
- `COLLECTION` is used for `KArray` instances containing `KDataValue` objects (e.g., arrays of `KCollection`).

---

## 4. Type System

Kira uses a structural type system based on `KTypeInfo` for input/output validation of nodes.

### **A. Core Type Infos**
| TypeInfo | File | Description |
|----------|------|-------------|
| `KAnyTypeInfo` | `kira/ktypeinfo/any_type.py` | Matches anything. |
| `KLiteralTypeInfo` | `kira/kdata/kliteral.py` | Matches `KData` containing a `KLiteral` of a specific `KLiteralType`. Exposes `lit_type` property. |
| `KArrayTypeInfo` | `kira/kdata/karray.py` | Matches `KData` containing a `KArray`. Accepts a `KTypeInfo` for element validation. |
| `KTableTypeInfo` | `kira/kdata/ktable.py` | Matches `KData` containing a `KTable`. |
| `KCollectionTypeInfo` | `kira/kdata/kcollection.py` | Matches `KData` containing a `KCollection`. Optionally validates field types via a `fields: dict[str, KTypeInfo]`. Exposes `fields` and `field_names` properties. |
| `KUnionTypeInfo` | `kira/ktypeinfo/union_type.py` | Matches if any of the contained type infos match. |
| `KVariadicTypeInfo` | `kira/ktypeinfo/variadic_type.py` | Marks a variadic argument. Delegates validation to `KArrayTypeInfo`. See Section 8. |

### **B. KArrayTypeInfo (Extended)**
`kira/kdata/karray.py`
`KArrayTypeInfo` accepts a `KTypeInfo` as its element type:
- **`KAnyTypeInfo`**: Accepts any KArray.
- **`KLiteralTypeInfo`**: Checks `KArray.lit_type` matches the expected literal type (original behavior).
- **`KCollectionTypeInfo` or other**: Validates every element individually by wrapping each in `KData` and calling `element_type.match()`.

Pre-defined constants: `K_ARRAY_TYPE`, `K_ARRAY_INTEGER_TYPE`, `K_ARRAY_NUMBER_TYPE`, `K_ARRAY_STRING_TYPE`, `K_ARRAY_BOOLEAN_TYPE`, `K_ARRAY_DATE_TYPE`, `K_ARRAY_DATETIME_TYPE`.

---

## 5. Handling Heavy Data (KData)

Kira distinguishes between **Metadata** and **Heavy Data**.

1.  **Metadata (KEvent)**: Small strings, numbers, or code. Stored directly in the `body` of a `KEvent`.
2.  **Heavy Data (KData)**: Large tables or dataframes.
    -   When `AddData` occurs, the UI passes the `KData` object to `KPersistenceManager`.
    -   `KPersistenceManager` serializes the data to a binary format (e.g., Parquet/Binary) and stores it in the SQLite blob table.
    -   The `KEvent` only records the *target name* and *blob ID*.
    -   During reconstruction, `KProject` requests the data by name from `KPersistenceManager`, which either returns the cached memory instance or de-serializes it from disk.

---

## 6. Edge Cases & Safety

### **History Divergence**
If the user:
1.  Creates Event A, B, C.
2.  Undoes to Event A.
3.  Creates Event D.
**Result**: Events B and C are deleted from memory and **permanently removed from the SQLite file**. Event D becomes the new successor to A.

### **Thread Safety**
-   `KContext` and `KStatusBus` use Locks (`threading.Lock`) to ensure the UI can query values and statuses while the background thread is writing them.
-   `KProject` ensures the evaluator is stopped before any state reconstruction begins.

### **Dependency Cycles**
Currently, the system assumes a Directed Acyclic Graph (DAG). Users should avoid circular references (e.g., `A = B` and `B = A`), as the BFS will currently loop or overflow depending on depth checks (to be implemented).

---

## 7. UI Integration Guidelines

The UI should not "push" updates to the core or manipulate `KProject` internal lists. Instead:
1.  **Command**: UI sends a command (e.g., `add_variable`) via the `QTProject` wrapper.
2.  **Event Generation**: `QTProject` encapsulates this as a `KEvent` with current `UserInfo`.
3.  **Core Processing**: `KProject` processes the event, triggering persistence and evaluation.
4.  **Reactivity**: UI components subscribe to `KStatusBus` events (via `QTProject`) to refresh their views when variable statuses change.

---

## 8. Node System & Variadic Arguments

### **A. KNode (The Abstract Node)**
`kira/knodes/knode.py`
Base class for all executable nodes.
- **Input/Output Schema**: Declared as `list[tuple[str, KTypeInfo] | str]`.
- **Default Inputs**: Optional `dict[str, KDataValue]` for arguments with defaults.
- **Type Validation**: `__call__` validates all inputs via `KTypeInfo.match()` uniformly — no special-case logic for any type including variadic.
- **`has_variadic` property**: `True` if the last input type is `KVariadicTypeInfo`. Set at init time.
- **Constraint**: Only the last argument may be variadic.

### **B. KNodeInstance (The Evaluator)**
`kira/knodes/knode_instance.py`
Wraps a `KNode` with bound inputs for a specific call site.
- **Evaluation Flow**:
  1. Resolves the target node (if passed by name).
  2. Validates input count: `num_fixed = len(input_names) - (1 if has_variadic else 0)`.
  3. Evaluates all inputs in order.
  4. Builds the `inputs` dict: fixed inputs by name, variadic inputs wrapped into a `KArray`.
  5. Calls `node(inputs, context)`.
- **Variadic Handling**:
  - **Single variadic**: Each evaluated value's `KDataValue` is packed directly into a `KArray`. Errors become `KErrorValue` objects.
  - **Multi-variadic** (element_type is `KCollectionTypeInfo`): Evaluated arguments are grouped into `KCollection` objects based on `field_names`, then packed into a `KArray`. If the count isn't a multiple of the group size, a `KData` with error is assigned instead of the array.
- **Auto-Unpack**: When an input evaluates to a `KTable`, its columns are injected into the `formulas_context` as `KArray` objects for use by deferred expressions (`$...$`).

### **C. KFunction (Decorated Nodes)**
`kira/knodes/kfunction.py`
A `KNode` backed by a Python callable, typically created via the `@kfunction` decorator.
- **`use_values=True`** (default): Unwraps `KData` → `KDataValue` before calling the function. The variadic argument arrives as a `KArray`.
- **`use_values=False`**: Passes raw `KData` objects. Required for multi-variadic functions that need to traverse `KCollection` internals.
- **`use_context=True`**: Passes the `KContext` as a keyword argument `context`.

### **D. KVariadicTypeInfo**
`kira/ktypeinfo/variadic_type.py`
Marks an input as variadic. The node receives a single `KData` wrapping a `KArray`.
- **Constructor**: `KVariadicTypeInfo(element_type: KTypeInfo | None = None)`. Defaults to `KAnyTypeInfo()`.
- **Validation**: Delegates to `KArrayTypeInfo(element_type).match()`.
- **Single variadic**: `KVariadicTypeInfo()` or `KVariadicTypeInfo(K_STRING_TYPE)` — each arg becomes an element.
- **Multi-variadic**: `KVariadicTypeInfo(KCollectionTypeInfo({"name": K_STRING_TYPE, "values": K_ARRAY_TYPE}))` — args are grouped into `KCollection` objects by `KNodeInstance`.

### **E. Example: `table` function**
```python
@kfunction(
    inputs=[("columns", KVariadicTypeInfo(KCollectionTypeInfo({
        "name": K_STRING_TYPE,
        "values": K_ARRAY_TYPE
    })))],
    outputs=[("table", KTableTypeInfo())],
    name="table",
    use_values=False
)
def k_table(columns: KData):
    arr = columns.value  # KArray of KCollections
    data = {}
    for col in arr.value:
        name = col.get("name").value.value   # KLiteral -> str
        values = col.get("values").value.value  # KArray -> pd.Series
        data[str(name)] = values
    return [KTable(pd.DataFrame(data))]
```
DSL: `t = table("col1", [1, 2, 3], "col2", [4, 5, 6])`

---

## 9. UI Architecture & Reactive Bridge

The Kira UI is a reactive observer of the event-sourced core, centered around the `QTProject` bridge and a unified design system.

### **A. QTProject (The Bridge)**
`gui/qt_project.py`
The single source of truth for the PySide6 application.
- **Signal Dispatch**: Subscribes to `KStatusBus` events and re-emits them as Qt signals on the main thread.
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

## 10. Kira DSL (klanguage) Architecture

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
- **Deferred Expressions (Formulas)**: Expressions wrapped in `$` (e.g., `$diff(e)$`) are parsed as formulas. They bypass global dependency tracking and are evaluated dynamically when nodes resolve their inputs, making them ideal for step-by-step pipeline transformations where variables are resolved locally (e.g., dataframe columns).

---

## 11. Function Libraries

Kira ships with several function libraries registered via `KLibrary`:

| Library | File | Contents |
|---------|------|----------|
| Builtin | `library/builtin_library.py` | Arithmetic ops (`add`, `sub`, `mul`, `div`), comparison, logic, casting, string ops, `getitem`, `table` (multi-variadic). |
| Math | `library/math_library.py` | `exp`, `log`, `abs`, `sign`, `gamma`, `sigmoid`, and more via numpy. |
| Statistics | `library/statistics_library.py` | `min`, `max`, `mean`, `median`, `std`, `var`, `quantile`. |
| Array | `library/array_library.py` | Array-specific operations. |
| Table | `library/table_library.py` | Table/DataFrame operations. |

Libraries are registered in `library/__init__.py` and loaded during `KProject` initialization.
