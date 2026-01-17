from __future__ import annotations

from typing import Optional

from kira import KData, KLiteral
from kira.core.kobject import KObject
from kira.core.kprogram import KProgram
from kira.core.ksymbol import KSymbol
from kira.klanguage.kast import AstProgram, AstAssignment, AstExpressionStmt, AstWorkflow, AstExpression, AstLiteral, \
    AstSymbol, AstCall
from kira.klanguage.utils import token_hash_name
from kira.knodes.knode_instance import KNodeInstance
from kira.knodes.kworkflow import KWorkflow


class AstToProgramBuilder:
    def build(self, ast: AstProgram) -> KProgram:
        statements = []
        for stmt in ast.statements:
            if isinstance(stmt, AstAssignment):
                statements.append(self._build_assignment(stmt))
            elif isinstance(stmt, AstExpressionStmt):
                statements.append(self._build_expression(stmt.expression, None))
            elif isinstance(stmt, AstWorkflow):
                statements.append(self._build_workflow(stmt))
        return KProgram(statements)

    def _build_expression(self, expr: AstExpression, target_name: Optional[str]) -> KObject:
        if isinstance(expr, AstLiteral):
            data_name = target_name if target_name is not None else token_hash_name(expr.token, "lit")
            data = KData(data_name, KLiteral(expr.value))
            return data

        if isinstance(expr, AstSymbol):
            sym = KSymbol(expr.name)
            if target_name:
                return KNodeInstance(target_name, "identity", [sym])
            return sym

        if isinstance(expr, AstCall):
            # Recurse build args
            built_args = [self._build_expression(arg, None) for arg in expr.args]

            inst_name = target_name if target_name is not None else token_hash_name(expr.token, "call")

            return KNodeInstance(inst_name, expr.func_name, built_args)

        raise ValueError(f"Unknown AST expression type: {type(expr)}")

    def _build_assignment(self, stmt: AstAssignment) -> KObject:
        return self._build_expression(stmt.expression, stmt.target)

    def _build_workflow(self, ast_wf: AstWorkflow) -> KWorkflow:
        nodes = []
        for stmt in ast_wf.body:
            if isinstance(stmt, AstAssignment):
                nodes.append(self._build_assignment(stmt))
            else:
                nodes.append(self._build_expression(stmt.expression, None))

        return KWorkflow(ast_wf.name, ast_wf.inputs, ast_wf.outputs, ast_wf.returns, nodes=nodes)


def build_program(ast: AstProgram) -> KProgram:
    builder = AstToProgramBuilder()
    return builder.build(ast)
