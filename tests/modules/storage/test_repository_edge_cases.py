"""
Test edge cases for storage repository.
"""
import pytest
from datetime import datetime

from app.core.exceptions import ValidationError, DatabaseError, NotFoundException
from app.modules.storage.repository import StorageRepository
from app.modules.storage.models import File, FileStatus
from app.modules.storage.schemas import FileCreate, FileUpdate, FileMetadataCreate
from app.modules.auth.models import User

@pytest.mark.asyncio
async def test_create_file_with_invalid_data(storage_repo: StorageRepository):
    """Test file creation with invalid data."""
    # Test with None data
    with pytest.raises(ValidationError):
        await storage_repo.create_file(None)

    # Test with missing required fields
    invalid_file_data = FileCreate(
        filename=None,  # Required field
        original_filename="test.txt",
        path="/test/test.txt",
        size=12,
        content_type="text/plain",
        bucket="test-bucket",
        owner_id=1,
        status=FileStatus.PROCESSED
    )
    with pytest.raises(ValidationError):
        await storage_repo.create_file(invalid_file_data)

@pytest.mark.asyncio
async def test_update_file_with_invalid_data(storage_repo: StorageRepository, test_file: File):
    """Test file update with invalid data."""
    # Test with None file_id
    with pytest.raises(ValidationError):
        await storage_repo.update_file(None, FileUpdate(filename="new.txt"))

    # Test with non-existent file
    with pytest.raises(NotFoundException):
        await storage_repo.update_file(9999, FileUpdate(filename="new.txt"))

    # Test with deleted file
    test_file.status = FileStatus.DELETED
    storage_repo.db.add(test_file)
    await storage_repo.db.commit()

    with pytest.raises(NotFoundException):
        await storage_repo.update_file(test_file.id, FileUpdate(filename="new.txt"))

@pytest.mark.asyncio
async def test_delete_file_edge_cases(storage_repo: StorageRepository, test_file: File):
    """Test file deletion edge cases."""
    # Test with None file_id
    with pytest.raises(ValidationError):
        await storage_repo.delete_file(None)

    # Test with non-existent file
    with pytest.raises(NotFoundException):
        await storage_repo.delete_file(9999)

    # Test deleting already deleted file
    test_file.status = FileStatus.DELETED
    storage_repo.db.add(test_file)
    await storage_repo.db.commit()

    # Should not raise an error
    await storage_repo.delete_file(test_file.id)

    # Verify file remains deleted
    file = await storage_repo.get_file_by_id(test_file.id)
    assert file.status == FileStatus.DELETED

@pytest.mark.asyncio
async def test_shared_item_operations_edge_cases(storage_repo: StorageRepository, test_file: File):
    """Test shared item operations edge cases."""
    # Test create shared item with invalid data
    with pytest.raises(ValidationError):
        await storage_repo.create_shared_item(
            file_id=None,
            folder_id=None,
            owner_id=1,
            shared_with_id=2
        )

    # Test create shared item with non-existent file
    with pytest.raises(DatabaseError):
        await storage_repo.create_shared_item(
            file_id=9999,
            owner_id=1,
            shared_with_id=2
        )

    # Test delete non-existent shared item
    with pytest.raises(ValidationError):
        await storage_repo.delete_shared_item(None)

@pytest.mark.asyncio
async def test_file_metadata_operations_edge_cases(storage_repo: StorageRepository, test_file: File):
    """Test file metadata operations edge cases."""
    # Test create metadata with invalid file_id
    with pytest.raises(DatabaseError):
        await storage_repo.create_file_metadata(FileMetadataCreate(
            file_id=9999,
            content_hash="test_hash"
        ))

    # Test delete metadata with None file_id
    with pytest.raises(ValidationError):
        await storage_repo.delete_file_metadata(None)

    # Test create duplicate metadata
    metadata = FileMetadataCreate(
        file_id=test_file.id,
        content_hash="test_hash"
    )
    await storage_repo.create_file_metadata(metadata)

    # Attempting to create duplicate should raise error
    with pytest.raises(DatabaseError):
        await storage_repo.create_file_metadata(metadata)

@pytest.mark.asyncio
async def test_get_file_by_path_edge_cases(storage_repo: StorageRepository, test_user: User):
    """Test get_file_by_path edge cases."""
    # Test with empty path
    with pytest.raises(ValidationError):
        await storage_repo.get_file_by_path("", test_user.id)

    # Test with None owner_id
    with pytest.raises(ValidationError):
        await storage_repo.get_file_by_path("/test/test.txt", None)

    # Test with non-existent path
    file = await storage_repo.get_file_by_path("/nonexistent/path", test_user.id)
    assert file is None

@pytest.mark.asyncio
async def test_list_files_by_user_edge_cases(storage_repo: StorageRepository, test_user: User):
    """Test list_files_by_user edge cases."""
    # Test with None owner_id
    with pytest.raises(ValidationError):
        await storage_repo.list_files_by_user(None)

    # Test with invalid pagination values
    files, total = await storage_repo.list_files_by_user(test_user.id, limit=-1, offset=-1)
    assert len(files) == 0
    assert total == 0

    # Test with very large offset
    files, total = await storage_repo.list_files_by_user(test_user.id, offset=999999)
    assert len(files) == 0

@pytest.mark.asyncio
async def test_get_storage_usage_edge_cases(storage_repo: StorageRepository, test_user: User):
    """Test get_storage_usage edge cases."""
    # Test with non-existent user
    usage = await storage_repo.get_storage_usage(9999)
    assert usage["total_size"] == 0
    assert usage["file_count"] == 0
    assert len(usage["type_distribution"]) == 0

    # Test with user having only deleted files
    test_file = File(
        filename="test.txt",
        original_filename="test.txt",
        path="/test/test.txt",
        size=100,
        content_type="text/plain",
        bucket="test-bucket",
        owner_id=test_user.id,
        status=FileStatus.DELETED,
        version=1,
        is_latest=True,
        created_at=datetime.now()
    )
    storage_repo.db.add(test_file)
    await storage_repo.db.commit()

    usage = await storage_repo.get_storage_usage(test_user.id)
    assert usage["total_size"] == 0  # Should not count deleted files
