# Kira Application State Architecture Design

This document outlines the proposed architecture for managing the application state in your reactive GUI application (Kira), utilizing event sourcing, the DSL, and non-blocking execution.

## 1. High-Level Architecture

The core philosophy separates state management, persistence, execution, and UI to keep the application responsive and maintainable. The main components are:

*   **`KProject`**: The central, framework-agnostic orchestrator. It receives commands, dispatches events, and coordinates the managers. It maintains the current `state_version` (an `event_id` hash) and acts as the query interface for the UI. It also provides the `save_project(filepath)` API.
*   **`QTProject` (or similar Wrapper)**: A framework-specific (e.g., Qt) wrapper around `KProject`. It actively polls `KProject` for status changes and emits native Qt Signals to notify the UI to redraw.
*   **`KStateManager`**: The "single source of truth" for the current in-memory *structural* representation (ASTs, Dependencies, Code). For data, it only stores the *names* of the data variables, updated naturally via `process_event`.
*   **`KContext`**: Stores the actual values (results) of the language, functioning as the evaluation environment. `KProject` injects loaded data directly into `KContext` using `KContext.register_object(kdata)`.
*   **`KEvaluator` / Execution Engine**: A continuous background worker that holds references to `KContext` and `KStateManager`. It computes values, mutates `KContext`, and maintains a thread-safe dictionary of the execution status of all variables.
*   **`EventManager` / Event Sourcing**: Records every state change as a sequential `KEvent`, hashed to produce unique `event_id`s.
*   **`PersistenceManager`**: Tracks event history and large data blobs. Functions entirely in memory for unsaved projects and flushes to a SQLite-backed store upon request.

## 2. State Versioning and Hashing (Multi-User Ready)

Instead of a simple integer, an `event_id` (or `state_version`) should be a **cryptographic hash** (e.g., SHA-256) of the event's contents combined with the *previous event's hash*, exactly like a blockchain or Git commit.
*   **Usage**: The `KEvaluator` tracks the hash of the state it is currently computing. If `KProject` receives a new event, it calculates the new hash. The `KEvaluator` notices `target_hash != current_hash` and aborts.

## 3. The `KEvaluator` & Future Caching (Undo/Redo Optimization)

The `KEvaluator` has **write access** to mutate `KContext` during computation. It is also the sole owner of the status state (Waiting, Processing, Ready, Error) during an evaluation pass. 

**Future Cache Integration**:
To optimize undo/redo without costly recomputations, `KContext` (or an external Cache) can be expanded to store a mapping of `(variable_name, event_hash) -> value`. During an Undo, if the target hash exists in the cache, the `KEvaluator` skips computation and instantly grabs the historical value.

## 4. UI Notification Flow (Pull Architecture)

To ensure the UI is notified efficiently, we use a Poll/Pull approach rather than pushing statuses.

### The Agnostic API (`KEvaluator` & `KProject`)
The background `KEvaluator` maintains a simple, thread-safe dictionary of the nodes' current status during its execution loop:
```python
class KVariableStatus(Enum):
    WAITING = "WAITING"
    PROCESSING = "PROCESSING"
    READY = "READY"
    ERROR = "ERROR"

# Maintained internally by KEvaluator
# self.statuses: Dict[str, KVariableStatus] = {}
```

`KProject` exposes two separate APIs, acting as pass-throughs:
1.  **Status API**: `get_all_statuses() -> Dict[str, KVariableStatus]` (Delegates to `KEvaluator.get_statuses()`)
2.  **Value API**: `get_node_value(node_name) -> KObject` (Delegates a read to `KContext`)

### The Qt Wrapper (`QTProject`) & QTimer Polling
The GUI framework uses a timer to periodically pull the status dictionary from `KProject`, compute what changed since the last tick, and emit signals.

```python
# --- Qt Specific Wrapper ---
from PyQt5.QtCore import QObject, pyqtSignal, QTimer

class QTProject(QObject):
    # Native Qt Signal to inform the UI that a node's status has changed
    nodeStatusChanged = pyqtSignal(str, object) 

    def __init__(self, kproject: KProject):
        super().__init__()
        self.kproject = kproject
        self.last_known_statuses = {}
        
        # QTimer runs purely on the Main UI thread, keeping the GUI unblocked.
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.poll_kproject)
        self.timer.start(16) # ~60fps

    def poll_kproject(self):
        current_statuses = self.kproject.get_all_statuses()
        
        # Compute the delta (Diff)
        for node_name, new_status in current_statuses.items():
            old_status = self.last_known_statuses.get(node_name)
            if old_status != new_status:
                # State changed, update UI!
                self.nodeStatusChanged.emit(node_name, new_status)
                
        self.last_known_statuses = current_statuses.copy()
```

## 5. `KStateManager` Data Structure

To eliminate fragile parallel lists, `KStateManager` uses dictionaries containing explicit `Dataclass` states. Notice `KData` itself is no longer stored here.

```python
@dataclass
class VariableState:
    code: str
    ast: AstNode
    dependencies: Set[str]
    kobject: KNodeInstance

@dataclass
class WorkflowState:
    code: str
    ast: AstNode
    dependencies: Set[str]
    kobject: KNode

class KStateManager:
    def __init__(self):
        self.variables: Dict[str, VariableState] = {}
        self.workflows: Dict[str, WorkflowState] = {}
        
        # KData is NOT stored here. AddData events update KStateManager
        # via the standard `process_event` just to register the target name 
        # in the dependency graph.
```

## 6. Persistence: In-Memory, Dirty Tracking, and Disk Serialization

Not every action immediately writes to disk. A user might open Kira, manipulate data, and close it without ever saving. 

Therefore, `PersistenceManager` must function flawlessly in memory and support explicit saving. Note: the act of saving a project is an environment action requested by the UI, **not a `KEvent`**.

### 1. In-Memory Operation and Data Caching
During normal operation (before saving is requested), the `PersistenceManager`:
*   Takes `filepath` as a constructor parameter, defaulting to `None`.
*   Keeps a raw list of all processed `KEvent`s in memory.
*   **Data Caching**: When an `AddData` event occurs, the loaded `KData` blob memory reference is cached directly inside `PersistenceManager` (e.g., `self._kdata_cache: Dict[str, KData]`).
*   This ensures that we NEVER have to re-serialize and de-serialize a newly added data blob unless we unload it from memory. `KProject` requests the `KData` object from `PersistenceManager` and places it straight into `KContext.register_object(kdata)`.

### 2. Dirty Tracking
`PersistenceManager` must track what has and hasn't been written to the backing SQLite file:
*   `self._unsaved_events: List[KEvent]`
*   `self._unsaved_data: Dict[str, KData]` (Mappings of new target names to their loaded memory instances).
When a user modifies a project that *does* have a linked file, these lists act as the queue.

### 3. Explicit File Saving
`KProject` exposes a public method for the UI to call: `kproject.save_project(filepath=None)`.

When `save_project()` is invoked:
1.  **File Management**: If `filepath` is provided, `PersistenceManager` connects to or creates a SQLite db at that path. If no path is provided and `self.filepath` is `None`, it gracefully returns or prompts the UI for a path rather than raising an error.
2.  **Event Flush**: `PersistenceManager` loops through `self._unsaved_events` and writes them into the `events` SQLite table.
3.  **Data Serialization**: It loops through `self._unsaved_data`.
    *   If it's a TABLE, it looks at the object type, serializes it (e.g., Pandas to raw binary/parquet), computes the `blob_id`, and inserts it into `KTableDataStorage` via the `(blob_id, table_type_enum, raw_binary_content)` schema.
    *   If it's simple data, it writes directly to the metadata table.
4.  **Clear Trackers**: The dirty event and dirty data lists are cleared.
5.  **Memory Preservation**: The `_kdata_cache` is kept intact so the user can continue working without re-loading the data from the newly minted SQLite file.

### 4. Loading Data from Disk
When reopening a saved `.kira` project file:
1.  `KProject` instructs `PersistenceManager` to connect to the SQLite DB and fetch the event history.
2.  `KProject` replays the history.
3.  When hitting a historical `AddData` event, `PersistenceManager` checks its memory `_kdata_cache`. Since it's a fresh boot, it misses.
4.  It checks `KTableDataStorage` in SQLite using the `blob_id` and `table_type_enum` found in the event body, executes the proper deserialization, stores it in its `_kdata_cache`, and hands it back to `KProject` to inject into `KContext`.
