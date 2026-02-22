# Kira

Kira is a data analysis software that allows users to create and manage data workflows, perform data analysis, and visualize data updates in real-time.

Kira is a gui application that runs locally on the user's machine, uses Qt for the gui, python for the backend, and sqlite for the database. 

Kira is meant to be extensible, it comes with a builtin scripting language allowing users to create custom workflows to repeat data analysis easily. It comes with a node based workflow editor allowing non programming users to create custom workflows visually. It also comes with a library of prebuilt high-performance nodes and workflows to perform all common data analysis tasks. 

Kira uses high-performance in-memory libraries to run computations, scaling gracefully as data grows. Tens of tables with millions of rows can be processed in seconds with no lagging or freezing. 

Kira uses an event-sourcing architecture to track user actions and maintain a history of changes. This allows users to undo and redo actions, compare different states of the project, and revert to previous states of the project when needed. 

Kira uses a snapshot history cache to store previous states of the project. This allows users to compare different states of the project and revert to previous states of the project without expensive reprocessing.

Kira uses a dependency graph to track dependencies between nodes and workflows. This allows to recompute only the necessary parts of the project when a change is made. 

Kira stores the state of the application in a Project object.

Project:
- KContext
- PeristanceManager:
    - SQLite Connection
- CodeManager
- ASTManager:
    - CodeManager
- VariableManager:
    - KContext
    - DependencyGraph
    - SnapshotHistoryCache
    - ASTManager

The gui updates the project through events. Events are used to notify the backend of changes to the gui.

Event:
- Author
- Timestamp
- Type
- Target
- Body (optional)

Event Types:
- AddVariable
- AddData
- AddWorkflow
- DeleteVariable
- DeleteData
- DeleteWorkflow
- UpdateWorkflow
- Store

The gui emits events when the user performs actions. The backend subscribes to these events and updates the project accordingly. 

