import os
import sys
import argparse
import difflib

# Ensure the root is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from repl.repl_backend import KiraREPL

def run_script_and_get_transcript(script_path: str) -> str:
    """Runs a kscript and returns a clean REPL-style transcript of inputs and outputs."""
    repl = KiraREPL()
    transcript = []
    
    with open(script_path, "r", encoding="utf-8") as f:
        code = f.read()
        
    for line in code.splitlines():
        trimmed = line.strip()
        transcript.append(f"kira> {line}")
        
        # Don't evaluate empty lines or comment-only lines
        if not trimmed or trimmed.startswith("#"):
            continue
            
        res = repl.eval_line(line, timeout=5.0)
        if res.get("output"):
            # Add output, indented slightly for readability
            output = res["output"]
            transcript.append(output)
            
    # Return formatted string with ending newline
    return "\n".join(transcript) + "\n"

def main():
    # Force UTF-8 for stdout if possible
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="Kira Snapshot Testing Engine")
    parser.add_argument("--update", action="store_true", help="Update snapshot references")
    args, unknown = parser.parse_known_args()
    
    test_files_dir = os.path.join(os.path.dirname(__file__), "..", "test_files")
    references_dir = os.path.join(os.path.dirname(__file__), "references")
    
    os.makedirs(references_dir, exist_ok=True)
    
    # Get all .kscript files
    kscripts = [f for f in os.listdir(test_files_dir) if f.endswith(".kscript")]
    if not kscripts:
        print("No .kscript files found in tests/test_files/.")
        sys.exit(0)
        
    failures = 0
    for script_name in sorted(kscripts):
        base_name = os.path.splitext(script_name)[0]
        script_path = os.path.join(test_files_dir, script_name)
        ref_path = os.path.join(references_dir, f"{base_name}.snapshot")
        
        print(f"Running snapshot for {script_name}...")
        try:
            transcript = run_script_and_get_transcript(script_path)
        except Exception as e:
            print(f"[ERROR] Failed to execute {script_name}: {e}")
            import traceback
            traceback.print_exc()
            failures += 1
            continue
            
        if args.update:
            with open(ref_path, "w", encoding="utf-8") as f:
                f.write(transcript)
            print(f"[OK] Updated reference for {script_name}")
        else:
            if not os.path.exists(ref_path):
                print(f"[ERROR] Reference file not found: {ref_path}. Please run with --update to generate it first.")
                failures += 1
                continue
                
            with open(ref_path, "r", encoding="utf-8") as f:
                expected = f.read()
                
            if transcript != expected:
                print(f"[FAIL] Snapshot MISMATCH for {script_name}!")
                # Generate visual diff
                diff = difflib.unified_diff(
                    expected.splitlines(keepends=True),
                    transcript.splitlines(keepends=True),
                    fromfile="Expected Snapshot",
                    tofile="Actual Transcript"
                )
                print("".join(diff))
                failures += 1
            else:
                print(f"[OK] {script_name} passed")
                
    if failures > 0:
        print(f"\nSnapshot testing failed with {failures} mismatch(es)/error(s).")
        sys.exit(1)
    else:
        print("\nAll snapshots passed successfully!")
        sys.exit(0)

if __name__ == "__main__":
    main()
