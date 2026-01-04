from typing import Iterable

from kira.kexpections.kexception import KException

class KMissingResult(KException):
    def __init__(self, name: str, msg: str = ""):
        super().__init__()
        self._name_missing_result = name
        self._msg = msg

    def __repr__(self):
        return f"KMissingResult(name={repr(self._name_missing_result)}, msg={repr(self._msg)})"
