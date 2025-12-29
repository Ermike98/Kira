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

    QUOTES = "'\""


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
            tokens.append(KToken(char, KTokenType.MINUS))
        elif char in KTokenType.MULTIPLY.value:
            tokens.append(KToken(char, KTokenType.MULTIPLY))
        elif char in KTokenType.DIVIDE.value:
            tokens.append(KToken(char, KTokenType.DIVIDE))
        elif char in KTokenType.EXPONENT.value:
            tokens.append(KToken(char, KTokenType.EXPONENT))
        elif char in KTokenType.QUOTES.value:
            start_idx = stop_idx + 1
            while stop_idx < len(expression) and expression[stop_idx] != char:
                stop_idx += 1
            tokens.append(KToken(expression[start_idx:stop_idx], KTokenType.QUOTES))
        else:
            start_idx = stop_idx
            while stop_idx < len(expression) and (expression[stop_idx].isalnum() or expression[stop_idx] in "_."):
                stop_idx += 1

            word = expression[start_idx:stop_idx]

            if word == "and":
                tokens.append(KToken(word, KTokenType.AND))
            elif word == "or":
                tokens.append(KToken(word, KTokenType.OR))
            else:
                tokens.append(KToken(word, KTokenType.SYMBOL))

            stop_idx -= 1

        stop_idx += 1

    return tokens