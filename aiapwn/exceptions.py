class AiaPwnException(Exception):
    """
    Base exception class for AiaPwn-related errors.
    All custom exceptions should inherit from this class.
    """
    pass

class ClientError(AiaPwnException):
    """
    Exception raised for errors occurring in the client module.
    For example, HTTP request failures or JSON parsing issues.
    """
    pass

class PayloadError(AiaPwnException):
    """
    Exception raised when there are issues with payload generation or management.
    """
    pass

class ScanError(AiaPwnException):
    """
    Exception raised for errors encountered during the scanning process.
    """
    pass
