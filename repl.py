import sys
import time
import os
import traceback
from datetime import datetime

# Ensure the current directory is in PYTHONPATH
sys.path.append(os.getcwd())

from kproject.kproject import KProject
from klogging.klogging import setup_logging, log_kobject
from kproject.kpersistence_manager import KPersistenceManager
import logging
from kproject.kevent import KEvent, KEventTypes
from kproject.kevaluator import KVariableStatus
from kira.kexpections.kgenericexception import KGenericException
from kira.kdata.kdata import KData
from kira.kdata.kliteral import KLiteral
from kira.kdata.karray import KArray
from kira.kdata.ktable import KTable
from kira.kdata.kcollection import KCollection


def display_value(name: str, obj):
    """Display a KData value in a human-readable format."""
    if not isinstance(obj, KData):
        print(f"  {name} = {obj}")
        return

    if obj.error and not obj.value:
        print(f"  {name} = ERROR: {obj.error}")
        return

    value = obj.value
    if isinstance(value, KTable):
        print(f"  {name} = Table ({value.value.shape[0]} rows × {value.value.shape[1]} cols)")
        print(value.value.to_string(index=True, max_rows=20, max_cols=10))
    elif isinstance(value, KArray):
        print(f"  {name} = Array ({len(value.value)} elements, {value.lit_type.name})")
        print(f"  {value.value.to_string(index=True, max_rows=20)}")
    elif isinstance(value, KLiteral):
        print(f"  {name} = {value.value} ({value.lit_type.name})")
    elif isinstance(value, KCollection):
        print(f"  {name} = Collection ({len(value.value)} items)")
        for item in value.value:
            print(f"    {item.name}: {item.value}")
    else:
        print(f"  {name} = {value}")

    if obj.error:
        print(f"  ⚠ Warning: {obj.error}")


def run_repl():
    # Setup logging to output to console (and optionally a file if needed)
    # You can change log_file to a path (e.g., "kira_debug.log") to output to a file
    setup_logging(level=logging.INFO, log_file=None)
    
    # Initialize KProject with an in-memory PersistenceManager
    pm = KPersistenceManager()
    project = KProject(pm)
    author = "repl_user"

    print("Kira Language REPL")
    print("Commands:")
    print("  name = expression  - Define a variable (AddVariable event)")
    print("  name               - Get variable value (get_value)")
    print("  exit / quit        - Exit REPL")
    print("-" * 20)

    while True:
        try:
            line = input("kira> ").strip()
            if not line:
                continue
            
            if line.lower() in ("exit", "quit"):
                break
            
            if "=" in line:
                # Feature 1: Define variables
                parts = line.split("=", 1)
                name = parts[0].strip()
                expr = parts[1].strip()
                
                if not name.isidentifier():
                    print(f"Error: '{name}' is not a valid variable name.")
                    continue
                
                # Create and process AddVariable event (body must be the full assignment)
                event = KEvent(
                    author=author,
                    timestamp=datetime.now(),
                    type=KEventTypes.AddVariable,
                    target=name,
                    body=line
                )
                project.process_event(event)
                
                # Wait for the variable to be READY or ERROR (REPL UX)
                start_time = time.time()
                while time.time() - start_time < 2.0: # 2 second timeout
                    status = project.get_status(name)
                    if status in (KVariableStatus.READY, KVariableStatus.ERROR):
                        break
                    time.sleep(0.05)
                
                status = project.get_status(name)
                if status == KVariableStatus.ERROR:
                    try:
                        value = project.get_value(name)
                        display_value(name, value)
                    except Exception:
                        print(f"Error: Failed to evaluate variable '{name}'.")
                elif status == KVariableStatus.READY:
                    try:
                        value = project.get_value(name)
                        display_value(name, value)
                    except Exception as e:
                        print(f"Error: {e}")
                
            else:
                # Feature 2: Get variable (single symbol)
                if line.isidentifier():
                    try:
                        value = project.get_value(line)
                        display_value(line, value)
                    except Exception as e:
                        print(f"Error: {e}")
                else:
                    # REPL constraint: expressions without = are errors
                    print("Error: Invalid command. Use 'name = expression' or a single symbol.")
                    
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except EOFError:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    run_repl()
