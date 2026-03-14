from kira.klanguage.ktokenizer import ktokenize
from kira.klanguage.kast import kparse

def print_ast(node, indent=0):
    pref = "  " * indent
    print(f"{pref}{node.__class__.__name__}")
    if hasattr(node, 'statements'):
        for s in node.statements:
            print_ast(s, indent + 1)
    elif hasattr(node, 'expression'):
        print_ast(node.expression, indent + 1)
    elif hasattr(node, 'body'):
        for s in node.body:
            print_ast(s, indent + 1)
    elif hasattr(node, 'value'):
        print(f"{pref}  Value: {node.value}")
    elif hasattr(node, 'name'):
        print(f"{pref}  Name: {node.name}")
    elif hasattr(node, 'target'):
        print(f"{pref}  Target: {node.target}")
        print_ast(node.expression, indent + 1)

def main():
    print("--- Kira Language Example: Parser ---")

    code = "x = 10 + 20 * 2"
    print(f"Parsing: {code}")
    
    tokens = ktokenize(code)
    # Filter WHITESPACE if the parser expects it, though kparse usually handles tokens as they come
    # Looking at kparse, it doesn't explicitly skip whitespace, let's see if it's needed.
    # Actually, kparse in kast.py uses stream.current which might be WHITESPACE.
    # Most hand-written parsers for Kira skip whitespace during tokenization or in the stream.
    tokens = [t for t in tokens if t.token_type.name != "WHITESPACE"]
    
    ast = kparse(tokens)
    print("\nGenerated AST Structure:")
    print_ast(ast)

if __name__ == "__main__":
    main()
