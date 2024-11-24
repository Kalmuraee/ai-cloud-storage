"""
AI Processor service implementation
"""
from typing import Dict, Any, Optional, List
import asyncio
from datetime import datetime
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import joinedload

from app.core.config import settings
from app.core.logging import get_logger
from app.modules.ai_processor.models import (
    ProcessingTask, ProcessingResult,
    ChatSession, ChatMessage
)
from app.modules.storage.models import File, FileMetadata, Folder
from app.modules.storage.service import StorageService
from . import text_classifier, text_embedder

logger = get_logger(__name__)

class AIProcessorService:
    """AI Processor service for processing files with AI models"""
    
    def __init__(self, db: AsyncSession):
        """Initialize AI processor service"""
        self.db = db
        self.text_classifier = text_classifier
        self.text_embedder = text_embedder
        self.processing_tasks: Dict[str, asyncio.Task] = {}
        self.storage_service = StorageService(db)

    async def process_file(
        self,
        file: File,
        task_type: str,
        params: Optional[Dict[str, Any]] = None
    ) -> ProcessingTask:
        """Start processing a file"""
        try:
            # Create processing task
            task = ProcessingTask(
                file_id=file.id,
                task_type=task_type,
                params=params or {},
                status="pending"
            )
            self.db.add(task)
            await self.db.commit()
            await self.db.refresh(task)
            
            # Start processing in background
            processing_task = asyncio.create_task(
                self._process_file_task(task.id, file, task_type, params)
            )
            self.processing_tasks[str(task.id)] = processing_task
            
            return task
        except Exception as e:
            logger.error(f"Failed to start processing task: {str(e)}")
            raise
    
    async def _process_file_task(
        self,
        task_id: str,
        file: File,
        task_type: str,
        params: Dict[str, Any]
    ):
        """Background task for processing a file"""
        try:
            # Update task status
            task = await self.db.get(ProcessingTask, task_id)
            task.status = "processing"
            task.started_at = datetime.utcnow()
            await self.db.commit()
            
            # Process file based on task type
            result = None
            if task_type == "classify":
                result = await self._classify_file(file, params)
            elif task_type == "embed":
                result = await self._embed_file(file, params)
            else:
                raise ValueError(f"Unsupported task type: {task_type}")
            
            # Create processing result
            processing_result = ProcessingResult(
                task_id=task_id,
                result=result
            )
            self.db.add(processing_result)
            
            # Update task status
            task.status = "completed"
            task.completed_at = datetime.utcnow()
            
            # Update file metadata
            metadata = file.file_metadata or FileMetadata(file_id=file.id)
            if task_type == "classify":
                metadata.classification = result
            elif task_type == "embed":
                metadata.embedding = result
            
            if not file.file_metadata:
                self.db.add(metadata)
            
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"Error processing file {file.id}: {str(e)}")
            # Update task status to failed
            task = await self.db.get(ProcessingTask, task_id)
            task.status = "failed"
            task.error = str(e)
            await self.db.commit()
    
    async def _classify_file(
        self,
        file: File,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Classify file content"""
        try:
            # Get file content
            content = await self._get_file_content(file)
            
            # Run classification
            result = self.text_classifier(content)
            
            return {
                "labels": [r["label"] for r in result],
                "scores": [r["score"] for r in result],
                "model": settings.DEFAULT_CLASSIFICATION_MODEL
            }
        except Exception as e:
            logger.error(f"Error classifying file {file.id}: {str(e)}")
            raise
    
    async def _embed_file(
        self,
        file: File,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate embeddings for file content"""
        try:
            # Get file content
            content = await self._get_file_content(file)
            
            # Generate embeddings
            embeddings = self.text_embedder.encode(content)
            
            return {
                "embedding": embeddings.tolist(),
                "model": settings.DEFAULT_EMBEDDING_MODEL
            }
        except Exception as e:
            logger.error(f"Error generating embeddings for file {file.id}: {str(e)}")
            raise
    
    async def _get_file_content(self, file: File) -> str:
        """Get file content for processing"""
        # TODO: Implement file content retrieval from storage service
        return "Sample file content"

    async def get_task_status(
        self,
        task_id: str,
    ) -> Dict[str, Any]:
        """Get status of a processing task"""
        try:
            task = await self.db.get(ProcessingTask, task_id)
            if not task:
                raise ValueError(f"Task not found: {task_id}")
            
            status = {
                "id": task.id,
                "status": task.status,
                "created_at": task.created_at,
                "started_at": task.started_at,
                "completed_at": task.completed_at,
                "error": task.error
            }
            
            if task.status == "completed":
                result = await self.db.get(ProcessingResult, {"task_id": task_id})
                if result:
                    status["result"] = result.result
            
            return status
        except Exception as e:
            logger.error(f"Failed to get task status: {str(e)}")
            raise
    
    async def cancel_task(
        self,
        task_id: str,
    ) -> None:
        """Cancel a processing task"""
        try:
            task = await self.db.get(ProcessingTask, task_id)
            if not task:
                raise ValueError(f"Task not found: {task_id}")
            
            if task.status in ["completed", "failed"]:
                return
            
            # Cancel background task
            processing_task = self.processing_tasks.get(str(task_id))
            if processing_task:
                processing_task.cancel()
                del self.processing_tasks[str(task_id)]
            
            # Update task status
            task.status = "cancelled"
            await self.db.commit()
        except Exception as e:
            logger.error(f"Failed to cancel task: {str(e)}")
            raise
    
    async def list_tasks(
        self,
        file_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List processing tasks"""
        try:
            query = self.db.query(ProcessingTask)
            
            if file_id:
                query = query.filter(ProcessingTask.file_id == file_id)
            if status:
                query = query.filter(ProcessingTask.status == status)
            
            tasks = await query.all()
            return [
                {
                    "id": task.id,
                    "file_id": task.file_id,
                    "task_type": task.task_type,
                    "status": task.status,
                    "created_at": task.created_at,
                    "started_at": task.started_at,
                    "completed_at": task.completed_at,
                    "error": task.error
                }
                for task in tasks
            ]
        except Exception as e:
            logger.error(f"Failed to list tasks: {str(e)}")
            raise

    async def create_chat_session(
        self,
        user_id: int,
        folder_ids: List[int],
        initial_message: str
    ) -> Dict[str, Any]:
        """Create a new chat session"""
        try:
            # Verify folders exist and user has access
            folders = []
            for folder_id in folder_ids:
                folder = await self.storage_service.get_folder(folder_id)
                if not folder or folder.owner_id != user_id:
                    raise ValueError(f"Invalid or inaccessible folder: {folder_id}")
                folders.append(folder)

            # Create chat session
            session = ChatSession(
                user_id=user_id,
                folder_ids=folder_ids
            )
            self.db.add(session)
            
            # Add initial message
            user_message = ChatMessage(
                session=session,
                sender="user",
                message=initial_message
            )
            self.db.add(user_message)
            
            # Generate AI response
            ai_response = await self._generate_response(session.id, folders, initial_message)
            ai_message = ChatMessage(
                session=session,
                sender="ai",
                message=ai_response
            )
            self.db.add(ai_message)
            
            await self.db.commit()
            await self.db.refresh(session)
            
            return {
                "session_id": session.id,
                "response": ai_response
            }
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create chat session: {str(e)}")
            raise

    async def continue_chat_session(
        self,
        session_id: uuid.UUID,
        message: str
    ) -> Dict[str, Any]:
        """Continue an existing chat session"""
        try:
            # Get session with folders
            session = await self._get_chat_session(session_id)
            if not session:
                raise ValueError("Chat session not found")
            
            # Add user message
            user_message = ChatMessage(
                session=session,
                sender="user",
                message=message
            )
            self.db.add(user_message)
            
            # Get folders
            folders = []
            for folder_id in session.folder_ids:
                folder = await self.storage_service.get_folder(folder_id)
                if folder:
                    folders.append(folder)
            
            # Generate AI response
            ai_response = await self._generate_response(session_id, folders, message)
            ai_message = ChatMessage(
                session=session,
                sender="ai",
                message=ai_response
            )
            self.db.add(ai_message)
            
            # Update session
            session.updated_at = datetime.utcnow()
            
            await self.db.commit()
            
            return {
                "response": ai_response
            }
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to continue chat session: {str(e)}")
            raise

    async def get_chat_history(
        self,
        session_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Get chat session history"""
        try:
            # Get session with messages
            session = await self._get_chat_session(session_id)
            if not session:
                raise ValueError("Chat session not found")
            
            # Format messages
            messages = [
                {
                    "sender": msg.sender,
                    "message": msg.message,
                    "timestamp": msg.timestamp
                }
                for msg in sorted(session.messages, key=lambda x: x.timestamp)
            ]
            
            return {
                "messages": messages
            }
        except Exception as e:
            logger.error(f"Failed to get chat history: {str(e)}")
            raise

    async def _get_chat_session(self, session_id: uuid.UUID) -> Optional[ChatSession]:
        """Get chat session with messages"""
        query = (
            select(ChatSession)
            .options(joinedload(ChatSession.messages))
            .where(ChatSession.id == session_id)
        )
        result = await self.db.execute(query)
        return result.unique().scalar_one_or_none()

    async def _generate_response(
        self,
        session_id: uuid.UUID,
        folders: List[Folder],
        message: str
    ) -> str:
        """Generate AI response based on context and message"""
        try:
            # TODO: Implement actual AI response generation
            # For now, return a placeholder response
            folder_names = [folder.name for folder in folders]
            return f"I understand you're asking about folders: {', '.join(folder_names)}. Here's what I found..."
        except Exception as e:
            logger.error(f"Failed to generate response: {str(e)}")
            raise
