from typing import Set
from kira.klanguage.kast import (
    AstNode, AstLiteral, AstSymbol, AstCall, AstArray, 
    AstAssignment, AstExpressionStmt, AstWorkflow, AstProgram, AstFormula
)

def find_dependencies(node: AstNode, defined_symbols: Set[str] = None) -> Set[str]:
    """
    Recursively traverses the AST to find all symbol dependencies.
    If defined_symbols is provided, only symbols in that set are considered dependencies.
    """
    dependencies: Set[str] = set()
    
    if isinstance(node, AstLiteral):
        return dependencies
        
    elif isinstance(node, AstSymbol):
        if defined_symbols is None or node.name in defined_symbols:
            dependencies.add(node.name)
            
    elif isinstance(node, AstCall):
        for arg in node.args:
            dependencies.update(find_dependencies(arg, defined_symbols))
            
    elif isinstance(node, AstArray):
        for elem in node.elements:
            dependencies.update(find_dependencies(elem, defined_symbols))
    
    elif isinstance(node, AstFormula):
        # Formulas encapsulate local variables but still depend on defined global variables
        dependencies.update(find_dependencies(node.expression, defined_symbols))

    elif isinstance(node, AstAssignment):
        dependencies.update(find_dependencies(node.expression, defined_symbols))
        
    elif isinstance(node, AstExpressionStmt):
        dependencies.update(find_dependencies(node.expression, defined_symbols))
        
    elif isinstance(node, AstWorkflow):
        # Collect all symbols used in the workflow body
        body_deps = set()
        for stmt in node.body:
            body_deps.update(find_dependencies(stmt, defined_symbols))
        # Dependencies are symbols used but NOT defined in the input list
        dependencies = body_deps - set(node.inputs)
        
    elif isinstance(node, AstProgram):
        for stmt in node.statements:
            dependencies.update(find_dependencies(stmt, defined_symbols))
            
    return dependencies
