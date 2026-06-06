#!/usr/bin/env python3
"""
Kira Snapshot Updater Utility
This script runs the snapshot tests in update mode, regenerating the Golden Master
snapshot references.
"""

import os
import sys
import subprocess

def main():
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Path to the run_snapshots.py script in the same directory
    updater_script = os.path.join(script_dir, "run_snapshots.py")
    
    # Get the project root directory (two levels up from tests/snapshots/)
    root_dir = os.path.abspath(os.path.join(script_dir, "..", ".."))
    
    # Verify the updater script exists
    if not os.path.exists(updater_script):
        print(f"Error: Could not find snapshot runner at {updater_script}")
        if os.name == 'nt':
            input("\nPress Enter to exit...")
        sys.exit(1)
        
    # Set up environment variables
    env = os.environ.copy()
    env["PYTHONPATH"] = root_dir
    
    print("=" * 60)
    print("               KIRA SNAPSHOT UPDATER")
    print("=" * 60)
    print("Updating Golden Master snapshots...")
    print(f"Running: {updater_script} --update\n")
    
    # Command to run the snapshot script with --update flag
    cmd = [sys.executable, updater_script, "--update"]
    
    try:
        # Run subprocess and let output flow to stdout/stderr
        result = subprocess.run(cmd, env=env)
        
        if result.returncode == 0:
            print("\n" + "=" * 60)
            print("SUCCESS: All snapshots have been updated successfully!")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print(f"FAILED: Snapshot updater exited with code {result.returncode}")
            print("=" * 60)
            
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"CRASHED: Failed to run the updater: {e}")
        print("=" * 60)
        
    # If run on Windows (likely via double-click), keep console open
    if os.name == 'nt':
        input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
