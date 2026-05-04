"""Base error classes."""


class ApplicationError(Exception):
    """Base application error."""

    def __init__(self, message: str, code: str = "INTERNAL_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class ValidationError(ApplicationError):
    """Validation error."""

    def __init__(self, message: str, code: str = "VALIDATION_ERROR"):
        super().__init__(message, code)


class NotFoundError(ApplicationError):
    """Resource not found error."""

    def __init__(self, message: str, code: str = "NOT_FOUND"):
        super().__init__(message, code)


class AuthorizationError(ApplicationError):
    """Authorization error."""

    def __init__(self, message: str, code: str = "UNAUTHORIZED"):
        super().__init__(message, code)


class PermissionError(ApplicationError):
    """Permission denied error."""

    def __init__(self, message: str, code: str = "FORBIDDEN"):
        super().__init__(message, code)
