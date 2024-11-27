"""
Task processor for handling AI processing tasks
"""
from typing import Optional
from datetime import datetime

from app.core.logging import get_logger
from app.core.events import event_bus
from app.modules.ai_processor.models import ProcessingTask, ProcessingStatus
from app.modules.ai_processor.repository import AIProcessorRepository
from app.modules.ai_processor.retry_handler import RetryHandler
from app.modules.ai_processor.ai_engine import AIEngine
from app.modules.storage.repository import StorageRepository

logger = get_logger(__name__)

class TaskProcessor:
    """Processor for AI processing tasks"""
    
    def __init__(
        self,
        repo: AIProcessorRepository,
        retry_handler: RetryHandler,
        storage_repo: Optional[StorageRepository] = None
    ):
        self.repo = repo
        self.retry_handler = retry_handler
        self.storage_repo = storage_repo or StorageRepository()
        self.ai_engine = AIEngine()

    async def process_task(self, task: ProcessingTask) -> None:
        """
        Process a single task
        
        Args:
            task: Task to process
        """
        try:
            # Update task status
            task.status = ProcessingStatus.PROCESSING
            task.started_at = datetime.utcnow()
            await self.repo.update_task_status(task, ProcessingStatus.PROCESSING)
            
            # Get file
            file = await self.storage_repo.get_file_by_id(task.file_id)
            if not file:
                raise ValueError(f"File {task.file_id} not found")
            
            # Process based on task type
            result = None
            if task.task_type == "analyze_content":
                result = await self.ai_engine.analyze_content(file)
            elif task.task_type == "extract_metadata":
                result = await self.ai_engine.extract_metadata(file)
            else:
                raise ValueError(f"Unknown task type: {task.task_type}")
                
            # Check result
            if not result or result.get('error'):
                raise ProcessingError(
                    result.get('error', 'Processing failed with no error details')
                )
                
            # Update task with result
            task.result = result
            task.confidence_score = result.get('confidence', 0.0)
            task.status = ProcessingStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            await self.repo.update_task(task)
            
            # Publish completion event
            await event_bus.publish(
                "task_completed",
                {
                    "task_id": task.id,
                    "file_id": task.file_id,
                    "task_type": task.task_type,
                    "confidence": task.confidence_score
                }
            )
            
        except Exception as e:
            logger.error(f"Task processing failed: {str(e)}")
            
            # Check if we should retry
            should_retry = await self.retry_handler.should_retry(task)
            
            if should_retry:
                # Update for retry
                task.status = ProcessingStatus.RETRYING
                task.retry_count += 1
                task.last_retry_at = datetime.utcnow()
                task.error_message = str(e)
                await self.repo.update_task(task)
                
                # Schedule retry
                retry_delay = self.retry_handler.get_retry_delay(task)
                await event_bus.publish(
                    "task_retry",
                    {
                        "task_id": task.id,
                        "retry_count": task.retry_count,
                        "delay_ms": retry_delay
                    },
                    delay_ms=retry_delay
                )
            else:
                # Mark as failed
                task.status = ProcessingStatus.FAILED
                task.error_message = str(e)
                task.completed_at = datetime.utcnow()
                await self.repo.update_task(task)
                
                # Publish failure event
                await event_bus.publish(
                    "task_failed",
                    {
                        "task_id": task.id,
                        "file_id": task.file_id,
                        "error": str(e),
                        "retry_count": task.retry_count
                    }
                )
