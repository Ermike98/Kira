# AI Developer Context & Knowledge Base for Kira

This document serves to onboard future AI assistants rapidly to the structural constraints, design decisions, and core philosophies of the Kira project's state architecture.

## Overview
Kira is a reactive data analytics GUI application (similar to Excel). Changes trigger a cascade of updates through a user-defined DSL dependency graph. State is heavily event-sourced.

## Key Subsystems
1. **`KProject` (Core Orchestrator)**
   - Acts as the framework-agnostic boundary.
   - Rejects coupling with Qt or any specific UI framework. Exposed via plain Python function calls.
   - Relies on **pull-based** UI signaling. It holds state/status, and the UI (via `QTProject`) pulls/polls at 60 FPS using `QTimer` to detect diffs and emit thread-safe signals.

2. **`KStateManager` (Structural Truth)**
   - Holds ASTs, compiled DSL code, and `KNode`/`KNodeInstance` relationships in explicit `@dataclass` mappings (e.g., `VariableState`, `WorkflowState`).
   - DOES NOT hold KData. It only holds dependency strings/names for the graph. Parallel Lists have been explicitly deprecated in favor of nested dicts/dataclasses.

3. **`KContext` (Execution Context)**
   - The evaluation engine's environment. Stores evaluated variables, functions, and heavy `KData` (DataFrames loaded from CSVs, etc.). `KProject` invokes `kcontext.register_object(kdata)`.
   - Modifiable directly by `KEvaluator`. Can potentially hook into a `ResultCache` based on event_hash to optimize undo/redo.

4. **`KEvaluator` (Background Execution Loop)**
   - A single, continuous background worker thread.
   - Uses `state_version` (SHA-256 event cryptographic hashing) to track evaluation state. If an event causes a hash mismatch, it safely preempts and aborts its current pass to restart with fresh inputs. Non-blocking to the main UI.

5. **`PersistenceManager` (Event Sourcing & SQLite Blobs)**
   - Handles the event-sourcing log (SQLite `events` table).
   - *Heavy Data Policy*: Avoids stuffing large datasets (like Pandas tables) into `KEvent.body`. Uses lightweight JSON in `KEvent.body` referencing `blob_id` and `table_type_enum`. The heavy payload is physically isolated in `KTableDataStorage` (SQLite blob table).
   - *In-Memory Caching*: Supports file-less usage. Keeps an in-memory cache of heavy KData (`_kdata_cache`), maintaining dirty tracks (`_unsaved_events`) until a user explicitly requests `save_project(filepath=...)`. Costly serializations are deferred until explicitly requested.

## Rules of Thumb for Future Agents
- DO NOT couple core logic to PyQT. Any PyQT dependencies must reside strictly inside a wrapper (like `QTProject`).
- PREFER hash-based versioning (`state_version`) over incrementing integers to support multi-user collaboration and easy state replication.
- DO NOT duplicate large sets of data across managers. KData lives in `PersistenceManager` (as un-serialized cache/SQLite Blobs) AND `KContext` (evaluation usage). Keep `KStateManager` entirely abstracted from the actual data payload.
- PREEMPT background work if state changes. Maintain single-threaded UI polling patterns via queues/dictionaries.
