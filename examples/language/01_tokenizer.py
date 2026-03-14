from kira.klanguage.ktokenizer import ktokenize

def main():
    print("--- Kira Language Example: Tokenizer ---")

    # Example 1: Simple expression
    expr1 = "x = 42 + 10"
    print(f"\nTokenizing: '{expr1}'")
    tokens1 = ktokenize(expr1)
    for t in tokens1:
        # Skip whitespace for cleaner output if desired, but here we show all
        print(f"  {t.token_type.name:20} : '{t.sym_str}'")

    # Example 2: Workflow definition
    expr2 = """
    workflow my_flow (a) -> result:
        x = a * 2
        return x
    """
    print(f"\nTokenizing workflow...")
    tokens2 = ktokenize(expr2)
    # Filter out whitespace for a more readable summary
    filtered_tokens = [t for t in tokens2 if t.token_type.name != "WHITESPACE"]
    for t in filtered_tokens:
         print(f"  {t.token_type.name:20} : '{t.sym_str}'")

if __name__ == "__main__":
    main()
