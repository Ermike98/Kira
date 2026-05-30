import sys
import os

# Ensure the current directory is in PYTHONPATH
sys.path.append(os.getcwd())

from repl import run_repl

if __name__ == "__main__":
    run_repl()
