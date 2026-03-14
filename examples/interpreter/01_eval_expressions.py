from kira.klanguage.ktokenizer import ktokenize
from kira.klanguage.kast import kparse
from kira.core.kcontext import KContext

def main():
    print("--- Kira Interpreter Example: Expression Evaluation ---")
    
    # Note: Full evaluation requires AstNode.eval() implementation.
    # KProgram.eval(ctx) iterates through statements and calls stmt.eval(ctx).
    
    code = "x = 5 + 5 * 2"
    print(f"Code: {code}")
    
    ctx = KContext()
    tokens = [t for t in ktokenize(code) if t.token_type.name != "WHITESPACE"]
    ast_program = kparse(tokens)
    
    # In Kira, AstProgram usually contains statements. 
    # To evaluate them, we need to ensure the AST nodes have eval() methods if expected,
    # or use a dedicated Interpreter class if one exists.
    # Based on kprogram.py, it expects KObject statements. 
    # Let's check if AstNode inherits from KObject or has eval.
    
    print("\nNote: This example demonstrates the pipeline setup.")
    print("In a complete implementation, ast_program.eval(ctx) would be called.")
    
    # Example simulation if eval is available:
    try:
        # Assuming AstProgram or its nodes have eval implemented (via KObject)
        # or that they are converted to KObjects first.
        # In current codebase, AstProgram is an AstNode.
        result = ast_program.eval(ctx)
        print(f"Result: {result}")
        print(f"Context variables: {ctx.symbols}")
    except AttributeError:
        print("\n[Pending Implementation] AstNode.eval() needs to be implemented or AST needs conversion to KObjects.")

if __name__ == "__main__":
    main()
