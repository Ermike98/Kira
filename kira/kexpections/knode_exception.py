from enum import Enum

from kira.kexpections.kexception import KException


class KNodeExceptionType(Enum):
    MISSING_INPUTS = "Missing inputs"
    MISSING_OUTPUTS = "Missing outputs"
    WRONG_INPUT_TYPES = "Wrong input types"
    WRONG_OUTPUT_TYPES = "Wrong output types"
    TOO_MANY_OUTPUTS = "Too many outputs"
    INVALID_EDGE = "Invalid edge"
    FAILED_OUTPUT = "Failed output"

class KNodeException(KException):
    def __init__(self, node, exception_type: KNodeExceptionType, message: str = "", **kwargs):
        super().__init__()
        self._node = node
        self._type = exception_type
        self._message = message
        self._kwargs = kwargs

    def __repr__(self):
        return f"KNodeException(node={repr(self._node)}, type={repr(self._type)}, message={repr(self._message)}, kwargs={repr(self._kwargs)})"
