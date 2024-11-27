"""
AI Processor module routes
"""
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.logging import get_logger
from app.modules.ai_processor.dependencies import get_ai_service
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.storage.models import File
from app.modules.ai_processor.models import ProcessingTask
from app.modules.ai_processor.schemas import (
    ChatSessionCreate,
    ChatSessionResponse,
    ChatMessageCreate,
    ChatMessageResponse,
    ChatHistory
)

router = APIRouter()
logger = get_logger(__name__)

class ProcessFileRequest(BaseModel):
    """Request model for file processing"""
    task_type: str = Field(..., description="Type of processing task (classify/embed)")
    params: Optional[Dict[str, Any]] = Field(None, description="Optional parameters for the task")

    class Config:
        schema_extra = {
            "example": {
                "task_type": "classify",
                "params": {
                    "model": "distilbert-base-uncased-finetuned-sst-2-english",
                    "max_length": 512
                }
            }
        }

class TaskResponse(BaseModel):
    """Response model for processing tasks"""
    id: str = Field(..., description="Task ID")
    status: str = Field(..., description="Current status of the task")
    created_at: str = Field(..., description="Task creation timestamp")
    started_at: Optional[str] = Field(None, description="Task start timestamp")
    completed_at: Optional[str] = Field(None, description="Task completion timestamp")
    error: Optional[str] = Field(None, description="Error message if task failed")
    result: Optional[Dict[str, Any]] = Field(None, description="Task processing results")

    class Config:
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "completed",
                "created_at": "2024-01-01T12:00:00Z",
                "started_at": "2024-01-01T12:00:01Z",
                "completed_at": "2024-01-01T12:00:02Z",
                "error": None,
                "result": {
                    "classification": {
                        "label": "positive",
                        "score": 0.95
                    }
                }
            }
        }

class FileMetadataResponse(BaseModel):
    """Response model for file metadata"""
    classification: Optional[Dict[str, Any]] = Field(None, description="Classification results")
    embedding: Optional[Dict[str, Any]] = Field(None, description="Embedding results")

    class Config:
        schema_extra = {
            "example": {
                "classification": {
                    "labels": ["positive"],
                    "scores": [0.95],
                    "model": "distilbert-base-uncased-finetuned-sst-2-english"
                },
                "embedding": {
                    "embedding": [0.1, 0.2, 0.3],
                    "model": "all-MiniLM-L6-v2"
                }
            }
        }

@router.post("/files/{file_id}/process", response_model=TaskResponse, tags=["AI Processing"])
async def process_file(
    file_id: str = Path(..., description="ID of the file to process"),
    request: ProcessFileRequest = Body(..., description="Processing request parameters"),
    current_user: User = Depends(get_current_user),
    ai_service = Depends(get_ai_service)
):
    """
    Start processing a file with AI models.
    
    - **file_id**: ID of the file to process
    - **task_type**: Type of processing task (classify/embed)
    - **params**: Optional parameters for the processing task
    
    Returns:
        TaskResponse: Created processing task information
    """
    try:
        # Get file
        file = await ai_service.db.get(File, {"id": file_id, "owner_id": current_user.id})
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Start processing
        task = await ai_service.process_file(
            file,
            request.task_type,
            request.params
        )
        
        return TaskResponse(
            id=task.id,
            status=task.status,
            created_at=task.created_at.isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start processing: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tasks/{task_id}", response_model=TaskResponse, tags=["AI Processing"])
async def get_task_status(
    task_id: str = Path(..., description="ID of the task to retrieve"),
    current_user: User = Depends(get_current_user),
    ai_service = Depends(get_ai_service)
):
    """
    Get status of a processing task.
    
    - **task_id**: ID of the task to retrieve
    
    Returns:
        TaskResponse: Current task status and results if completed
    """
    try:
        # Get task
        task = await ai_service.db.get(ProcessingTask, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Verify file access
        file = await ai_service.db.get(File, {"id": task.file_id, "owner_id": current_user.id})
        if not file:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return await ai_service.get_task_status(task_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/tasks/{task_id}", response_model=Dict[str, str], tags=["AI Processing"])
async def cancel_task(
    task_id: str = Path(..., description="ID of the task to cancel"),
    current_user: User = Depends(get_current_user),
    ai_service = Depends(get_ai_service)
):
    """
    Cancel a processing task.
    
    - **task_id**: ID of the task to cancel
    
    Returns:
        Dict[str, str]: Confirmation message
    """
    try:
        # Get task
        task = await ai_service.db.get(ProcessingTask, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Verify file access
        file = await ai_service.db.get(File, {"id": task.file_id, "owner_id": current_user.id})
        if not file:
            raise HTTPException(status_code=403, detail="Access denied")
        
        await ai_service.cancel_task(task_id)
        return {"message": "Task cancelled successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tasks", response_model=List[TaskResponse], tags=["AI Processing"])
async def list_tasks(
    file_id: Optional[str] = Query(None, description="Optional file ID to filter tasks"),
    status: Optional[str] = Query(None, description="Optional status to filter tasks"),
    current_user: User = Depends(get_current_user),
    ai_service = Depends(get_ai_service)
):
    """
    List processing tasks.
    
    - **file_id**: Optional ID of the file to filter tasks by
    - **status**: Optional status to filter tasks by
    
    Returns:
        List[TaskResponse]: List of tasks matching the filter criteria
    """
    try:
        return await ai_service.list_tasks(file_id, status)
    except Exception as e:
        logger.error(f"Failed to list tasks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/files/{file_id}/metadata", response_model=FileMetadataResponse, tags=["AI Processing"])
async def get_file_metadata(
    file_id: str = Path(..., description="ID of the file to retrieve metadata for"),
    current_user: User = Depends(get_current_user),
    ai_service = Depends(get_ai_service)
):
    """
    Get AI-processed metadata for a file.
    
    - **file_id**: ID of the file to retrieve metadata for
    
    Returns:
        FileMetadataResponse: AI processing results for the file
    """
    try:
        # Get file
        file = await ai_service.db.get(File, {"id": file_id, "owner_id": current_user.id})
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get metadata
        metadata = file.file_metadata
        if not metadata:
            return FileMetadataResponse()
        
        return FileMetadataResponse(
            classification=metadata.classification,
            embedding=metadata.embedding
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get file metadata: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/chat/sessions",
    response_model=ChatSessionResponse,
    tags=["Chat"],
    responses={
        201: {
            "description": "Chat session created successfully",
            "model": ChatSessionResponse
        },
        422: {
            "description": "Validation error in request body"
        }
    }
)
async def create_chat_session(
    data: ChatSessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new chat session.
    
    Creates a new chat session with the specified folders. The session will have access
    to files in these folders for context during the conversation.
    
    - **folders**: List of folder IDs to include in the chat context
    - **name**: Optional name for the chat session
    """
    try:
        ai_service = AIProcessorService(db)
        return await ai_service.create_chat_session(current_user.id, data)
    except Exception as e:
        logger.error(f"Failed to create chat session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/chat/sessions/{session_id}/messages",
    response_model=ChatMessageResponse,
    tags=["Chat"],
    responses={
        200: {
            "description": "Message processed successfully",
            "model": ChatMessageResponse
        },
        404: {
            "description": "Chat session not found"
        },
        422: {
            "description": "Validation error in request body"
        }
    }
)
async def continue_chat_session(
    session_id: str,
    data: ChatMessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Continue a chat session by sending a new message.
    
    Sends a new message to an existing chat session and gets the AI's response.
    The response will be generated using context from files in the session's folders.
    
    - **session_id**: ID of the chat session
    - **message**: User's message text
    """
    try:
        ai_service = AIProcessorService(db)
        return await ai_service.process_chat_message(session_id, current_user.id, data)
    except Exception as e:
        logger.error(f"Failed to process chat message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/chat/sessions/{session_id}/history",
    response_model=ChatHistory,
    tags=["Chat"],
    responses={
        200: {
            "description": "Chat history retrieved successfully",
            "model": ChatHistory
        },
        404: {
            "description": "Chat session not found"
        }
    }
)
async def get_chat_history(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the message history for a chat session.
    
    Retrieves all messages exchanged in a chat session, including both user messages
    and AI responses.
    
    - **session_id**: ID of the chat session to retrieve history for
    """
    try:
        ai_service = AIProcessorService(db)
        return await ai_service.get_chat_history(session_id, current_user.id)
    except Exception as e:
        logger.error(f"Failed to get chat history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
