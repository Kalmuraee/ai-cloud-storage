"""
AI Processor service for handling file analysis and processing
"""
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.core.logging import get_logger
from app.core.events import event_bus
from app.core.exceptions import ProcessingError
from app.modules.ai_processor.repository import AIProcessorRepository
from app.modules.ai_processor.models import ProcessingTask, ProcessingStatus
from app.modules.ai_processor.retry_handler import RetryHandler
from app.modules.ai_processor.task_processor import TaskProcessor
from app.modules.ai_processor.schemas import (
    TaskCreate,
    TaskUpdate,
    ProcessingResult
)

logger = get_logger(__name__)

class AIProcessorService:
    """Service for handling AI processing tasks"""
    
    def __init__(self, repo: AIProcessorRepository):
        self.repo = repo
        self.retry_handler = RetryHandler()
        self.task_processor = TaskProcessor(repo, self.retry_handler)
        # Subscribe to file events
        event_bus.subscribe("file_uploaded", self.handle_file_uploaded)
        event_bus.subscribe("task_retry", self.handle_task_retry)

    async def handle_file_uploaded(self, data: Dict[str, Any]) -> None:
        """
        Handle file uploaded event
        
        Args:
            data: Event data containing file_id and tasks
        """
        try:
            file_id = data["file_id"]
            tasks = data.get("tasks", ["analyze_content", "extract_metadata"])
            batch_id = data.get("batch_id")
            await self.process_file(file_id, tasks, batch_id)
        except Exception as e:
            logger.error(f"Failed to handle file uploaded event: {str(e)}")

    async def handle_task_retry(self, data: Dict[str, Any]) -> None:
        """
        Handle task retry event
        
        Args:
            data: Event data containing task_id
        """
        try:
            task_id = data["task_id"]
            task = await self.repo.get_task_by_id(task_id)
            
            if task:
                await self.task_processor.process_task(task)
            else:
                logger.error(f"Task {task_id} not found for retry")
                
        except Exception as e:
            logger.error(f"Failed to handle task retry event: {str(e)}")

    async def process_file(
        self,
        file_id: int,
        tasks: List[str],
        batch_id: Optional[str] = None
    ) -> List[ProcessingTask]:
        """
        Process a file with specified tasks
        
        Args:
            file_id: ID of the file to process
            tasks: List of task types to perform
            batch_id: Optional batch ID for grouped processing
            
        Returns:
            List[ProcessingTask]: Created processing tasks
        """
        processing_tasks = []
        
        try:
            for task_type in tasks:
                task = ProcessingTask(
                    file_id=file_id,
                    task_type=task_type,
                    status=ProcessingStatus.QUEUED,
                    params={
                        "batch_id": batch_id
                    } if batch_id else {},
                    retry_count=0
                )
                created_task = await self.repo.create_processing_task(task)
                processing_tasks.append(created_task)
                
                # Process task asynchronously
                await event_bus.publish(
                    "task_queued",
                    {
                        "task_id": created_task.id,
                        "task_type": task_type,
                        "file_id": file_id,
                        "batch_id": batch_id
                    }
                )
                
        except Exception as e:
            logger.error(f"Failed to queue processing task: {str(e)}")
            raise ProcessingError(f"Failed to queue processing task: {str(e)}")
            
        return processing_tasks

    async def get_task_status(self, task_id: int) -> Optional[ProcessingTask]:
        """Get status of a processing task"""
        return await self.repo.get_task_by_id(task_id)

    async def get_file_tasks(self, file_id: int) -> List[ProcessingTask]:
        """Get all tasks for a file"""
        return await self.repo.get_tasks_by_file_id(file_id)

    async def get_batch_tasks(self, batch_id: str) -> List[ProcessingTask]:
        """Get all tasks in a batch"""
        return await self.repo.get_tasks_by_batch_id(batch_id)

    async def cancel_task(self, task_id: int) -> bool:
        """Cancel a processing task if possible"""
        task = await self.repo.get_task_by_id(task_id)
        if task and task.status in [ProcessingStatus.QUEUED, ProcessingStatus.RETRYING]:
            task.status = ProcessingStatus.FAILED
            task.error_message = "Task cancelled by user"
            await self.repo.update_task_status(task, ProcessingStatus.FAILED)
            return True
        return False
