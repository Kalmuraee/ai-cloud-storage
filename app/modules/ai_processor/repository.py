from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repository import BaseRepository
from app.modules.ai_processor.models import ProcessingTask, ProcessingResult


class AIProcessorRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def create_processing_task(self, task: ProcessingTask) -> ProcessingTask:
        """Create a new AI processing task."""
        self.session.add(task)
        await self.session.flush()
        return task

    async def get_task_by_id(self, task_id: str) -> Optional[ProcessingTask]:
        """Get a task by its ID."""
        query = select(ProcessingTask).where(ProcessingTask.id == task_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_tasks_by_file_id(self, file_id: str) -> List[ProcessingTask]:
        """Get all tasks associated with a file ID."""
        query = select(ProcessingTask).where(ProcessingTask.file_id == file_id)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def create_processing_result(self, result: ProcessingResult) -> ProcessingResult:
        """Create a new AI processing result."""
        self.session.add(result)
        await self.session.flush()
        return result

    async def get_result_by_task_id(self, task_id: str) -> Optional[ProcessingResult]:
        """Get a processing result by its task ID."""
        query = select(ProcessingResult).where(ProcessingResult.task_id == task_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update_task_status(self, task: ProcessingTask, status: str) -> ProcessingTask:
        """Update the status of a processing task."""
        task.status = status
        await self.session.flush()
        return task
