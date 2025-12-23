from typing import Iterable

from kira.kexpections.kexception import KException
from kira.core.kobject import KObject


class KFailedDependency(KException):
    def __init__(self, failed_dependencies: Iterable[KObject]):
        self._failed_dependencies = failed_dependencies