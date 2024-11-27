"""
Custom middleware for the application.
"""
import time
from typing import Callable
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.types import ASGIApp

from app.core.config import settings
from app.core.logging import logger

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request and log details."""
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            process_time = time.time() - start_time
            logger.info(
                f"Path: {request.url.path} "
                f"Method: {request.method} "
                f"Status: {response.status_code} "
                f"Duration: {process_time:.3f}s"
            )
            
            return response
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Path: {request.url.path} "
                f"Method: {request.method} "
                f"Error: {str(e)} "
                f"Duration: {process_time:.3f}s"
            )
            raise

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware."""
    
    def __init__(self, app: ASGIApp, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request and apply rate limiting."""
        client_ip = request.client.host
        current_time = time.time()
        
        # Clean old requests
        self.requests = {
            ip: times for ip, times in self.requests.items()
            if current_time - times[-1] < self.window_seconds
        }
        
        # Check rate limit
        if client_ip in self.requests:
            times = self.requests[client_ip]
            if len(times) >= self.max_requests:
                return Response(
                    content="Rate limit exceeded",
                    status_code=429
                )
            times.append(current_time)
        else:
            self.requests[client_ip] = [current_time]
        
        return await call_next(request)

def setup_middleware(app: FastAPI) -> None:
    """Setup middleware for the application."""
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Request logging
    app.add_middleware(RequestLoggingMiddleware)
    
    # Rate limiting
    if settings.ENABLE_RATE_LIMIT:
        app.add_middleware(
            RateLimitMiddleware,
            max_requests=settings.RATE_LIMIT_MAX_REQUESTS,
            window_seconds=settings.RATE_LIMIT_WINDOW_SECONDS,
        )
