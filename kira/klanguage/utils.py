from __future__ import annotations

from kira.klanguage.ktokenizer import KToken


def token_hash_name(token: KToken, name: str, hash_limit=100_000_000) -> str:
    token_hash = abs(hash(token)) % hash_limit
    return f"{name}_{token_hash:08d}"


def print_depth_ast(depth):
    if depth != 0:
        print("   " * (depth - 1) + "|--", end="")


def print_ast(ast, depth=0):
    from kira.klanguage.kast import AstProgram, AstLiteral, AstSymbol, AstCall, AstAssignment, AstExpressionStmt, \
        AstWorkflow

    print_depth_ast(depth)
    if isinstance(ast, AstProgram):
        print("Program:")
        for stmt in ast.statements:
            print_ast(stmt, depth=depth + 1)
    elif isinstance(ast, AstLiteral):
        print("Literal:", ast.value, ", token:", ast.token)
    elif isinstance(ast, AstSymbol):
        print("Symbol:", ast.name, ", token:", ast.token)
    elif isinstance(ast, AstCall):
        print("Call:", ast.func_name, ", token:", ast.token, ", args:")
        for arg in ast.args:
            print_ast(arg, depth=depth + 1)
    elif isinstance(ast, AstAssignment):
        print("Assignment:", ast.target, ", token:", ast.token, ", expr:")
        print_ast(ast.expression, depth=depth + 1)
    elif isinstance(ast, AstExpressionStmt):
        print("ExpressionStmt:")
        print_ast(ast.expression, depth=depth + 1)
    elif isinstance(ast, AstWorkflow):
        print("Workflow:", ast.name, ", inputs:", ast.inputs, ", outputs:", ast.outputs, ", returns:", ast.returns)
        for stmt in ast.body:
            print_ast(stmt, depth=depth + 1)
    else:
        raise ValueError(f"Unknown AST node type: {type(ast)}")
