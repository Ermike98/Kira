import os
import sys
import time
import argparse
import subprocess

def print_banner():
    banner = """
======================================================================
                     KIRA UNIFIED TEST SUITE RUNNER
======================================================================
"""
    print(banner)

def run_suite(name: str, cmd: list[str], env: dict) -> tuple[bool, float, str]:
    """Runs a test suite as a subprocess, timing it and capturing success/failure."""
    print(f"--> Starting suite: {name}...")
    start_time = time.time()
    
    try:
        # Run subprocess and let it print directly to stdout/stderr in real-time
        result = subprocess.run(cmd, env=env, check=False)
        duration = time.time() - start_time
        
        if result.returncode == 0:
            print(f"--> Suite '{name}' completed successfully in {duration:.2f}s.\n")
            return True, duration, "All tests passed"
        else:
            print(f"--> Suite '{name}' FAILED with exit code {result.returncode} in {duration:.2f}s.\n")
            return False, duration, f"Failed with exit code {result.returncode}"
    except Exception as e:
        duration = time.time() - start_time
        print(f"--> Suite '{name}' CRASHED: {e} in {duration:.2f}s.\n")
        return False, duration, str(e)

def main():
    print_banner()
    
    parser = argparse.ArgumentParser(description="Kira Unified Test Orchestrator")
    parser.add_argument(
        "--suite", 
        type=str, 
        default="all", 
        help="Specific test suite to run: unit, snapshots, fuzzer, or all (default: all)"
    )
    parser.add_argument(
        "--update-snapshots", 
        action="store_true", 
        help="Update Golden Master snapshot references"
    )
    parser.add_argument(
        "--fuzz-iterations", 
        type=int, 
        default=20, 
        help="Number of iterations for property fuzzer (default: 20)"
    )
    args = parser.parse_args()
    
    # 1. Setup PYTHONPATH environment
    root_dir = os.path.dirname(os.path.abspath(__file__))
    env = os.environ.copy()
    env["PYTHONPATH"] = root_dir
    
    # Define test suites to run
    suites_to_run = []
    
    selected = args.suite.lower().strip()
    
    # Setup Unit Tests
    if selected in ("all", "unit"):
        # We discover and execute all test_*.py files inside tests/unit/
        unit_dir = os.path.join(root_dir, "tests", "unit")
        if os.path.exists(unit_dir):
            unit_files = sorted([f for f in os.listdir(unit_dir) if f.startswith("test_") and f.endswith(".py")])
            for f in unit_files:
                f_path = os.path.join(unit_dir, f)
                suites_to_run.append((
                    f"Unit: {f}", 
                    [sys.executable, f_path],
                    env
                ))
    
    # Setup Snapshots
    if selected in ("all", "snapshots"):
        cmd = [sys.executable, os.path.join(root_dir, "tests", "snapshots", "run_snapshots.py")]
        if args.update_snapshots:
            cmd.append("--update")
        suites_to_run.append(("Snapshot Suite", cmd, env))
        
    # Setup Fuzzer
    if selected in ("all", "fuzzer"):
        cmd = [sys.executable, os.path.join(root_dir, "tests", "pseudo_random", "test_fuzzer.py")]
        # Note: We could customize iterations if needed by passing flags, but the fuzzer runs internally.
        suites_to_run.append(("Fuzzer Suite", cmd, env))
        
    if not suites_to_run:
        print(f"No suites found matching choice: {args.suite}")
        sys.exit(1)
        
    results = []
    global_success = True
    
    total_start = time.time()
    for name, cmd, run_env in suites_to_run:
        success, duration, info = run_suite(name, cmd, run_env)
        results.append((name, success, duration, info))
        if not success:
            global_success = False
            
    total_duration = time.time() - total_start
    
    # 2. Print elegant summary table
    print("=" * 80)
    print("                           KIRA TEST RUNNER SUMMARY")
    print("=" * 80)
    print(f"{'Suite Name':<35} | {'Status':<10} | {'Duration':<10} | {'Details':<20}")
    print("-" * 80)
    
    for name, success, duration, info in results:
        status_str = "PASSED" if success else "FAILED"
        # Truncate detail info if too long
        detail = info[:20] if len(info) > 20 else info
        print(f"{name:<35} | {status_str:<10} | {duration:.2f}s     | {detail:<20}")
        
    print("=" * 80)
    print(f"Total Execution Time: {total_duration:.2f}s")
    
    if global_success:
        print("RESULT: ALL TEST SUITES PASSED SUCCESSFULY!\n")
        sys.exit(0)
    else:
        print("RESULT: SOME TEST SUITES FAILED. PLEASE REVIEW LOGS ABOVE.\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
