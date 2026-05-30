import time
import traceback
from datetime import datetime
from typing import Optional, Dict, Any, Union

from kproject.kproject import KProject
from kproject.kpersistence_manager import KPersistenceManager
from kproject.kevent import KEvent, KEventTypes
from kproject.kevaluator import KVariableStatus
from kira.core.kobject import KObject
from kira.kdata.kdata import KData
from kira.kdata.kliteral import KLiteral
from kira.kdata.karray import KArray
from kira.kdata.ktable import KTable
from kira.kdata.kcollection import KCollection

from kira.klanguage.ktokenizer import ktokenize
from kira.klanguage.kast import kparse, AstAssignment, AstExpressionStmt, AstSymbol, AstWorkflow


def format_value(name: str, obj: Any) -> str:
    """Format a KData value or other object in a standardized, human-readable format."""
    if not isinstance(obj, KData):
        return f"  {name} = {obj}"

    if obj.error and not obj.value:
        return f"  {name} = ERROR: {obj.error}"

    lines = []
    value = obj.value
    if isinstance(value, KTable):
        lines.append(f"  {name} = Table ({value.value.shape[0]} rows × {value.value.shape[1]} cols)")
        lines.append(value.value.to_string(index=True, max_rows=20, max_cols=10))
    elif isinstance(value, KArray):
        lines.append(f"  {name} = Array ({len(value.value)} elements, {value.lit_type.name})")
        lines.append(f"  {value.value.to_string(index=True, max_rows=20)}")
    elif isinstance(value, KLiteral):
        lines.append(f"  {name} = {value.value} ({value.lit_type.name})")
    elif isinstance(value, KCollection):
        lines.append(f"  {name} = Collection ({len(value.value)} items)")
        for item in value.value:
            lines.append(f"    {item.name}: {item.value}")
    else:
        lines.append(f"  {name} = {value}")

    if obj.error:
        lines.append(f"  ⚠ Warning: {obj.error}")

    return "\n".join(lines)


class KiraREPL:
    """
    Programmatic, non-blocking backend for the Kira Domain-Specific Language REPL.
    Wraps a KProject session to enable easy script compilation, evaluation, and inspection.
    """

    def __init__(self, project: Optional[KProject] = None):
        """
        Initialize the REPL.
        If a KProject is provided, it operates on that project session (enabling GUI integration).
        Otherwise, it instantiates a clean in-memory KProject (perfect for automated testing).
        """
        if project is None:
            pm = KPersistenceManager()
            self.project = KProject(pm)
        else:
            self.project = project

        self.author = "repl_user"

    def _parse_line(self, line: str) -> dict:
        """
        Analyze a line of code to determine its action type and perform
        expression desugaring (rewriting expressions like `1 + 2` to `_ = 1 + 2`).
        """
        line_stripped = line.strip()
        if not line_stripped:
            return {"type": "empty", "target": None, "rewritten": line_stripped}

        # Handle exiting
        if line_stripped.lower() in ("exit", "quit"):
            return {"type": "command", "target": None, "rewritten": line_stripped}

        try:
            tokens = [t for t in ktokenize(line_stripped) if t.token_type.name != "WHITESPACE"]
            ast = kparse(tokens)
        except Exception as e:
            return {"type": "error", "target": None, "rewritten": line_stripped, "error": str(e)}

        if isinstance(ast, AstWorkflow):
            return {"type": "workflow", "target": ast.name, "rewritten": line_stripped}

        if isinstance(ast, AstAssignment):
            return {"type": "assignment", "target": ast.target, "rewritten": line_stripped}

        if isinstance(ast, AstExpressionStmt):
            expr = ast.expression
            if isinstance(expr, AstSymbol):
                # Simple symbol lookup query
                return {"type": "query", "target": expr.name, "rewritten": line_stripped}
            else:
                # Arbitrary expression, rewrite to assign to _
                rewritten = f"_ = {line_stripped}"
                return {"type": "expression", "target": "_", "rewritten": rewritten}

        # Fallback
        rewritten = f"_ = {line_stripped}"
        return {"type": "expression", "target": "_", "rewritten": rewritten}

    def eval_line(self, line: str, timeout: float = 2.0) -> dict:
        """
        Synchronously compile and evaluate a line of Kira code.
        Blocks until the evaluation status transitions to READY or ERROR, or hits the timeout.
        Returns a detailed results dictionary.
        """
        parsed = self._parse_line(line)
        t = parsed["type"]

        if t == "empty":
            return {
                "success": True,
                "type": "empty",
                "target": None,
                "value": None,
                "error": None,
                "output": ""
            }

        if t == "command":
            return {
                "success": True,
                "type": "command",
                "target": None,
                "value": None,
                "error": None,
                "output": "exit"
            }

        if t == "error":
            return {
                "success": False,
                "type": "error",
                "target": None,
                "value": None,
                "error": parsed["error"],
                "output": f"Syntax Error: {parsed['error']}"
            }

        if t == "query":
            name = parsed["target"]
            try:
                value = self.project.get_value(name)
                return {
                    "success": True,
                    "type": "query",
                    "target": name,
                    "value": value,
                    "error": None,
                    "output": format_value(name, value)
                }
            except Exception as e:
                return {
                    "success": False,
                    "type": "query",
                    "target": name,
                    "value": None,
                    "error": str(e),
                    "output": f"Error: {e}"
                }

        # Assignment, Expression, or Workflow
        target = parsed["target"]
        rewritten = parsed["rewritten"]
        event_type = KEventTypes.AddWorkflow if t == "workflow" else KEventTypes.AddVariable

        try:
            event = KEvent(
                author=self.author,
                timestamp=datetime.now(),
                type=event_type,
                target=target,
                body=rewritten
            )
            self.project.process_event(event)

            if t == "workflow":
                # Workflows don't have reactive evaluation statuses in the bus
                return {
                    "success": True,
                    "type": "workflow",
                    "target": target,
                    "value": None,
                    "error": None,
                    "output": f"  Workflow '{target}' defined successfully."
                }

            # Wait for variable to become READY or ERROR
            start_time = time.time()
            evaluated = False
            while time.time() - start_time < timeout:
                status = self.project.get_status(target)
                if status in (KVariableStatus.READY, KVariableStatus.ERROR):
                    evaluated = True
                    break
                time.sleep(0.02)

            if not evaluated:
                return {
                    "success": False,
                    "type": t,
                    "target": target,
                    "value": None,
                    "error": "Evaluation timeout",
                    "output": f"Error: Evaluation timed out for '{target}'."
                }

            # Get status and fetch value/error
            status = self.project.get_status(target)
            value = self.project.get_value(target)

            if status == KVariableStatus.ERROR:
                err_msg = value.error if isinstance(value, KData) else "Failed to evaluate"
                return {
                    "success": False,
                    "type": t,
                    "target": target,
                    "value": value,
                    "error": str(err_msg),
                    "output": format_value(target, value)
                }
            
            return {
                "success": True,
                "type": t,
                "target": target,
                "value": value,
                "error": None,
                "output": format_value(target, value)
            }

        except Exception as e:
            return {
                "success": False,
                "type": t,
                "target": target,
                "value": None,
                "error": str(e),
                "output": f"An unexpected error occurred during processing: {e}"
            }

    def eval_script(self, script_text: str, timeout: float = 2.0) -> list[dict]:
        """
        Evaluate a sequence of lines from a script.
        Sequentially executes each line and collects results.
        """
        results = []
        for line in script_text.splitlines():
            res = self.eval_line(line, timeout=timeout)
            if res["type"] == "empty":
                continue
            results.append(res)
            if res["type"] == "command" and res["output"] == "exit":
                break
        return results
