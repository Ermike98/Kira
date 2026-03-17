from __future__ import annotations
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, TYPE_CHECKING

from PySide6.QtCore import QObject, Signal, QTimer

from kproject.kproject import KProject
from kproject.kevent import KEvent, KEventTypes

if TYPE_CHECKING:
    from kproject.kpersistence_manager import KPersistenceManager
    from kproject.kevaluator import KVariableStatus
    from kira.core.kobject import KObject

@dataclass
class UserInfo:
    """Stores user identity information for event attribution."""
    username: str = "Anonymous"
    email: str = ""
    display_name: str = ""

@dataclass
class UserConfig:
    """Stores user-specific GUI and behavior preferences."""
    theme: str = "light"
    auto_save: bool = True
    polling_interval_ms: int = 100

@dataclass
class ProjectConfig:
    """Stores project-specific settings and metadata."""
    name: str = "Untitled Project"
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)

class QTProject(QObject):
    """
    Reactive wrapper around KProject for PySide6 applications.
    Dispatches events through KProject and notifies UI of state changes.
    """
    
    # Signals for UI reactivity
    status_changed = Signal(dict)  # Dict[str, KVariableStatus]
    data_added = Signal(str)       # target name
    history_updated = Signal()     # Triggered on Undo/Redo/New Event
    error_occurred = Signal(str)   # General error message
    
    def __init__(
        self, 
        kproject: KProject, 
        user_info: Optional[UserInfo] = None,
        user_config: Optional[UserConfig] = None,
        parent: Optional[QObject] = None
    ):
        super().__init__(parent)
        self.kproject = kproject
        self.user_info = user_info or UserInfo()
        self.user_config = user_config or UserConfig()
        
        # Internal state tracking for polling
        self._prev_statuses: Dict[str, Any] = {}
        
        # Polling timer for reactive updates
        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._poll_status)
        self._poll_timer.start(self.user_config.polling_interval_ms)

    def process_event(self, type: KEventTypes, target: str, body: str = ""):
        """
        Creates and dispatches a KEvent through the core KProject.
        """
        try:
            event = KEvent(
                author=f"{self.user_info.username} <{self.user_info.email}>".strip(),
                timestamp=datetime.now(),
                type=type,
                target=target,
                body=body
            )
            self.kproject.process_event(event)
            self.history_updated.emit()
            
            if type == KEventTypes.AddData:
                self.data_added.emit(target)
                
        except Exception as e:
            logging.error(f"Failed to process event: {e}")
            self.error_occurred.emit(str(e))

    def undo(self):
        """Reverts the last action in the core kproject."""
        self.kproject.undo()
        self.history_updated.emit()

    def redo(self):
        """Replays the next action from the history log."""
        self.kproject.redo()
        self.history_updated.emit()

    def restore(self, event_id: str):
        """Jumps to a specific historical point."""
        self.kproject.restore(event_id)
        self.history_updated.emit()

    def get_value(self, name: str) -> Optional[KObject]:
        """Thread-safe retrieval of a variable value from context."""
        return self.kproject.get_value(name)

    def _poll_status(self):
        """
        Polls the background evaluator for status changes.
        Emits status_changed if anything has changed since the last poll.
        """
        try:
            current_statuses = self.kproject.get_all_statuses()
            
            # Simple change detection
            if current_statuses != self._prev_statuses:
                self._prev_statuses = current_statuses.copy()
                self.status_changed.emit(current_statuses)
                
        except Exception as e:
            # We don't want to crash the timer/UI on a polling error
            logging.warning(f"Polling error: {e}")

    @property
    def history(self) -> List[KEvent]:
        """Returns the full event log from the core project."""
        return self.kproject._history # Accessing internal for now, might need public API

    @property
    def current_index(self) -> int:
        """Current pointer position in the history log."""
        return self.kproject._current_index

    @property
    def state_version(self) -> str:
        """Returns the current state version hash from the core project."""
        return self.kproject.state_version
