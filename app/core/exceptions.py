"""
Custom exceptions for the application.
"""
from typing import Any, Dict, Optional
from fastapi import HTTPException, status

class BaseAPIException(HTTPException):
    """Base API exception with status code and detail message."""
    def __init__(
        self,
        status_code: int,
        detail: str,
        headers: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(status_code=status_code, detail=detail, headers=headers)

class StorageError(BaseAPIException):
    """Base exception for storage operations."""
    def __init__(self, detail: str, headers: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            headers=headers
        )

class FileNotFoundError(StorageError):
    """Raised when a file is not found in storage."""
    def __init__(self, detail: str = "File not found", headers: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            headers=headers
        )

class FileUploadError(StorageError):
    """Raised when file upload fails."""
    pass

class FileDeleteError(StorageError):
    """Raised when file deletion fails."""
    pass

class AIProcessingError(BaseAPIException):
    """Base exception for AI processing operations."""
    def __init__(self, detail: str, headers: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            headers=headers
        )

class ModelLoadError(AIProcessingError):
    """Raised when model loading fails."""
    pass

class ProcessingError(AIProcessingError):
    """Raised when file processing fails."""
    pass

class AuthenticationError(BaseAPIException):
    """Base exception for authentication operations."""
    def __init__(self, detail: str, headers: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers=headers
        )

class InvalidCredentialsError(AuthenticationError):
    """Raised when credentials are invalid."""
    def __init__(self, detail: str = "Invalid credentials", headers: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(detail=detail, headers={"WWW-Authenticate": "Bearer", **(headers or {})})

class TokenError(AuthenticationError):
    """Raised when token is invalid or expired."""
    def __init__(self, detail: str = "Invalid or expired token", headers: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(detail=detail, headers={"WWW-Authenticate": "Bearer", **(headers or {})})

class PermissionError(BaseAPIException):
    """Raised when user lacks required permissions."""
    def __init__(self, detail: str = "Insufficient permissions", headers: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            headers=headers
        )

class DatabaseError(BaseAPIException):
    """Base exception for database operations."""
    def __init__(self, detail: str, headers: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            headers=headers
        )

class ValidationError(BaseAPIException):
    """Base exception for validation errors."""
    def __init__(self, detail: str, headers: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            headers=headers
        )

class NotFoundException(BaseAPIException):
    """Raised when a requested resource is not found."""
    def __init__(self, detail: str = "Resource not found", headers: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            headers=headers
        )

class ConflictError(BaseAPIException):
    """Raised when there is a conflict with the current state."""
    def __init__(self, detail: str = "Resource conflict", headers: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            headers=headers
        )
