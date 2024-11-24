"""
Models package initialization
"""
from app.modules.auth.models import User, Role, Token
from app.modules.storage.models import (
    File, Folder, FileVersion, SharedItem,
    FolderCollaborator, FileTag, FileMetadata
)
from app.modules.ai_processor.models import (
    ProcessingTask, ProcessingResult,
    ChatSession, ChatMessage
)

# Import all models here to ensure they are registered with SQLAlchemy
__all__ = [
    # Auth models
    'User',
    'Role',
    'Token',
    
    # Storage models
    'File',
    'Folder',
    'FileVersion',
    'SharedItem',
    'FolderCollaborator',
    'FileTag',
    'FileMetadata',
    
    # AI Processor models
    'ProcessingTask',
    'ProcessingResult',
    'ChatSession',
    'ChatMessage'
]
