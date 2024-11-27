"""
Retry handler for AI processing tasks with advanced retry strategies
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import random
from app.core.logging import get_logger
from app.core.events import event_bus
from app.modules.ai_processor.models import ProcessingStatus, ProcessingTask

logger = get_logger(__name__)

class RetryStrategy:
    """Base class for retry strategies"""
    
    def calculate_delay(self, retry_count: int) -> float:
        """Calculate delay in seconds for next retry"""
        raise NotImplementedError

class ExponentialBackoff(RetryStrategy):
    """Exponential backoff with jitter"""
    
    def __init__(self, base_delay: float = 1.0, max_delay: float = 300.0, jitter: float = 0.1):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.jitter = jitter
        
    def calculate_delay(self, retry_count: int) -> float:
        delay = min(self.base_delay * (2 ** retry_count), self.max_delay)
        jitter_amount = delay * self.jitter
        return delay + random.uniform(-jitter_amount, jitter_amount)

class LinearBackoff(RetryStrategy):
    """Linear backoff with optional jitter"""
    
    def __init__(self, base_delay: float = 5.0, increment: float = 5.0, jitter: float = 0.1):
        self.base_delay = base_delay
        self.increment = increment
        self.jitter = jitter
        
    def calculate_delay(self, retry_count: int) -> float:
        delay = self.base_delay + (self.increment * retry_count)
        jitter_amount = delay * self.jitter
        return delay + random.uniform(-jitter_amount, jitter_amount)

class RetryHandler:
    """Handles retrying of failed processing tasks with advanced strategies"""
    
    def __init__(
        self,
        max_retries: int = 3,
        strategy: RetryStrategy = None,
        max_retry_window: timedelta = timedelta(hours=24)
    ):
        self.max_retries = max_retries
        self.strategy = strategy or ExponentialBackoff()
        self.max_retry_window = max_retry_window
        
        # Error classification
        self.permanent_errors = {
            "permission denied": "Access permission issues",
            "not found": "Resource not found",
            "invalid format": "Invalid input format",
            "quota exceeded": "Resource quota exceeded",
            "invalid credentials": "Authentication failed"
        }
        
        # Retry-specific errors
        self.retriable_errors = {
            "timeout": "Request timeout",
            "rate limit": "Rate limit exceeded",
            "connection reset": "Connection issues",
            "service unavailable": "Temporary service outage",
            "internal server error": "Server error"
        }
        
    def _classify_error(self, error: str) -> Dict[str, Any]:
        """Classify the error and determine retry strategy"""
        error_lower = error.lower()
        
        # Check for permanent errors
        for key, description in self.permanent_errors.items():
            if key in error_lower:
                return {
                    "retriable": False,
                    "reason": description,
                    "error_type": "permanent"
                }
                
        # Check for retriable errors
        for key, description in self.retriable_errors.items():
            if key in error_lower:
                return {
                    "retriable": True,
                    "reason": description,
                    "error_type": "transient"
                }
                
        # Default to retriable for unknown errors
        return {
            "retriable": True,
            "reason": "Unknown error",
            "error_type": "unknown"
        }
        
    def _is_within_retry_window(self, task: ProcessingTask) -> bool:
        """Check if the task is within the allowed retry window"""
        if not task.created_at:
            return True
            
        time_since_creation = datetime.utcnow() - task.created_at
        return time_since_creation <= self.max_retry_window
        
    async def handle_failure(self, task: ProcessingTask, error: Optional[str] = None) -> bool:
        """
        Handle task failure and determine if it should be retried
        
        Args:
            task: The failed task
            error: Optional error message
            
        Returns:
            bool: True if task was queued for retry, False otherwise
        """
        try:
            # Check retry conditions
            if not self.should_retry(task, error):
                logger.error(
                    f"Task {task.id} failed permanently: retry_count={task.retry_count}, "
                    f"error='{error}'"
                )
                return False
                
            # Increment retry count and update task state
            task.retry_count += 1
            task.last_retry_at = datetime.utcnow()
            task.status = ProcessingStatus.RETRYING
            task.error_message = error
            
            # Calculate backoff time using strategy
            backoff = self.strategy.calculate_delay(task.retry_count)
            
            # Classify error for logging
            error_info = self._classify_error(error) if error else {
                "error_type": "unknown",
                "reason": "No error information"
            }
            
            # Queue retry event
            await event_bus.publish(
                "task_retry",
                {
                    "task_id": task.id,
                    "retry_count": task.retry_count,
                    "error": error,
                    "error_type": error_info["error_type"],
                    "reason": error_info["reason"],
                    "backoff": backoff
                },
                delay_seconds=backoff
            )
            
            logger.info(
                f"Task {task.id} queued for retry {task.retry_count}/{self.max_retries} "
                f"with {backoff:.2f}s backoff. Error type: {error_info['error_type']}, "
                f"Reason: {error_info['reason']}"
            )
            return True
            
        except Exception as e:
            logger.error(
                f"Failed to handle retry for task {task.id}: {str(e)}",
                exc_info=True
            )
            return False
            
    def should_retry(self, task: ProcessingTask, error: Optional[str] = None) -> bool:
        """
        Determine if a task should be retried based on its state and error
        
        Args:
            task: The failed task
            error: Optional error message
            
        Returns:
            bool: True if task should be retried
        """
        # Check retry count
        if task.retry_count >= self.max_retries:
            logger.info(f"Task {task.id} exceeded max retries ({self.max_retries})")
            return False
            
        # Check retry window
        if not self._is_within_retry_window(task):
            logger.info(f"Task {task.id} exceeded retry window ({self.max_retry_window})")
            return False
            
        # Check error classification
        if error:
            error_info = self._classify_error(error)
            if not error_info["retriable"]:
                logger.info(
                    f"Task {task.id} has non-retriable error: {error_info['reason']}"
                )
                return False
                
        return True
