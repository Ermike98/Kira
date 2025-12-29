import enum
from abc import abstractmethod, ABC

from kira.core.kcontext import KContext
from kira.core.kobject import KObject
from kira.kdata.kdata import KDataValue, KData
from kira.kdata.kliteral import KLiteral
from kira.klanguage.ktokenizer import KToken, KTokenType
from kira.knodes.knode import KNode, KNodeInstance


def token_hash_name(token: KToken, name: str, hash_limit = 100_000_000) -> str:
    token_hash = abs(hash(token)) % hash_limit
    return f"{name}_{token_hash:08d}"


class KSyntaxType(enum.Enum):
    EXPRESSION = 0
    SYMBOL = 1
    VALUE = 2


class KAstNode(ABC):
    @abstractmethod
    def evaluate(self, ctx: KContext) -> KObject:
        pass


class KAstExpression(KAstNode):
    def __init__(self, node_sym: KToken, children: list[KAstNode]):
        self._node_sym = node_sym
        self._children = children

    def evaluate(self, ctx: KContext) -> KObject:
        node = ctx.get_object(self._node_sym.sym_str)

        assert isinstance(node, KNode), f"Node {self._node_sym.sym_str} is not a KNode"

        inputs = {name: child.evaluate(ctx) for name, child in zip(node.input_names, self._children)}
        node_instance = KNodeInstance(node, token_hash_name(self._node_sym, f"node_{node.name}"))
        result = node_instance(inputs)

        ctx.register_object(result)

        return result


class KAstSymbol(KAstNode):
    def __init__(self, sym: KToken):
        self._sym = sym

    def evaluate(self, ctx: KContext) -> KObject:
        return ctx.get_object(self._sym.sym_str)


class KAstValue(KAstNode):
    __HASH_LIMIT = 100_000_000

    def __init__(self, value: KToken):
        self._value = value
        self._name = token_hash_name(value, "literal", hash_limit = KAstValue.__HASH_LIMIT)

    def evaluate(self, ctx: KContext) -> KObject:
        return KData(self._name, KLiteral(self._value))


def kast(tokens: list[KToken]):
    pass
