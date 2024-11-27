"""
Health check endpoints and utilities.
"""
from datetime import datetime
from typing import Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import logger

router = APIRouter(tags=["health"])

async def check_database(db: AsyncSession) -> Dict[str, str]:
    """Check database connection."""
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "healthy", "message": "Database connection is healthy"}
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return {"status": "unhealthy", "message": f"Database connection failed: {str(e)}"}

@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)) -> Dict[str, any]:
    """
    Health check endpoint that verifies all system components.
    
    Returns:
        Dict with health status of all components and overall system health.
    """
    start_time = datetime.utcnow()
    
    # Check all components
    checks: List[Dict[str, str]] = []
    
    # Database check
    db_status = await check_database(db)
    checks.append({"name": "database", **db_status})
    
    # Determine overall health
    is_healthy = all(check["status"] == "healthy" for check in checks)
    
    # Calculate response time
    response_time = (datetime.utcnow() - start_time).total_seconds()
    
    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks,
        "response_time": f"{response_time:.3f}s"
    }

@router.get("/health/live")
async def liveness_probe() -> Dict[str, str]:
    """
    Kubernetes liveness probe endpoint.
    
    Returns:
        Dict with basic health status.
    """
    return {"status": "alive"}

@router.get("/health/ready")
async def readiness_probe(db: AsyncSession = Depends(get_db)) -> Dict[str, str]:
    """
    Kubernetes readiness probe endpoint.
    
    Returns:
        Dict with readiness status.
    """
    # Check database
    db_status = await check_database(db)
    
    if db_status["status"] == "healthy":
        return {"status": "ready"}
    else:
        return {"status": "not ready", "message": db_status["message"]}
