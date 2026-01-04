from __future__ import annotations
from dataclasses import dataclass
from abc import ABC
from typing import Optional, Union

from kira.klanguage.ktokenizer import KToken, KTokenType


# --- AST Node Definitions ---

@dataclass
class AstNode(ABC):
    pass


@dataclass
class AstExpression(AstNode):
    pass


@dataclass
class AstLiteral(AstExpression):
    value: Union[str, int, float, bool]
    token: KToken


@dataclass
class AstSymbol(AstExpression):
    name: str
    token: KToken


@dataclass
class AstCall(AstExpression):
    func_name: str
    args: list[AstExpression]
    token: KToken


@dataclass
class AstStatement(AstNode):
    pass


@dataclass
class AstAssignment(AstStatement):
    target: str
    expression: AstExpression
    token: KToken


@dataclass
class AstExpressionStmt(AstStatement):
    expression: AstExpression


@dataclass
class AstWorkflow(AstNode):
    name: str
    inputs: list[str]
    outputs: list[str]
    returns: list[str]
    body: list[AstStatement]
    token: KToken


@dataclass
class AstProgram(AstNode):
    statements: list[Union[AstStatement, AstWorkflow]]


# --- Utilities ---

class KTokenStream:
    def __init__(self, tokens: list[KToken]):
        self._tokens = tokens
        self._pos = 0

    @property
    def current(self) -> Optional[KToken]:
        if self._pos < len(self._tokens):
            return self._tokens[self._pos]
        return None

    @property
    def position(self):
        return self._pos

    def advance(self) -> Optional[KToken]:
        if self._pos < len(self._tokens):
            t = self._tokens[self._pos]
            self._pos += 1
            return t
        return None

    def match(self, token_type: KTokenType) -> bool:
        if self.current and self.current.token_type == token_type:
            self.advance()
            return True
        return False

    def expect(self, token_type: KTokenType, error_msg: str) -> KToken:
        if self.current and self.current.token_type == token_type:
            return self.advance()
        raise SyntaxError(f"{error_msg}. Got {self.current}")


# --- Parser (Returns AST) ---

def kparse(tokens: list[KToken]) -> AstProgram:
    stream = KTokenStream(tokens)
    statements = []

    while stream.current is not None:
        if stream.match(KTokenType.WORKFLOW):
            statements.append(_parse_workflow(stream))
        else:
            is_assignment = False
            if stream.current.token_type == KTokenType.SYMBOL:
                next_pos = stream.position + 1
                if next_pos < len(tokens) and tokens[next_pos].token_type == KTokenType.ASSIGN:
                    is_assignment = True

            if is_assignment:
                target_token = stream.expect(KTokenType.SYMBOL, "Expected variable name")
                assign_token = stream.expect(KTokenType.ASSIGN, "Expected '='")

                expr = _parse_expression(stream)
                statements.append(AstAssignment(target_token.sym_str, expr, assign_token))
            else:
                expr = _parse_expression(stream)
                statements.append(AstExpressionStmt(expr))

    return AstProgram(statements)


def _parse_workflow(stream: KTokenStream) -> AstWorkflow:
    name_token = stream.expect(KTokenType.SYMBOL, "Expected workflow name")
    workflow_name = name_token.sym_str

    stream.expect(KTokenType.OPEN_BRACKET, "Expected '('")
    inputs = []
    if stream.current.token_type != KTokenType.CLOSE_BRACKET:
        while True:
            arg = stream.expect(KTokenType.SYMBOL, "Expected argument")
            inputs.append(arg.sym_str)
            if not stream.match(KTokenType.COMMA):
                break
    stream.expect(KTokenType.CLOSE_BRACKET, "Expected ')'")

    outputs = []
    if stream.match(KTokenType.ARROW):
        while True:
            out = stream.expect(KTokenType.SYMBOL, "Expected output")
            outputs.append(out.sym_str)
            if not stream.match(KTokenType.COMMA):
                break
    stream.expect(KTokenType.COLON, "Expected ':'")

    body = []
    while stream.current is not None:
        if stream.match(KTokenType.RETURN):
            ret_symbols = []
            while True:
                s = stream.expect(KTokenType.SYMBOL, "Expected return symbol")
                ret_symbols.append(s.sym_str)
                if not stream.match(KTokenType.COMMA):
                    break
            if stream.current and stream.current.token_type == KTokenType.SEMICOLON:
                stream.advance()
            return AstWorkflow(workflow_name, inputs, outputs, ret_symbols, body, name_token)

        target_token = stream.expect(KTokenType.SYMBOL, "Expected variable name")
        assign_token = stream.expect(KTokenType.ASSIGN, "Expected '='")
        body.append(AstAssignment(target_token.sym_str, _parse_expression(stream), assign_token))

    raise SyntaxError("Missing return in workflow")


def _parse_expression(stream: KTokenStream) -> AstExpression:
    return _parse_logic_or(stream)


def _parse_logic_or(stream: KTokenStream) -> AstExpression:
    left = _parse_logic_and(stream)
    while stream.current and stream.current.token_type == KTokenType.OR:
        op_token = stream.advance()
        right = _parse_logic_and(stream)
        left = AstCall(op_token.sym_str, [left, right], op_token)
    return left


def _parse_logic_and(stream: KTokenStream) -> AstExpression:
    left = _parse_equality(stream)
    while stream.current and stream.current.token_type == KTokenType.AND:
        op_token = stream.advance()
        right = _parse_equality(stream)
        left = AstCall(op_token.sym_str, [left, right], op_token)
    return left


def _parse_equality(stream: KTokenStream) -> AstExpression:
    left = _parse_comparison(stream)
    while stream.current and stream.current.token_type in (KTokenType.EQUALS, KTokenType.NOT_EQUALS):
        op_token = stream.advance()
        right = _parse_comparison(stream)
        left = AstCall(op_token.sym_str, [left, right], op_token)
    return left


def _parse_comparison(stream: KTokenStream) -> AstExpression:
    left = _parse_additive(stream)
    while stream.current and stream.current.token_type in (
            KTokenType.GREATER_THAN, KTokenType.LESS_THAN,
            KTokenType.EQUALS_GREATER_THAN, KTokenType.EQUALS_LESS_THAN
    ):
        op_token = stream.advance()
        right = _parse_additive(stream)
        left = AstCall(op_token.sym_str, [left, right], op_token)
    return left


def _parse_additive(stream: KTokenStream) -> AstExpression:
    left = _parse_multiplicative(stream)
    while stream.current and stream.current.token_type in (KTokenType.PLUS, KTokenType.MINUS):
        op_token = stream.advance()
        right = _parse_multiplicative(stream)
        left = AstCall(op_token.sym_str, [left, right], op_token)
    return left


def _parse_multiplicative(stream: KTokenStream) -> AstExpression:
    # We start with Unary so that -5 * 2 works
    left = _parse_unary(stream)
    while stream.current and stream.current.token_type in (KTokenType.MULTIPLY, KTokenType.DIVIDE):
        op_token = stream.advance()
        right = _parse_unary(stream)
        left = AstCall(op_token.sym_str, [left, right], op_token)
    return left


def _parse_unary(stream: KTokenStream) -> AstExpression:
    if stream.current and stream.current.token_type in (KTokenType.MINUS, KTokenType.NOT):
        op_token = stream.advance()
        # We call unary recursively so ---5 works
        operand = _parse_unary(stream)
        return AstCall(f"unary_{op_token.sym_str}", [operand], op_token)

    # If no minus/not, move to exponentiation
    return _parse_exponent(stream)


def _parse_exponent(stream: KTokenStream) -> AstExpression:
    # Base must be a primary (2, x, or (expr))
    left = _parse_primary(stream)

    if stream.current and stream.current.token_type == KTokenType.EXPONENT:
        op_token = stream.advance()
        # POWER can be a unary! This allows 2^-2.
        # We call _parse_unary instead of _parse_primary.
        right = _parse_unary(stream)
        return AstCall(op_token.sym_str, [left, right], op_token)

    return left

def _parse_primary(stream: KTokenStream) -> AstExpression:
    if stream.match(KTokenType.OPEN_BRACKET):
        expr = _parse_expression(stream)
        stream.expect(KTokenType.CLOSE_BRACKET, "Expected ')'")
        return _parse_trailers(stream, expr)

    if stream.current.token_type == KTokenType.SYMBOL:
        sym_token = stream.advance()
        if stream.match(KTokenType.OPEN_BRACKET):
            args = []
            if stream.current.token_type != KTokenType.CLOSE_BRACKET:
                while True:
                    args.append(_parse_expression(stream))
                    if not stream.match(KTokenType.COMMA):
                        break
            stream.expect(KTokenType.CLOSE_BRACKET, "Expected ')'")
            return _parse_trailers(stream, AstCall(sym_token.sym_str, args, sym_token))
        return _parse_trailers(stream, AstSymbol(sym_token.sym_str, sym_token))

    elif stream.current.token_type == KTokenType.STRING:
        token = stream.advance()
        val = token.sym_str
        return _parse_trailers(stream, AstLiteral(val, token))

    elif stream.current.token_type == KTokenType.NUMBER:
        token = stream.advance()
        num_str = token.sym_str
        if "." in num_str or "e" in num_str.lower():
            val = float(num_str)
        else:
            val = int(num_str)
        return _parse_trailers(stream, AstLiteral(val, token))

    raise SyntaxError(f"Unexpected token {stream.current}")


def _parse_trailers(stream: KTokenStream, node: AstExpression) -> AstExpression:
    while stream.match(KTokenType.DOT):
        prop_token = stream.expect(KTokenType.SYMBOL, "Expected property name")
        node = AstCall("getattr", [node, AstLiteral(prop_token.sym_str, prop_token)], prop_token)
    return node

