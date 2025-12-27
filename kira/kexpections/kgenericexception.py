from kira.kexpections.kexception import KException


class KGenericException(KException):
    def __init__(self, message: str = ""):
        super().__init__(message)