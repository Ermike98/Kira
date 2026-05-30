import sys
import traceback
from repl.repl_backend import KiraREPL
from klogging.klogging import setup_logging
import logging

def run_repl():
    # Setup logging to console
    setup_logging(level=logging.WARNING, log_file=None)
    
    # Initialize programmatic REPL backend
    repl = KiraREPL()

    print("Kira Language REPL")
    print("Commands:")
    print("  name = expression  - Define a variable (AddVariable event)")
    print("  expression         - Evaluate any arbitrary expression")
    print("  name               - Get variable value (get_value)")
    print("  exit / quit        - Exit REPL")
    print("-" * 20)

    while True:
        try:
            line = input("kira> ").strip()
            if not line:
                continue
            
            # Evaluate using programmatic backend
            result = repl.eval_line(line)
            
            if result["type"] == "command" and result["output"] == "exit":
                break
                
            if result["output"]:
                print(result["output"])
                
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
