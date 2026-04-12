from __future__ import annotations

from typing import Optional

import numpy as np
from kira import KData, KLiteral, KArray, KFunction
from kira.knodes.kfunction import kfunction
from kira.core.kformula import KFormula
from kira.core.kobject import KObject
from kira.core.kprogram import KProgram
from kira.core.ksymbol import KSymbol
from kira.klanguage.kast import (
    AstProgram, AstAssignment, AstExpressionStmt, AstWorkflow,
    AstExpression, AstLiteral, AstSymbol, AstCall, AstFormula, AstArray
)
from kira.klanguage.utils import token_hash_name
from kira.knodes.knode_instance import KNodeInstance
from kira.knodes.kworkflow import KWorkflow
from kira.ktypeinfo.any_type import KAnyTypeInfo


def kbuild_program(ast: AstProgram) -> KProgram:
    statements = []
    for stmt in ast.statements:
        if isinstance(stmt, AstAssignment):
            statements.append(kbuild_assignment(stmt))
        elif isinstance(stmt, AstExpressionStmt):
            statements.append(kbuild_expression(stmt.expression, None))
        elif isinstance(stmt, AstWorkflow):
            statements.append(kbuild_workflow(stmt))
    return KProgram(statements)


def kbuild_expression(expr: AstExpression, target_name: Optional[str]) -> KObject:
    if isinstance(expr, AstLiteral):
        data_name = target_name if target_name is not None else token_hash_name(expr.token, "lit")
        data = KData(data_name, KLiteral(expr.value))
        return data

    if isinstance(expr, AstSymbol):
        sym = KSymbol(expr.name)
        if target_name:
            # Wrap in "identity node" if a target name is provided
            return KNodeInstance(target_name, "identity", [sym])
        return sym

    if isinstance(expr, AstCall):
        # Recurse build args
        built_args = [kbuild_expression(arg, None) for arg in expr.args]

        inst_name = target_name if target_name is not None else token_hash_name(expr.token, "call")
        return KNodeInstance(inst_name, expr.func_name, built_args)

    if isinstance(expr, AstFormula):
        inner_obj = kbuild_expression(expr.expression, None)
        inst_name = target_name if target_name is not None else token_hash_name(expr.token, "formula")
        return KFormula(inst_name, inner_obj)

    if isinstance(expr, AstArray):
        built_elements = [kbuild_expression(el, None) for el in expr.elements]
        
        # Check if all elements are constant (KData)
        is_constant = all(isinstance(el, KData) for el in built_elements)
        
        inst_name = target_name if target_name is not None else token_hash_name(expr.token, "array")
        
        if is_constant:
            # All elements are literals, we can collapse into a single KData
            values = [el.value.value for el in built_elements]
            return KData(inst_name, KArray(np.array(values, dtype=object)))
        else:
            # Reactive array: create a specialized node for this arity
            node = _create_array_node(len(built_elements))
            return KNodeInstance(inst_name, node, built_elements)

    raise ValueError(f"Unknown AST expression type: {type(expr)}")


def _create_array_node(num_elements: int) -> KFunction:
    inputs = [(f"x{i}", KAnyTypeInfo()) for i in range(num_elements)]
    outputs = [("y", KAnyTypeInfo())]

    @kfunction(
        inputs=inputs,
        outputs=outputs,
        name=f"array_{num_elements}",
        use_values=True,
        use_context=False
    )
    def wrapper(*args):
        # Extract raw values from KDataValue objects
        raw_values = [v.value for v in args]
        return [KArray(raw_values)]

    return wrapper


def kbuild_assignment(stmt: AstAssignment) -> KObject:
    return kbuild_expression(stmt.expression, stmt.target)


def kbuild_workflow(ast_wf: AstWorkflow) -> KWorkflow:
    nodes = []
    for stmt in ast_wf.body:
        if isinstance(stmt, AstAssignment):
            nodes.append(kbuild_assignment(stmt))
        elif isinstance(stmt, AstExpressionStmt):
            nodes.append(kbuild_expression(stmt.expression, None))
        else:
            raise ValueError(f"Unknown AST expression type: {type(stmt)}")

    defaults = {}
    if ast_wf.defaults:
        for name, expr in ast_wf.defaults.items():
            data = kbuild_expression(expr, None)
            if not isinstance(data, KData):
                raise ValueError(f"Default value for '{name}' must be a constant expression")
            defaults[name] = data.value

    return KWorkflow(
        ast_wf.name,
        ast_wf.inputs,
        ast_wf.outputs,
        ast_wf.returns,
        nodes=nodes,
        default_inputs=defaults
    )