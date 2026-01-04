from kira.kexpections.kexception import KException


class KGenericException(KException):
    def __init__(self, message: str = ""):
        super().__init__()
        self._message = message

    def __repr__(self):
        return f"KGenericException(message={repr(self._message)})"