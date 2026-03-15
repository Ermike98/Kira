from typing import Set
from kira.klanguage.kast import (
    AstNode, AstLiteral, AstSymbol, AstCall, AstArray, 
    AstAssignment, AstExpressionStmt, AstWorkflow, AstProgram
)

def find_dependencies(node: AstNode) -> Set[str]:
    """
    Recursively traverses the AST to find all symbol dependencies.
    """
    dependencies: Set[str] = set()
    
    if isinstance(node, AstLiteral):
        return dependencies
        
    elif isinstance(node, AstSymbol):
        dependencies.add(node.name)
        
    elif isinstance(node, AstCall):
        for arg in node.args:
            dependencies.update(find_dependencies(arg))
            
    elif isinstance(node, AstArray):
        for elem in node.elements:
            dependencies.update(find_dependencies(elem))
            
    elif isinstance(node, AstAssignment):
        dependencies.update(find_dependencies(node.expression))
        
    elif isinstance(node, AstExpressionStmt):
        dependencies.update(find_dependencies(node.expression))
        
    elif isinstance(node, AstWorkflow):
        # Collect all symbols used in the workflow body
        body_deps = set()
        for stmt in node.body:
            body_deps.update(find_dependencies(stmt))
        # Dependencies are symbols used but NOT defined in the input list
        dependencies = body_deps - set(node.inputs)
        
    elif isinstance(node, AstProgram):
        for stmt in node.statements:
            dependencies.update(find_dependencies(stmt))
            
    return dependencies
