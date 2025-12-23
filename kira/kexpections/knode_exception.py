from enum import Enum

from kira.kexpections.kexception import KException


class KNodeExceptionType(Enum):
    MISSING_INPUTS = "Missing inputs"
    MISSING_OUTPUTS = "Missing outputs"
    WRONG_INPUT_TYPES = "Wrong input types"
    WRONG_OUTPUT_TYPES = "Wrong output types"
    TOO_MANY_OUTPUTS = "Too many outputs"
    INVALID_EDGE = "Invalid edge"

class KNodeException(KException):
    def __init__(self, node, exception_type: KNodeExceptionType, message: str = "", **kwargs):
        self._node = node
        self._type = exception_type
        self._message = message
        self._kwargs = kwargs
