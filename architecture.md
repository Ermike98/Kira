# Kira Architecture

Kira is designed with a clean separation of concerns, organized into three distinct layers to ensure extensibility, maintainability, and testability.

## 1. Architectural Layers

### A. DSL Layer (`kira/`)
The DSL layer is a pure Python implementation of the Kira scripting language and data processing engine. It is completely independent of the UI and the application state.

- **Responsibilities**:
    - Parsing and AST representation of Kira scripts.
    - Execution of workflows and data transformations.
    - Definition of core data structures (`KTable`, `KData`, etc.).
- **Key Components**: `Parser`, `Interpreter`, `AST`, `KNodes`, `KContext`.

### B. Application State Layer (`core/`)

The Application State (Project) layer manages the "world" of the application. It handles the lifecycle of data, variables, and workflows, and maintains the history of changes. This layer is completely independent of the UI and is a pure Python layer.

- **Responsibilities**:
    - Maintaining the `Project` state (Variables, Data Store, Workflows).
    - Managing persistence (SQLite).
    - Implementing Event Sourcing and Undo/Redo logic.
    - Coordinating the execution of DSL components.

**Project: application state**
- **KContext**: KContext stores the current state of variable and workflows. It is used to retrive the current data for visualisation and processing.
- **PeristanceManager**: Manages the persistence of the project state.
    - SQLite Connection
- **CodeManager**: Manages the code of the project.
- **ASTManager**: Manage AST and recretes them when the code is updated
- **VariableManager**: Manage variable states and updates them when needed
    - **KContext**:
    - **DependencyGraph**: The depencencie graph analyse the AST to extract dependencies between the variables in the context. This is used to know which variables need reprocessing when something is updated
    - **SnapshotHistoryCache**: The snapshot history is a point-in-time cache for the variable. 
The key identifies the variable at a specific point-in-time key="{var_name}_{timestamp_id/event_id}".
Replaying the history we can first check whether a variable is already here to avoid expensive computations.
    - **ASTManager**

The project is event driven. The gui emits events when the user performs actions. The `Project` is updated through events via the `process_event(event)` method.

**Events**: Events are used to notify the backend of changes to the gui.
- **Author**: The author of the event.
- **Timestamp**: The timestamp of the event.
- **Type**: The type of the event.
- **Target**: The target of the event.
- **Body**: The body of the event.

**Event Types**:
- **AddVariable**: Adds a variable to the project.
- **AddData**: Adds data to the project.
- **AddWorkflow**: Adds a workflow to the project.
- **DeleteVariable**: Deletes a variable from the project.
- **DeleteData**: Deletes data from the project.
- **DeleteWorkflow**: Deletes a workflow from the project.
- **UpdateWorkflow**: Updates a workflow in the project.
- **Store**: Stores the current state of the project.

**Project methods:**:
- **process_event(event)**: Processes an event and updates the project state.
- **undo()**: Undoes the last event.
- **redo()**: Redoes the last event.
- **restore(event_id or timestamp)**: Restores the project state to the given event_id or timestamp.

Project exposes the internal components through attributes. This allows the gui to access the internal components of the project.

### C. User Account Layer (`user_account/`)

This layer is responsible for managing user accounts and authentication.

### D. GUI Layer (`gui/`)

The GUI layer provides a rich, interactive interface for users to build workflows and visualize data. It is built using PySide6.

- **Responsibilities**:
    - Rendering the application state to the user.
    - Capturing user input and translating it into Events.
    - Providing specialized editors (Workflow Editor, Table Viewer).
- **Interactions**: Communicates with the State Layer exclusively through an asynchronous Event system.

The gui creates a thin wrapper around the project to handle the communication between the gui and the state. This wrapper is not aware of the internal implementation of the state, but only of the events that can be emitted. This allows the gui to be completely independent of the state. 

The gui also has:
- a **QueryAPI** to get information from the state objects. This is used to display information in the gui, such as the list of variables, the list of workflows, etc.
- a **Autocompleter** to help the user to write code.


---

## 2. Interaction Model: GUI & State

Kira uses an **Event-Souring** and **Observer** pattern to handle the communication between the UI and the Backend.

### GUI to State (Commands/Events)
Instead of the GUI directly modifying the state, it emits a structured `Event` object.
- The `Project` receives the `Event`.
- If the event is valid, the `Project` updates its state (e.g., adding to the `VariableManager`).
- This update is recorded for undo/redo and persistence.

### State to GUI (Notifications)
The State Layer communicates changes to the GUI via a Signal/Slot mechanism.
- When the state changes (e.g., a variable is added), the `Project` emits a Signal.
- The GUI layer observes these signals and updates the interface accordingly, maintaining a decoupled data flow.
