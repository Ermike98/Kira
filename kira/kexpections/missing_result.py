from typing import Iterable

from kira.kexpections.kexception import KException

class KMissingResult(KException):
    def __init__(self, name: str, msg: str = ""):
        self._names = name
        self._msg = msg
