from typing import Iterable

from kira.kexpections.kexception import KException

class KMissingResult(KException):
    def __init__(self, name: str, msg: str = ""):
        self._name_missing_result = name
        self._msg = msg
