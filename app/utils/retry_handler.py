"""Retry handler for HTTP requests with configurable retry strategies."""

import asyncio
from functools import wraps
from typing import Any, Callable, Dict, Optional, Type, Union

import structlog
import tenacity
from aiohttp import ClientError, ClientResponse
from tenacity import (
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = structlog.get_logger(__name__)

# Default retry configuration
DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_WAIT_MIN = 1  # seconds
DEFAULT_WAIT_MAX = 10  # seconds
DEFAULT_WAIT_MULTIPLIER = 2


class RetryableError(Exception):
    """Base class for retryable errors."""
    pass


class NonRetryableError(Exception):
    """Base class for non-retryable errors."""
    pass


def is_retryable_error(exception: Exception) -> bool:
    """
    Determine if an exception should trigger a retry.
    
    Args:
        exception: The exception to check.
    
    Returns:
        bool: True if the exception should trigger a retry, False otherwise.
    """
    if isinstance(exception, RetryableError):
        return True
    
    if isinstance(exception, ClientError):
        return True
    
    return False


def create_retry_decorator(
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    wait_min: int = DEFAULT_WAIT_MIN,
    wait_max: int = DEFAULT_WAIT_MAX,
    wait_multiplier: int = DEFAULT_WAIT_MULTIPLIER,
    retry_on_exceptions: Optional[Union[Type[Exception], tuple[Type[Exception], ...]]] = None,
) -> Callable:
    """
    Create a retry decorator with custom configuration.
    
    Args:
        max_attempts: Maximum number of retry attempts.
        wait_min: Minimum wait time between retries in seconds.
        wait_max: Maximum wait time between retries in seconds.
        wait_multiplier: Multiplier for wait time between retries.
        retry_on_exceptions: Exception types that should trigger a retry.
        
    Returns:
        Callable: A retry decorator configured with the specified parameters.
    """
    if retry_on_exceptions is None:
        retry_on_exceptions = (RetryableError, ClientError)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            retry = tenacity.AsyncRetrying(
                stop=stop_after_attempt(max_attempts),
                wait=wait_exponential(
                    multiplier=wait_multiplier,
                    min=wait_min,
                    max=wait_max
                ),
                retry=retry_if_exception_type(retry_on_exceptions),
                before_sleep=lambda retry_state: logger.warning(
                    "Retrying request",
                    attempt=retry_state.attempt_number,
                    wait_time=retry_state.next_action.sleep,
                    exception=retry_state.outcome.exception(),
                ),
            )
            
            try:
                async for attempt in retry:
                    with attempt:
                        result = await func(*args, **kwargs)
                        
                        # If the result is a ClientResponse, check its status
                        if isinstance(result, ClientResponse):
                            status = result.status
                            if status >= 500:
                                raise RetryableError(f"Server error: {status}")
                            elif status >= 400:
                                raise NonRetryableError(f"Client error: {status}")
                        
                        return result
                        
            except tenacity.RetryError as e:
                logger.error(
                    "Max retry attempts reached",
                    max_attempts=max_attempts,
                    last_exception=str(e.last_attempt.exception()),
                )
                raise
                
        return wrapper
    
    return decorator


# Default retry decorator with standard configuration
retry_request = create_retry_decorator()
