import os
import sys
import random
import time
from datetime import datetime

# Ensure root directory is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from repl.repl_backend import KiraREPL
from kproject.kproject import KProject
from kproject.kpersistence_manager import KPersistenceManager
from kproject.kevent import KEvent, KEventTypes
from kproject.kevaluator import KVariableStatus

def wait_for_evaluator_to_idle(project: KProject, timeout: float = 3.0, context_name: str = "") -> None:
    """Blocks until all variables in the evaluation queue have reached READY or ERROR."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        all_statuses = project.get_all_statuses()
        busy = False
        for name, status in all_statuses.items():
            if status in (KVariableStatus.WAITING, KVariableStatus.PROCESSING):
                busy = True
                break
        if not busy:
            return
        time.sleep(0.01)
    
    # If we hit the timeout, print a diagnostic warning
    all_statuses = project.get_all_statuses()
    print(f"  [WARN] wait_for_evaluator_to_idle timed out ({timeout}s) in {context_name}. Statuses: {all_statuses}")

# Helper: Perturb code string
def perturb_code(code: str) -> str:
    """Randomly perturbs the code string to generate syntax variations and errors."""
    if not code:
        return code
        
    mutation_type = random.choice([
        "replace_char", "insert_char", "delete_char", "double_op", "swap_words"
    ])
    
    chars = list(code)
    n = len(chars)
    
    if mutation_type == "replace_char" and n > 0:
        idx = random.randint(0, n - 1)
        chars[idx] = random.choice(["+", "-", "*", "/", "(", ")", "[", "]", ",", ".", "\"", "'", "a", "1"])
    elif mutation_type == "insert_char":
        idx = random.randint(0, n)
        chars.insert(idx, random.choice(["+", "-", "*", "/", "(", ")", "[", "]", ",", ".", "\"", "'"]))
    elif mutation_type == "delete_char" and n > 0:
        idx = random.randint(0, n - 1)
        chars.pop(idx)
    elif mutation_type == "double_op":
        ops = ["+", "-", "*", "/", "=", "|>"]
        op = random.choice(ops)
        code_str = "".join(chars)
        if op in code_str:
            return code_str.replace(op, op + op, 1)
    elif mutation_type == "swap_words":
        words = code.split()
        if len(words) > 1:
            idx = random.randint(0, len(words) - 2)
            words[idx], words[idx+1] = words[idx+1], words[idx]
            return " ".join(words)
            
    return "".join(chars)

def test_kscript_perturbation(iterations_per_file: int = 5) -> None:
    """
    Fuzzes the parser and compiler by reading valid sample scripts and applying random perturbations.
    Verifies that the parser and compiler never crash with unhandled Python exceptions.
    """
    print(f"Running KScript Perturbation Fuzzing ({iterations_per_file} iterations/file)...")
    test_files_dir = os.path.join(os.path.dirname(__file__), "..", "test_files")
    kscripts = [f for f in os.listdir(test_files_dir) if f.endswith(".kscript")]
    
    random.seed(42)  # Set seed for reproducible fuzz runs
    
    for script_name in kscripts:
        script_path = os.path.join(test_files_dir, script_name)
        with open(script_path, "r", encoding="utf-8") as f:
            original_code = f.read()
            
        print(f"  Fuzzing script: {script_name}...")
        for i in range(iterations_per_file):
            perturbed = perturb_code(original_code)
            print(f"    [{script_name}] Iteration {i+1}: perturbing...")
            first_line = perturbed.splitlines()[0] if perturbed.strip() else ""
            print(f"      Code snippet: {first_line[:50]}...")
            
            start_t = time.time()
            repl = KiraREPL()
            try:
                repl.eval_script(perturbed, timeout=0.1)
            except Exception as e:
                print(f"\n[FAIL] CRASH DETECTED on iteration {i} of {script_name}!")
                print(f"Perturbed code:\n{perturbed}\n")
                raise e
            finally:
                repl.project.evaluator.stop()
            print(f"      Completed in {time.time() - start_t:.3f}s")
            
    print("[OK] KScript perturbation fuzzing completed successfully with zero crashes.")

def test_state_reconstruction_consistency(iterations: int = 3) -> None:
    """
    Fuzzes the Event-Sourcing state reconstruction logic.
    Randomly generates sequences of AddVariable, EditVariable, Undo, and Redo events.
    Verifies that the sequential state matches the reconstructed state from the event log perfectly.
    """
    print(f"Running Event-Sourcing Reconstruction Consistency Property Test ({iterations} iterations)...")
    random.seed(1337)
    
    for run in range(iterations):
        print(f"  Starting Run {run+1} of {iterations}...")
        pm = KPersistenceManager()
        project = KProject(pm)
        recon_project = None
        
        try:
            vars_in_play = {}
            
            num_actions = random.randint(5, 10)
            for step in range(num_actions):
                action = random.choice(["add", "edit", "undo", "redo"])
                print(f"    Step {step+1}: action '{action}'")
                
                if action == "add" or (action == "edit" and not vars_in_play):
                    var_name = f"v_{random.randint(1, 10)}"
                    val = random.randint(-100, 100)
                    expr = f"{var_name} = {val}"
                    print(f"      Dispatch AddVariable: {expr}")
                    
                    event = KEvent(
                        author="fuzzer",
                        timestamp=datetime.now(),
                        type=KEventTypes.AddVariable,
                        target=var_name,
                        body=expr
                    )
                    project.process_event(event)
                    vars_in_play[var_name] = val
                    
                elif action == "edit" and vars_in_play:
                    var_name = random.choice(list(vars_in_play.keys()))
                    other_var = random.choice(list(vars_in_play.keys()))
                    val = random.randint(-100, 100)
                    
                    if var_name != other_var and random.random() > 0.5:
                        expr = f"{var_name} = {other_var} + {val}"
                    else:
                        expr = f"{var_name} = {val}"
                    print(f"      Dispatch EditVariable: {expr}")
                        
                    event = KEvent(
                        author="fuzzer",
                        timestamp=datetime.now(),
                        type=KEventTypes.AddVariable,
                        target=var_name,
                        body=expr
                    )
                    project.process_event(event)
                    
                elif action == "undo":
                    print("      Dispatch Undo")
                    project.undo()
                    
                elif action == "redo":
                    print("      Dispatch Redo")
                    project.redo()
                    
            wait_for_evaluator_to_idle(project, context_name=f"Run {run+1} pre-reconstruct")
            
            # Capture current sequential state
            seq_state = {}
            for name in project.state_manager.data_names:
                status = project.get_status(name)
                val = None
                try:
                    val = project.get_value(name)
                except Exception:
                    pass
                seq_state[name] = (status, val)
                
            # Reconstruct
            print("    Reconstructing state from event log...")
            events = pm.get_all_events()
            
            fresh_pm = KPersistenceManager()
            for evt in events:
                fresh_pm.process_event(evt)
                
            recon_project = KProject(fresh_pm)
            wait_for_evaluator_to_idle(recon_project, context_name=f"Run {run+1} post-reconstruct")
            
            # Compare states
            recon_names = recon_project.state_manager.data_names
            assert set(seq_state.keys()) == set(recon_names)
                
            for name in seq_state:
                orig_status, orig_val = seq_state[name]
                recon_status = recon_project.get_status(name)
                
                assert orig_status == recon_status
                    
                if orig_status == KVariableStatus.READY:
                    recon_val = recon_project.get_value(name)
                    orig_raw = orig_val.value.value if hasattr(orig_val, "value") and hasattr(orig_val.value, "value") else None
                    recon_raw = recon_val.value.value if hasattr(recon_val, "value") and hasattr(recon_val.value, "value") else None
                    assert orig_raw == recon_raw
        finally:
            project.evaluator.stop()
            if recon_project:
                recon_project.evaluator.stop()
        print(f"  Run {run+1} completed successfully.")
                    
    print(f"[OK] Event-Sourcing Reconstruction Consistency Property Test passed successfully.")

if __name__ == "__main__":
    try:
        test_kscript_perturbation(iterations_per_file=5)
        print()
        test_state_reconstruction_consistency(iterations=3)
        print("\nAll pseudo-random and fuzz tests passed successfully!")
    except Exception as e:
        print(f"\n[FAIL] Fuzzer test run failed: {e}")
        import traceback
        print(traceback.format_exc())
        sys.exit(1)
