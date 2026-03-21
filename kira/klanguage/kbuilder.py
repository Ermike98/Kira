from __future__ import annotations

from typing import Optional

from kira import KData, KLiteral
from kira.core.kformula import KFormula
from kira.core.kobject import KObject
from kira.core.kprogram import KProgram
from kira.core.ksymbol import KSymbol
from kira.klanguage.kast import (
    AstProgram, AstAssignment, AstExpressionStmt, AstWorkflow,
    AstExpression, AstLiteral, AstSymbol, AstCall, AstFormula
)
from kira.klanguage.utils import token_hash_name
from kira.knodes.knode_instance import KNodeInstance
from kira.knodes.kworkflow import KWorkflow


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
        return KFormula(inner_obj, inst_name)

    raise ValueError(f"Unknown AST expression type: {type(expr)}")


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

    return KWorkflow(
        ast_wf.name,
        ast_wf.inputs,
        ast_wf.outputs,
        ast_wf.returns,
        nodes=nodes
    )