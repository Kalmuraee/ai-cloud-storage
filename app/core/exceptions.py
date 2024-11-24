"""
Custom exceptions for the application.
"""

class StorageError(Exception):
    """Base exception for storage operations."""
    pass

class FileNotFoundError(StorageError):
    """Raised when a file is not found in storage."""
    pass

class FileUploadError(StorageError):
    """Raised when file upload fails."""
    pass

class FileDeleteError(StorageError):
    """Raised when file deletion fails."""
    pass

class AIProcessingError(Exception):
    """Base exception for AI processing operations."""
    pass

class ModelLoadError(AIProcessingError):
    """Raised when model loading fails."""
    pass

class ProcessingError(AIProcessingError):
    """Raised when file processing fails."""
    pass

class AuthenticationError(Exception):
    """Base exception for authentication operations."""
    pass

class InvalidCredentialsError(AuthenticationError):
    """Raised when credentials are invalid."""
    pass

class TokenError(AuthenticationError):
    """Raised when token is invalid or expired."""
    pass

class PermissionError(AuthenticationError):
    """Raised when user lacks required permissions."""
    pass

class DatabaseError(Exception):
    """Base exception for database operations."""
    pass

class ValidationError(Exception):
    """Base exception for validation errors."""
    pass
