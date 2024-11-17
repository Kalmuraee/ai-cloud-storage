from typing import Dict, List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from app.services.monitoring import monitoring_service
from app.services.backup import backup_service
from app.services.quota import quota_service
from app.api import deps

router = APIRouter()

@router.get("/health", response_model=Dict)
async def get_health():
    """
    Get system health status.
    """
    return await monitoring_service.get_system_health()

@router.get("/metrics")
async def get_metrics():
    """
    Get system metrics in Prometheus format.
    """
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from fastapi.responses import Response
    
    return Response(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

@router.post("/backups", response_model=Dict)
async def create_backup(
    background_tasks: BackgroundTasks,
    bucket_name: str = None,
    current_user = Depends(deps.get_current_superuser)
):
    """
    Create a new backup.
    """
    # Run backup in background
    background_tasks.add_task(backup_service.create_backup, bucket_name)
    return {"message": "Backup started"}

@router.get("/backups", response_model=List[Dict])
async def list_backups(
    current_user = Depends(deps.get_current_superuser)
):
    """
    List all backups.
    """
    return await backup_service.list_backups()

@router.post("/backups/{backup_id}/restore")
async def restore_backup(
    backup_id: str,
    bucket_name: str = None,
    current_user = Depends(deps.get_current_superuser)
):
    """
    Restore from a backup.
    """
    await backup_service.restore_backup(backup_id, bucket_name)
    return {"message": "Restore completed"}

@router.get("/quotas", response_model=Dict[str, Dict])
async def get_all_quotas(
    current_user = Depends(deps.get_current_superuser)
):
    """
    Get quota information for all users.
    """
    return await quota_service.get_all_quotas()

@router.get("/quotas/{user_id}", response_model=Dict)
async def get_user_quota(
    user_id: int,
    current_user = Depends(deps.get_current_user)
):
    """
    Get quota information for a user.
    """
    if current_user.id != user_id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return await quota_service.get_quota(user_id)

@router.put("/quotas/{user_id}")
async def set_user_quota(
    user_id: int,
    quota_bytes: int,
    current_user = Depends(deps.get_current_superuser)
):
    """
    Set quota for a user.
    """
    await quota_service.set_quota(user_id, quota_bytes)
    return {"message": "Quota updated"}

@router.post("/quotas/{user_id}/recalculate")
async def recalculate_quota(
    user_id: int,
    current_user = Depends(deps.get_current_superuser)
):
    """
    Recalculate storage usage for a user.
    """
    await quota_service.recalculate_usage(user_id)
    return {"message": "Usage recalculated"}