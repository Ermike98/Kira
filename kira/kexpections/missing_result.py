from typing import Iterable

from kira.kexpections.kexception import KException

class KMissingResults(KException):
    def __init__(self, names: Iterable[str]):
        self._names = list(names)