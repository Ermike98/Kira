import enum
from typing import NamedTuple


class KTokenType(enum.Enum):
    SYMBOL = ""

    OPEN_BRACKET = "("
    CLOSE_BRACKET = ")"
    COMMA = ","
    DOT = "."
    COLON = ":"
    SEMICOLON = ";"
    ARROW = "->"

    END_LINE = "\n"
    WHITESPACE = " \t"

    OPEN_SQUARE_BRACKET = "["
    CLOSE_SQUARE_BRACKET = "]"

    PLUS = "+"
    MINUS = "-"
    MULTIPLY = "*"
    DIVIDE = "/"
    EXPONENT = "^"
    ASSIGN = "="

    GREATER_THAN = ">"
    LESS_THAN = "<"
    EQUALS_GREATER_THAN = ">="
    EQUALS_LESS_THAN = "<="
    NOT_EQUALS = "!="
    EQUALS = "=="
    NOT = "!"
    AND = "and"
    OR = "or"

    WORKFLOW = "workflow"
    RETURN = "return"

    STRING = "'\""
    NUMBER = "0123456789.eE-+"


class KToken(NamedTuple):
    sym_str: str
    token_type: KTokenType


def ktokenize(expression: str):
    stop_idx = 0

    tokens = []

    while stop_idx < len(expression):
        char = expression[stop_idx]

        if char in KTokenType.OPEN_BRACKET.value:
            tokens.append(KToken(char, KTokenType.OPEN_BRACKET))
        elif char in KTokenType.CLOSE_BRACKET.value:
            tokens.append(KToken(char, KTokenType.CLOSE_BRACKET))
        elif char in KTokenType.COMMA.value:
            tokens.append(KToken(char, KTokenType.COMMA))
        elif char in KTokenType.DOT.value:
            # Check if it's a number starting with dot (e.g. .89)
            if stop_idx + 1 < len(expression) and expression[stop_idx + 1].isdigit():
                start_idx = stop_idx
                stop_idx += 1
                while stop_idx < len(expression) and expression[stop_idx].isdigit():
                    stop_idx += 1
                # Support scientific notation
                if stop_idx < len(expression) and expression[stop_idx] in "eE":
                    e_pos = stop_idx
                    stop_idx += 1
                    if stop_idx < len(expression) and expression[stop_idx] in "+-":
                        stop_idx += 1
                    if stop_idx < len(expression) and expression[stop_idx].isdigit():
                        while stop_idx < len(expression) and expression[stop_idx].isdigit():
                            stop_idx += 1
                    else:
                        stop_idx = e_pos # Backtrack
                tokens.append(KToken(expression[start_idx:stop_idx], KTokenType.NUMBER))
                stop_idx -= 1
            else:
                tokens.append(KToken(char, KTokenType.DOT))
        elif char in KTokenType.COLON.value:
            tokens.append(KToken(char, KTokenType.COLON))
        elif char in KTokenType.SEMICOLON.value:
            tokens.append(KToken(char, KTokenType.SEMICOLON))
        elif char in KTokenType.END_LINE.value:
            tokens.append(KToken(char, KTokenType.END_LINE))
        elif char in KTokenType.WHITESPACE.value:
            start_idx = stop_idx
            while stop_idx < len(expression) and expression[stop_idx] in KTokenType.WHITESPACE.value:
                stop_idx += 1
            tokens.append(KToken(expression[start_idx:stop_idx], KTokenType.WHITESPACE))
            stop_idx -= 1
        elif char in KTokenType.GREATER_THAN.value: # = ">" || ">="
            if stop_idx + 1 < len(expression) and expression[stop_idx + 1] == "=":
                tokens.append(KToken(char + expression[stop_idx + 1], KTokenType.EQUALS_GREATER_THAN))
                stop_idx += 1
            else:
                tokens.append(KToken(char, KTokenType.GREATER_THAN))
        elif char in KTokenType.LESS_THAN.value: # = "<" || "<="
            if stop_idx + 1 < len(expression) and expression[stop_idx + 1] == "=":
                tokens.append(KToken(char + expression[stop_idx + 1], KTokenType.EQUALS_LESS_THAN))
                stop_idx += 1
            else:
                tokens.append(KToken(char, KTokenType.LESS_THAN))
        elif char in KTokenType.NOT.value: # = "!" || "!="
            if stop_idx + 1 < len(expression) and expression[stop_idx + 1] == "=":
                tokens.append(KToken(char + expression[stop_idx + 1], KTokenType.NOT_EQUALS))
                stop_idx += 1
            else:
                tokens.append(KToken(char, KTokenType.NOT))
        elif char in KTokenType.ASSIGN.value: # = "=" || "=="
            if stop_idx + 1 < len(expression) and expression[stop_idx + 1] == "=":
                tokens.append(KToken(char + expression[stop_idx + 1], KTokenType.EQUALS))
                stop_idx += 1
            else:
                tokens.append(KToken(char, KTokenType.ASSIGN))
        elif char in KTokenType.OPEN_SQUARE_BRACKET.value:
            tokens.append(KToken(char, KTokenType.OPEN_SQUARE_BRACKET))
        elif char in KTokenType.CLOSE_SQUARE_BRACKET.value:
            tokens.append(KToken(char, KTokenType.CLOSE_SQUARE_BRACKET))
        elif char in KTokenType.PLUS.value:
            tokens.append(KToken(char, KTokenType.PLUS))
        elif char in KTokenType.MINUS.value:
            if stop_idx + 1 < len(expression) and expression[stop_idx + 1] == ">":
                tokens.append(KToken(char + expression[stop_idx + 1], KTokenType.ARROW))
                stop_idx += 1
            else:
                tokens.append(KToken(char, KTokenType.MINUS))
        elif char in KTokenType.MULTIPLY.value:
            tokens.append(KToken(char, KTokenType.MULTIPLY))
        elif char in KTokenType.DIVIDE.value:
            tokens.append(KToken(char, KTokenType.DIVIDE))
        elif char in KTokenType.EXPONENT.value:
            tokens.append(KToken(char, KTokenType.EXPONENT))
        elif char in KTokenType.STRING.value:
            quote_char = char
            stop_idx += 1
            start_idx = stop_idx
            while stop_idx < len(expression) and expression[stop_idx] != quote_char:
                stop_idx += 1
            if stop_idx >= len(expression):
                raise SyntaxError(f"Unterminated string literal at {start_idx-1}")
            tokens.append(KToken(expression[start_idx:stop_idx], KTokenType.STRING))
        elif char.isdigit():
            start_idx = stop_idx
            while stop_idx < len(expression) and expression[stop_idx].isdigit():
                stop_idx += 1
            if stop_idx < len(expression) and expression[stop_idx] == ".":
                stop_idx += 1
                while stop_idx < len(expression) and expression[stop_idx].isdigit():
                    stop_idx += 1
            if stop_idx < len(expression) and expression[stop_idx] in "eE":
                e_pos = stop_idx
                stop_idx += 1
                if stop_idx < len(expression) and expression[stop_idx] in "+-":
                    stop_idx += 1
                if stop_idx < len(expression) and expression[stop_idx].isdigit():
                    while stop_idx < len(expression) and expression[stop_idx].isdigit():
                        stop_idx += 1
                else:
                    stop_idx = e_pos # Backtrack
            tokens.append(KToken(expression[start_idx:stop_idx], KTokenType.NUMBER))
            stop_idx -= 1
        else:
            start_idx = stop_idx
            while stop_idx < len(expression) and (expression[stop_idx].isalnum() or expression[stop_idx] == "_"):
                stop_idx += 1

            word = expression[start_idx:stop_idx]

            if word == "and":
                tokens.append(KToken(word, KTokenType.AND))
            elif word == "or":
                tokens.append(KToken(word, KTokenType.OR))
            elif word == "workflow":
                tokens.append(KToken(word, KTokenType.WORKFLOW))
            elif word == "return":
                tokens.append(KToken(word, KTokenType.RETURN))
            else:
                tokens.append(KToken(word, KTokenType.SYMBOL))

            stop_idx -= 1

        stop_idx += 1

    return tokens
