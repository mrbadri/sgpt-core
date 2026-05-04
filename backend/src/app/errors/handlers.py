"""Error handlers for FastAPI."""

from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.errors.base import (
    ApplicationError,
    AuthorizationError,
    NotFoundError,
    PermissionError,
    ValidationError,
)


async def application_error_handler(
    request: Request, exc: ApplicationError
) -> JSONResponse:
    """Handle application errors."""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    if isinstance(exc, ValidationError):
        status_code = status.HTTP_400_BAD_REQUEST
    elif isinstance(exc, NotFoundError):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, AuthorizationError):
        status_code = status.HTTP_401_UNAUTHORIZED
    elif isinstance(exc, PermissionError):
        status_code = status.HTTP_403_FORBIDDEN

    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
            }
        },
    )


async def general_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Handle unexpected exceptions."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
            }
        },
    )
