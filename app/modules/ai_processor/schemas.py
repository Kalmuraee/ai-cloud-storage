"""
AI Processor schemas
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID

from app.modules.ai_processor.models import ProcessingStatus

class TaskCreate(BaseModel):
    """Task creation schema"""
    file_id: int = Field(..., description="ID of the file to process")
    task_type: str = Field(..., description="Type of processing task")
    params: Optional[Dict[str, Any]] = Field(default=None, description="Optional task parameters")

class TaskUpdate(BaseModel):
    """Task update schema"""
    status: ProcessingStatus = Field(..., description="New task status")
    error_message: Optional[str] = Field(default=None, description="Error message if task failed")

class ProcessingResult(BaseModel):
    """Processing result schema"""
    task_id: int = Field(..., description="ID of the associated task")
    result_type: str = Field(..., description="Type of processing result")
    result_data: Dict[str, Any] = Field(..., description="Processing result data")
    confidence_score: Optional[float] = Field(default=None, description="Confidence score if applicable")

class ChatMessage(BaseModel):
    """Chat message schema"""
    sender: str = Field(..., description="Message sender (user or ai)")
    message: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ChatSession(BaseModel):
    """Chat session schema"""
    id: UUID = Field(..., description="Unique session identifier")
    user_id: int = Field(..., description="User who owns the session")
    folder_ids: List[int] = Field(..., description="IDs of folders included in the chat context")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ChatSessionCreate(BaseModel):
    """Chat session creation schema"""
    folders: List[int] = Field(..., description="List of folder IDs to include in chat context")
    message: str = Field(..., description="Initial message")

class ChatSessionResponse(BaseModel):
    """Chat session response schema"""
    session_id: UUID = Field(..., description="Unique session identifier")
    response: str = Field(..., description="AI's response to the message")

class ChatMessageCreate(BaseModel):
    """Chat message creation schema"""
    message: str = Field(..., description="User's message")

class ChatMessageResponse(BaseModel):
    """Chat message response schema"""
    response: str = Field(..., description="AI's response to the message")

class ChatHistory(BaseModel):
    """Chat history schema"""
    messages: List[ChatMessage] = Field(default_factory=list)
