# Kira Project Testing Strategy

This document describes the unified multi-tiered testing strategy designed to ensure absolute correctness, performance, and reliability of the Kira application and its domain-specific language (DSL).

---

## 1. Architecture Overview

Kira uses a four-tier testing system to provide comprehensive coverage:

```
                  +--------------------------------+
                  |    Kira Unified Test Runner    |
                  |         (run_tests.py)         |
                  +--------------------------------+
                                  |
         +------------------------+------------------------+
         |                        |                        |
+------------------+     +------------------+     +------------------+
|    Unit Tests    |     |  Snapshot Tests  |     |  Fuzzing/Property|
|  (tests/unit/)   |     | (tests/snapshots)|     | (tests/pseudo_r) |
+------------------+     +------------------+     +------------------+
         |                        |                        |
         | Covers core API       | Golden Master          | Stress tests and
         | logic, math libs,      | REPL scripts &         | Event-Sourcing
         | parser, engine         | transcripts            | property invariants
```

1.  **Unit Tests (`tests/unit/`)**:
    *   **Focus**: Single components and specific edge cases (e.g., AST structures, specific mathematical operations, evaluator state transitions).
    *   **Execution**: Fast, isolated, standard library unittest or direct script validation.
2.  **Snapshot Tests (Golden Master) (`tests/snapshots/`)**:
    *   **Focus**: End-to-end integration and language regressions.
    *   **Concept**: Processes `.kscript` scripts via the `KiraREPL` backend and compares execution transcripts (.snapshot files) character-for-character with reference files.
3.  **Pseudo-Random / Fuzz Testing (`tests/pseudo_random/`)**:
    *   **Focus**: Stress testing the parser, compiler, error handling, and event-sourced persistence.
    *   **Tiers**:
        *   **Unquoted CSV Paths**: Proves that invalid inputs (like omitting quotes in file paths) fail gracefully rather than crashing.
        *   **Parser Perturbation**: Randomly mutates valid scripts to find compiler loops or unhandled Python crashes.
        *   **Event-Sourcing Consistency**: Generates random sequences of events (Add, Edit, Undo, Redo) and asserts that the reconstructed state perfectly matches the sequential execution state.
4.  **LLM Agent Sandbox (`tests/llm/`)**:
    *   **Focus**: Isolated area for automated agents to write, debug, and test code during pair programming without polluting git history.
    *   **Configuration**: All scratch files in this directory are ignored via Git (except `.gitignore` and `README.md`).

---

## 2. Command Line Interface

A single entrypoint `run_tests.py` orchestrates the entire suite. It handles `sys.path` dynamically, ensuring tests can be run from any folder without `ModuleNotFoundError` issues.

### Run All Tests
```bash
python run_tests.py
```

### Run a Specific Suite
You can target a specific suite using the `--suite` parameter:
*   `unit`: Executes all unit tests under `tests/unit/`.
*   `snapshots`: Executes end-to-end snapshot comparisons.
*   `fuzzer`: Executes input-perturbation, unquoted path, and property fuzzing.

```bash
python run_tests.py --suite unit
python run_tests.py --suite snapshots
python run_tests.py --suite fuzzer
```

### Update Snapshots (Golden Master References)
When adding language features or changing mathematical operators, existing snapshots will mismatched. Update them to match the new behavior:
```bash
python run_tests.py --suite snapshots --update-snapshots
```

---

## 3. Creating New Tests

### Adding a Unit Test
1.  Create a file named `test_<feature>.py` in `tests/unit/`.
2.  Add `sys.path.append(os.getcwd())` at the top of the file.
3.  Implement standard `unittest.TestCase` classes or direct assertions.

### Adding a Snapshot Script
1.  Write a script containing your language expressions in `tests/test_files/<name>.kscript`.
2.  Run the updater to generate its corresponding Golden Master reference:
    ```bash
    python run_tests.py --suite snapshots --update-snapshots
    ```
3.  Commit both the `.kscript` and the newly created reference snapshot.

---

## 4. Coding Practices & Safety Invariants

To keep tests extremely fast and stable across platforms:
1.  **ASCII Safety**: All printed outputs, assertions, and test runner tables must use clean ASCII prefixes (`[OK]`, `[FAIL]`, `[WARN]`) instead of Unicode characters to prevent Windows CP1252 terminal crashes.
2.  **Thread Cleanliness**: When testing `KProject` or `KiraREPL`, always wrap execution in `try ... finally` blocks and call `project.evaluator.stop()` or `repl.project.evaluator.stop()` in `finally`. Otherwise, background evaluator daemon threads will leak, slowing down subsequent executions.
3.  **Error Isolation**: Upstream errors must propagate cleanly via `KErrorValue` or `KException` wrappers rather than raising unhandled exceptions in math ufuncs.
