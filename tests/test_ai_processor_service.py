"""
Test AI processor service
"""
import pytest
from unittest.mock import Mock
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai_processor.service import AIProcessorService
from app.modules.ai_processor.models import ProcessingTask, ProcessingResult
from app.modules.storage.models import File

@pytest.fixture
def ai_processor_service():
    return AIProcessorService()

@pytest.fixture
def mock_db():
    db = Mock(spec=AsyncSession)
    db.commit = Mock()
    db.refresh = Mock()
    return db

@pytest.fixture
def mock_file():
    return File(
        id="test-file-id",
        filename="test.txt",
        path="test/test.txt",
        size=100,
        content_type="text/plain"
    )

@pytest.mark.asyncio
async def test_process_file(ai_processor_service, mock_file, mock_db):
    # Start processing
    task = await ai_processor_service.process_file(
        file=mock_file,
        task_type="classify",
        params={"model": "test-model"},
        db=mock_db
    )
    
    assert task.file_id == mock_file.id
    assert task.task_type == "classify"
    assert task.status == "pending"
    assert task.params == {"model": "test-model"}

@pytest.mark.asyncio
async def test_get_task_status(ai_processor_service, mock_db):
    # Create mock task
    task = ProcessingTask(
        id="test-task-id",
        file_id="test-file-id",
        task_type="classify",
        status="completed"
    )
    mock_db.get = Mock(return_value=task)
    
    # Get status
    status = await ai_processor_service.get_task_status(
        task_id="test-task-id",
        db=mock_db
    )
    
    assert status["status"] == "completed"
    assert status["task_type"] == "classify"

@pytest.mark.asyncio
async def test_cancel_task(ai_processor_service, mock_db):
    # Create mock task
    task = ProcessingTask(
        id="test-task-id",
        file_id="test-file-id",
        task_type="classify",
        status="processing"
    )
    mock_db.get = Mock(return_value=task)
    
    # Cancel task
    await ai_processor_service.cancel_task(
        task_id="test-task-id",
        db=mock_db
    )
    
    assert task.status == "cancelled"
