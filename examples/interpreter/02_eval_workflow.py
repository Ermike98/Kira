from kira.klanguage.ktokenizer import ktokenize
from kira.klanguage.kast import kparse
from kira.core.kcontext import KContext

def main():
    print("--- Kira Interpreter Example: Workflow Evaluation ---")
    
    code = """
workflow calculate_total(price, tax) -> total:
    tax_amount = price * tax
    total = price + tax_amount
    return total
"""
    print(f"Defining workflow:\n{code}")
    
    ctx = KContext()
    tokens = [t for t in ktokenize(code) if t.token_type.name != "WHITESPACE"]
    ast_program = kparse(tokens)
    
    print("\nWorkflow parsed into AST.")
    print("To execute this:")
    print("1. Register the workflow in the context.")
    print("2. Call the workflow with input data.")
    
    # Simulation/Placeholder
    print("\nNext steps in development: Implement AstWorkflow.eval() to register KWorkflow objects.")

if __name__ == "__main__":
    main()
