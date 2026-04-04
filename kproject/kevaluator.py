from __future__ import annotations
from enum import Enum
import threading
import time
import logging
from klogging.klogging import log_kobject
from typing import Dict, Any, List, Set, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from kira.core.kcontext import KContext
    from kproject.kstate_manager import KStateManager

from kproject.kmanager import KManager
from kproject.kevent import KEvent

class KVariableStatus(Enum):
    WAITING = "WAITING"
    PROCESSING = "PROCESSING"
    READY = "READY"
    ERROR = "ERROR"

class KEvaluator(KManager):
    """
    Background worker responsible for executing variable evaluations based on events.
    Maintains a work queue of variables that need re-evaluation.
    """
    def __init__(self, context: KContext, state_manager: KStateManager):
        self.context = context
        self.state_manager = state_manager
        
        self._statuses: Dict[str, KVariableStatus] = {}
        self._status_lock = threading.Lock()
        
        self._evaluation_queue: List[str] = []
        self._queue_lock = threading.Lock()
        
        self._stop_event = threading.Event()
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True, name="KEvaluatorWorker")
        self._worker_thread.start()

        self._logger = logging.getLogger("kira.kevaluator")

    def process_event(self, event: KEvent):
        """
        Handles an incoming event by identifying dependent variables, 
        updating their status to WAITING, and adding them to the evaluation queue.
        """
        
        # Add the target itself first if it's a variable
        affected = []
        if event.target in self.state_manager.variables:
            affected.append(event.target)
        
        # Identify dependent variables in BFS order
        affected_dependents = self._get_all_dependents(event.target)
        affected.extend(affected_dependents)
        

        # 3. Update statuses and queue
        with self._status_lock, self._queue_lock:
            for var_name in affected:
                # Set status to WAITING
                self._statuses[var_name] = KVariableStatus.WAITING
                
                # Remove if already in queue (to re-insert at the end)
                if var_name in self._evaluation_queue:
                    self._evaluation_queue.remove(var_name)
                
                # Re-insert at the end
                self._evaluation_queue.append(var_name)

    def get_all_statuses(self) -> Dict[str, KVariableStatus]:
        """Returns a copy of the current status of all variables."""
        with self._status_lock:
            return self._statuses.copy()

    def get_status(self, name: str) -> KVariableStatus:
        """Returns the status of a specific variable."""
        with self._status_lock:
            return self._statuses.get(name, KVariableStatus.WAITING)

    # !DEPRECATED: Use context.get_object(name) instead
    def get_value(self, name: str) -> Any:
        """Gets the value associated with the object name from KContext."""
        try:
            return self.context.get_object(name)
        except Exception:
            return None

    def stop(self):
        """Stops the background worker thread."""
        self._stop_event.set()
        if self._worker_thread.is_alive():
            self._worker_thread.join()

    def _get_all_dependents(self, origin: str) -> list[str]:
        """
        BFS to find all symbols (variables or workflows) that depend on 'origin', 
        directly or indirectly. Returns them in BFS traversal order.
        """
        affected = []
        queue = [origin]
        visited = {origin}

        while queue:
            current = queue.pop(0)

            # Check variables
            for var_name, state in self.state_manager.variables.items():
                if current in state.dependencies and var_name not in visited:
                    visited.add(var_name)
                    affected.append(var_name)
                    queue.append(var_name)
            
            # Check workflows
            for wf_name, state in self.state_manager.workflows.items():
                if current in state.dependencies and wf_name not in visited:
                    visited.add(wf_name)
                    affected.append(wf_name)
                    queue.append(wf_name)
                    
        return affected

    def _worker_loop(self):
        while not self._stop_event.is_set():
            var_to_eval = None
            with self._queue_lock:
                if self._evaluation_queue:
                    var_to_eval = self._evaluation_queue.pop(0)
            
            if var_to_eval:
                self._evaluate_variable(var_to_eval)
            else:
                time.sleep(0.05)

    def _evaluate_variable(self, name: str):
        # Determine if it's a variable or workflow
        is_var = name in self.state_manager.variables
        is_wf = name in self.state_manager.workflows
        
        if not (is_var or is_wf):
            return

        self._logger.info(f"Processing evaluation for: {name}")

        with self._status_lock:
            self._statuses[name] = KVariableStatus.PROCESSING
        
        status = KVariableStatus.READY
        result = None

        if is_var:
            state = self.state_manager.variables[name]
            result = state.kobject.eval(self.context)
            if not result:
                status = KVariableStatus.ERROR
        elif is_wf:
            state = self.state_manager.workflows[name]
            result = state.kobject.eval(self.context)

        self._logger.info(f"Completed evaluation for: {name}")
        if result is not None:
            log_kobject(result)

        with self._status_lock:
            self._statuses[name] = status

