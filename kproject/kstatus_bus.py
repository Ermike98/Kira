from __future__ import annotations
import threading
from typing import Callable
from enum import Enum
import logging

class KVariableStatus(Enum):
    WAITING = "WAITING"
    PROCESSING = "PROCESSING"
    READY = "READY"
    ERROR = "ERROR"

class KStatusEvent(Enum):
    VARIABLE_STATUS_CHANGED = "variable_status_changed"

class KStatusBus:
    """
    Thread-safe event bus for runtime status notifications.
    Primarily used to notify the UI of variable evaluation status changes 
    from the background evaluator.
    """
    def __init__(self):
        self._subscribers: dict[KStatusEvent, list[Callable]] = {
            event: [] for event in KStatusEvent
        }
        self._variable_statuses: dict[str, KVariableStatus] = {}
        self._lock = threading.Lock()
        self._logger = logging.getLogger("kira.kevaluator")

    def subscribe(self, event_type: KStatusEvent, callback: Callable):
        """Registers a callback for a specific status event."""
        with self._lock:
            if callback not in self._subscribers[event_type]:
                self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: KStatusEvent, callback: Callable):
        """Removes a callback for a specific status event."""
        with self._lock:
            if callback in self._subscribers[event_type]:
                self._subscribers[event_type].remove(callback)

    def set_status(self, name: str, status: KVariableStatus):
        """
        Updates the internal status of a variable and dispatches the change event.
        """
        with self._lock:
            self._variable_statuses[name] = status
        
        self.dispatch(KStatusEvent.VARIABLE_STATUS_CHANGED, name, status)

    def get_status(self, name: str) -> KVariableStatus:
        """Returns the current status of a specific variable."""
        with self._lock:
            return self._variable_statuses.get(name, KVariableStatus.WAITING)

    def get_all_statuses(self) -> dict[str, KVariableStatus]:
        """Returns a copy of all current variable statuses."""
        with self._lock:
            return self._variable_statuses.copy()

    def clear_statuses(self):
        """Resets all variable statuses."""
        with self._lock:
            self._variable_statuses.clear()

    def dispatch(self, event_type: KStatusEvent, *args, **kwargs):
        """
        Dispatches an event to all subscribers.
        NOTE: Callbacks will run in the caller's thread (e.g., KEvaluator thread).
        """
        with self._lock:
            callbacks = list(self._subscribers[event_type])
        
        for callback in callbacks:
            try:
                callback(*args, **kwargs)
            except Exception as e:
                # We don't want one failing callback to crash the dispatcher
                self._logger.error(f"Error in status bus callback: {e}")
