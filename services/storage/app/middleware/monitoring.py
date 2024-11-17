import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.services.monitoring import monitoring_service

class MonitoringMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Start timer
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Record metrics
        await monitoring_service.record_request(
            method=request.method,
            endpoint=request.url.path,
            duration=duration,
            status=response.status_code
        )
        
        return response