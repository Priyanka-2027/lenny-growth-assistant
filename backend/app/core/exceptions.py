"""
Application-level exception hierarchy.
Maps to structured HTTP error responses.
"""
from fastapi import HTTPException, status


class AppError(Exception):
    """Base application error."""
    status_code: int = 500
    detail: str = "An unexpected error occurred."

    def __init__(self, detail: str | None = None):
        self.detail = detail or self.__class__.detail
        super().__init__(self.detail)


class NotFoundError(AppError):
    status_code = 404
    detail = "Resource not found."


class ValidationError(AppError):
    status_code = 422
    detail = "Validation error."


class LLMUnavailableError(AppError):
    status_code = 503
    detail = "The language model is currently unavailable."


class LLMTimeoutError(AppError):
    status_code = 504
    detail = "The language model request timed out."


class RetrievalError(AppError):
    status_code = 500
    detail = "Failed to retrieve context from the knowledge base."


class DatabaseError(AppError):
    status_code = 500
    detail = "A database error occurred."


class ArtifactError(AppError):
    status_code = 500
    detail = "Failed to generate artifact."


def to_http_exception(err: AppError) -> HTTPException:
    return HTTPException(status_code=err.status_code, detail=err.detail)
