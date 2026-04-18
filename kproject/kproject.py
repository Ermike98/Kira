from __future__ import annotations
import hashlib
from typing import Dict, List, Optional, TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from kproject.kevent import KEvent
    from kproject.kpersistence_manager import KPersistenceManager
    from kproject.kevaluator import KVariableStatus

from kira.core.kcontext import KContext
from kproject.kstate_manager import KStateManager
from kproject.kevaluator import KEvaluator
from kproject.kevent import KEventTypes
from kira.core.kobject import KObject
from library import load_libraries

logger = logging.getLogger("kira.kproject")

class KProject:
    """
    Central orchestrator for the Kira project.
    Manages the lifecycle of managers and coordinates event-driven state updates.
    """
    def __init__(self, persistence_manager: KPersistenceManager):
        self.persistence_manager = persistence_manager
        
        # Initialize Core Managers
        self.context = KContext()
        load_libraries(self.context)
        self.state_manager = KStateManager()
        self.evaluator = KEvaluator(self.context, self.state_manager)
        
        # State Versioning and History
        self._state_version: str = ""
        self._history: List[KEvent] = self.persistence_manager.get_all_events()
        self._current_index: int = 0  # Number of events applied
        
        # Initial Load
        for event in self._history:
            self._apply_event_internal(event)

    def _reconstruct_state(self, to_index: Optional[int] = None):
        """
        Full state reconstruction: Clears current state and replays events up to to_index.
        """
        if to_index is None:
            to_index = len(self._history)
            
        # Reset State
        self.evaluator.stop()
        self.context = KContext()
        load_libraries(self.context)
        self.state_manager = KStateManager()
        self.evaluator = KEvaluator(self.context, self.state_manager)
        
        self._state_version = ""
        self._current_index = 0
        
        for i in range(to_index):
            self._apply_event_internal(self._history[i])

    def _apply_event_internal(self, event: KEvent):
        """Applies an event to the internal managers without affecting persistence."""

        # 1. State Structures
        self.state_manager.process_event(event)

        # 2. Context Data Registration
        if event.type == KEventTypes.AddData:
            data = self.persistence_manager.get_data(event.target)
            if data:
                self.context.register_object(data)
        
        # 3. Evaluation
        self.evaluator.process_event(event)
        
        # 4. Hash chaining
        self._update_state_hash(event)
        self._current_index += 1

    def process_event(self, event: KEvent):
        """
        Main entry point for all state-changing actions.
        Orchestrates persistence, structure updates, and background evaluation.
        """
        logger.info(f"Processing event: {event.type} for target: {event.target}")
        
        # Handle Divergence: If we are not at the end of history, truncate the branch
        if self._current_index < len(self._history):
            # The first "future" event is at self._current_index
            future_event = self._history[self._current_index]
            self.persistence_manager.truncate_history(future_event.event_id)
            self._history = self._history[:self._current_index]

        # 1. Add to history
        self._history.append(event)
        
        # 2. Persistence
        self.persistence_manager.process_event(event)
        
        # 3. Application
        self._apply_event_internal(event)

    def _update_state_hash(self, event: KEvent):
        """Generates a new state version hash by chaining with the previous hash."""
        hasher = hashlib.sha256()
        hasher.update(self._state_version.encode())
        hasher.update(event.event_id.encode())
        self._state_version = hasher.hexdigest()

    @property
    def state_version(self) -> str:
        return self._state_version

    # UI Pass-through APIs
    def get_all_statuses(self) -> Dict[str, KVariableStatus]:
        return self.evaluator.get_all_statuses()

    def get_status(self, name: str) -> KVariableStatus:
        return self.evaluator.get_status(name)

    def get_value(self, name: str) -> KObject:
        return self.context.get_object(name)

    def get_data_names(self) -> List[str]:
        """Returns the list of all registered data names."""
        return sorted(self.state_manager.data_names)

    def get_context_state(self) -> dict:
        """Returns the full state of the KContext."""
        return self.context.get_context_state()

    # Undo/Redo/Restore logic
    def undo(self):
        """Moves back one event in history."""
        if self._current_index > 0:
            self._reconstruct_state(self._current_index - 1)

    def redo(self):
        """Moves forward one event in history if available."""
        if self._current_index < len(self._history):
            event = self._history[self._current_index]
            self._apply_event_internal(event)

    def restore(self, event_id: str):
        """Jumps to a specific historical point by event_id (hash)."""
        # Find the index of the event with the given hash
        target_idx = None
        for i, evt in enumerate(self._history):
            if evt.event_id == event_id:
                target_idx = i + 1
                break
        
        if target_idx is not None:
            self._reconstruct_state(target_idx)
