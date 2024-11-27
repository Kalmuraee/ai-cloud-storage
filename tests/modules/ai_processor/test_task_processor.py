"""Tests for Task Processor"""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

from app.modules.ai_processor.task_processor import TaskProcessor
from app.modules.ai_processor.models import ProcessingTask, ProcessingStatus
from app.modules.storage.models import File

@pytest.fixture
def mock_repo():
    return Mock(
        update_task_status=AsyncMock(),
        update_task=AsyncMock(),
        get_task_by_id=AsyncMock()
    )

@pytest.fixture
def mock_retry_handler():
    return Mock(
        should_retry=AsyncMock(),
        get_retry_delay=Mock(return_value=1000)
    )

@pytest.fixture
def mock_storage_repo():
    return Mock(get_file_by_id=AsyncMock())

@pytest.fixture
def mock_ai_engine():
    return Mock(
        analyze_content=AsyncMock(),
        extract_metadata=AsyncMock()
    )

@pytest.fixture
def processor(mock_repo, mock_retry_handler, mock_storage_repo):
    processor = TaskProcessor(mock_repo, mock_retry_handler, mock_storage_repo)
    processor.ai_engine = Mock(
        analyze_content=AsyncMock(),
        extract_metadata=AsyncMock()
    )
    return processor

@pytest.fixture
def task():
    return ProcessingTask(
        id=1,
        file_id=1,
        task_type="analyze_content",
        status=ProcessingStatus.QUEUED,
        retry_count=0
    )

@pytest.fixture
def file():
    return File(
        id=1,
        bucket="test-bucket",
        path="test.txt",
        size=100,
        content_type="text/plain"
    )

@pytest.mark.asyncio
async def test_successful_processing(processor, task, file):
    # Setup
    processor.storage_repo.get_file_by_id.return_value = file
    processor.ai_engine.analyze_content.return_value = {
        "content_type": "text",
        "summary": "Test summary",
        "confidence": 0.9
    }
    
    # Execute
    await processor.process_task(task)
    
    # Verify
    assert processor.repo.update_task_status.call_count == 1
    assert processor.repo.update_task.call_count == 1
    assert task.status == ProcessingStatus.COMPLETED
    assert task.confidence_score == 0.9
    assert task.completed_at is not None

@pytest.mark.asyncio
async def test_retry_on_failure(processor, task, file):
    # Setup
    processor.storage_repo.get_file_by_id.return_value = file
    processor.ai_engine.analyze_content.side_effect = Exception("Test error")
    processor.retry_handler.should_retry.return_value = True
    
    # Execute
    await processor.process_task(task)
    
    # Verify
    assert task.status == ProcessingStatus.RETRYING
    assert task.retry_count == 1
    assert task.last_retry_at is not None
    assert task.error_message == "Test error"
    assert processor.repo.update_task.call_count == 1

@pytest.mark.asyncio
async def test_failure_without_retry(processor, task, file):
    # Setup
    processor.storage_repo.get_file_by_id.return_value = file
    processor.ai_engine.analyze_content.side_effect = Exception("Test error")
    processor.retry_handler.should_retry.return_value = False
    
    # Execute
    await processor.process_task(task)
    
    # Verify
    assert task.status == ProcessingStatus.FAILED
    assert task.error_message == "Test error"
    assert task.completed_at is not None
    assert processor.repo.update_task.call_count == 1

@pytest.mark.asyncio
async def test_file_not_found(processor, task):
    # Setup
    processor.storage_repo.get_file_by_id.return_value = None
    processor.retry_handler.should_retry.return_value = True
    
    # Execute
    await processor.process_task(task)
    
    # Verify
    assert task.status == ProcessingStatus.RETRYING
    assert "File 1 not found" in task.error_message
    assert processor.repo.update_task.call_count == 1

@pytest.mark.asyncio
async def test_invalid_task_type(processor, task, file):
    # Setup
    task.task_type = "invalid_type"
    processor.storage_repo.get_file_by_id.return_value = file
    processor.retry_handler.should_retry.return_value = False
    
    # Execute
    await processor.process_task(task)
    
    # Verify
    assert task.status == ProcessingStatus.FAILED
    assert "Unknown task type" in task.error_message
    assert processor.repo.update_task.call_count == 1

@pytest.mark.asyncio
async def test_metadata_extraction(processor, task, file):
    # Setup
    task.task_type = "extract_metadata"
    processor.storage_repo.get_file_by_id.return_value = file
    processor.ai_engine.extract_metadata.return_value = {
        "technical": {"size": 100},
        "content": {"type": "text"},
        "confidence": 0.95
    }
    
    # Execute
    await processor.process_task(task)
    
    # Verify
    assert processor.ai_engine.extract_metadata.call_count == 1
    assert task.status == ProcessingStatus.COMPLETED
    assert task.confidence_score == 0.95
    assert task.completed_at is not None
