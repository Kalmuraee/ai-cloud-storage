"""
Storage module folder management routes
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import get_logger
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.storage.models import Folder, File
from app.modules.storage.schemas import (
    FolderCreate,
    FolderUpdate,
    FolderResponse,
    MoveItemRequest
)
from app.modules.storage.service import StorageService

router = APIRouter()
logger = get_logger(__name__)

@router.post("/folders", response_model=FolderResponse, tags=["Folders"])
async def create_folder(
    folder: FolderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new folder.
    
    - **name**: Folder name
    - **parent_id**: Optional parent folder ID
    """
    try:
        storage_service = StorageService(db)
        
        # Verify parent folder if provided
        if folder.parent_id:
            parent = await storage_service.get_folder(folder.parent_id)
            if not parent or parent.owner_id != current_user.id:
                raise HTTPException(status_code=404, detail="Parent folder not found")
        
        # Create the folder
        new_folder = await storage_service.create_folder(
            name=folder.name,
            owner_id=current_user.id,
            parent_id=folder.parent_id
        )
        
        return new_folder
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create folder: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/folders", response_model=List[FolderResponse], tags=["Folders"])
async def list_folders(
    parent_id: Optional[int] = Query(None, description="Parent folder ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all folders or folders within a specific parent.
    
    - **parent_id**: Optional parent folder ID to list contents
    """
    try:
        storage_service = StorageService(db)
        
        # Verify parent folder if provided
        if parent_id:
            parent = await storage_service.get_folder(parent_id)
            if not parent or parent.owner_id != current_user.id:
                raise HTTPException(status_code=404, detail="Parent folder not found")
        
        return await storage_service.list_folders(current_user.id, parent_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list folders: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/folders/{folder_id}", response_model=FolderResponse, tags=["Folders"])
async def get_folder(
    folder_id: int = Path(..., description="Folder ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve details of a specific folder.
    
    - **folder_id**: ID of the folder to retrieve
    """
    try:
        storage_service = StorageService(db)
        folder = await storage_service.get_folder(folder_id)
        
        if not folder or folder.owner_id != current_user.id:
            raise HTTPException(status_code=404, detail="Folder not found")
        
        return folder
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get folder: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/folders/{folder_id}", response_model=FolderResponse, tags=["Folders"])
async def update_folder(
    folder_id: int = Path(..., description="Folder ID"),
    folder_update: FolderUpdate = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update folder information.
    
    - **folder_id**: ID of the folder to update
    - **name**: New folder name
    """
    try:
        storage_service = StorageService(db)
        folder = await storage_service.get_folder(folder_id)
        
        if not folder or folder.owner_id != current_user.id:
            raise HTTPException(status_code=404, detail="Folder not found")
        
        updated_folder = await storage_service.update_folder(
            folder_id=folder_id,
            name=folder_update.name
        )
        
        return updated_folder
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update folder: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/folders/{folder_id}", tags=["Folders"])
async def delete_folder(
    folder_id: int = Path(..., description="Folder ID"),
    recursive: bool = Query(False, description="Delete folder contents recursively"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a folder and optionally its contents.
    
    - **folder_id**: ID of the folder to delete
    - **recursive**: If true, delete all contents recursively
    """
    try:
        storage_service = StorageService(db)
        folder = await storage_service.get_folder(folder_id)
        
        if not folder or folder.owner_id != current_user.id:
            raise HTTPException(status_code=404, detail="Folder not found")
        
        await storage_service.delete_folder(folder_id, recursive)
        return {"message": "Folder deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete folder: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/items/{item_id}/move", response_model=FolderResponse, tags=["Folders"])
async def move_item(
    item_id: int = Path(..., description="Item ID (file or folder)"),
    move_request: MoveItemRequest = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Move a file or folder to a new location.
    
    - **item_id**: ID of the item to move
    - **destination_folder_id**: Target folder ID (None for root)
    """
    try:
        storage_service = StorageService(db)
        
        # Check if item exists and user has access
        item = await storage_service.get_folder(item_id)
        if not item:
            item = await storage_service.get_file(item_id)
        
        if not item or item.owner_id != current_user.id:
            raise HTTPException(status_code=404, detail="Item not found")
        
        # Verify destination folder if provided
        if move_request.destination_folder_id:
            dest_folder = await storage_service.get_folder(move_request.destination_folder_id)
            if not dest_folder or dest_folder.owner_id != current_user.id:
                raise HTTPException(status_code=404, detail="Destination folder not found")
        
        # Move the item
        moved_item = await storage_service.move_item(
            item_id=item_id,
            destination_folder_id=move_request.destination_folder_id
        )
        
        return moved_item
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to move item: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
