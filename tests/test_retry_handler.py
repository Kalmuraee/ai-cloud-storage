"""Tests for the retry handler module."""

import asyncio
from unittest.mock import Mock, patch

import pytest
from aiohttp import ClientError, ClientResponse

from app.utils.retry_handler import (
    RetryableError,
    NonRetryableError,
    create_retry_decorator,
    is_retryable_error,
)


def test_is_retryable_error():
    """Test the is_retryable_error function."""
    assert is_retryable_error(RetryableError())
    assert is_retryable_error(ClientError())
    assert not is_retryable_error(NonRetryableError())
    assert not is_retryable_error(ValueError())


@pytest.mark.asyncio
async def test_retry_success_first_attempt():
    """Test successful execution on first attempt."""
    mock_func = Mock(return_value=asyncio.Future())
    mock_func.return_value.set_result("success")
    
    decorated = create_retry_decorator()(mock_func)
    result = await decorated()
    
    assert result == "success"
    mock_func.assert_called_once()


@pytest.mark.asyncio
async def test_retry_success_after_retries():
    """Test successful execution after several retries."""
    mock_func = Mock(side_effect=[
        RetryableError("First attempt"),
        RetryableError("Second attempt"),
        asyncio.Future()
    ])
    mock_func.return_value = asyncio.Future()
    mock_func.return_value.set_result("success")
    
    decorated = create_retry_decorator(max_attempts=3)(mock_func)
    result = await decorated()
    
    assert result == "success"
    assert mock_func.call_count == 3


@pytest.mark.asyncio
async def test_retry_max_attempts_exceeded():
    """Test that max retry attempts are not exceeded."""
    mock_func = Mock(side_effect=RetryableError("Error"))
    decorated = create_retry_decorator(max_attempts=3)(mock_func)
    
    with pytest.raises(Exception):
        await decorated()
    
    assert mock_func.call_count == 3


@pytest.mark.asyncio
async def test_non_retryable_error():
    """Test that non-retryable errors are not retried."""
    mock_func = Mock(side_effect=NonRetryableError("Not retryable"))
    decorated = create_retry_decorator()(mock_func)
    
    with pytest.raises(NonRetryableError):
        await decorated()
    
    mock_func.assert_called_once()


@pytest.mark.asyncio
async def test_client_response_handling():
    """Test handling of aiohttp ClientResponse objects."""
    # Mock a successful response
    success_response = Mock(spec=ClientResponse)
    success_response.status = 200
    
    # Mock a server error response
    server_error_response = Mock(spec=ClientResponse)
    server_error_response.status = 500
    
    # Mock a client error response
    client_error_response = Mock(spec=ClientResponse)
    client_error_response.status = 400
    
    # Test successful response
    mock_func = Mock(return_value=asyncio.Future())
    mock_func.return_value.set_result(success_response)
    decorated = create_retry_decorator()(mock_func)
    result = await decorated()
    assert result.status == 200
    mock_func.assert_called_once()
    
    # Test server error (should retry)
    mock_func = Mock(side_effect=[
        asyncio.Future(),
        asyncio.Future(),
        asyncio.Future()
    ])
    mock_func.side_effect[0].set_result(server_error_response)
    mock_func.side_effect[1].set_result(server_error_response)
    mock_func.side_effect[2].set_result(success_response)
    
    decorated = create_retry_decorator()(mock_func)
    result = await decorated()
    assert result.status == 200
    assert mock_func.call_count == 3
    
    # Test client error (should not retry)
    mock_func = Mock(return_value=asyncio.Future())
    mock_func.return_value.set_result(client_error_response)
    decorated = create_retry_decorator()(mock_func)
    
    with pytest.raises(NonRetryableError):
        await decorated()
    
    mock_func.assert_called_once()


@pytest.mark.asyncio
async def test_custom_retry_configuration():
    """Test retry decorator with custom configuration."""
    mock_func = Mock(side_effect=[
        RetryableError("First attempt"),
        RetryableError("Second attempt"),
        asyncio.Future()
    ])
    mock_func.return_value = asyncio.Future()
    mock_func.return_value.set_result("success")
    
    # Custom configuration
    decorated = create_retry_decorator(
        max_attempts=5,
        wait_min=2,
        wait_max=20,
        wait_multiplier=3,
        retry_on_exceptions=(RetryableError,)
    )(mock_func)
    
    result = await decorated()
    assert result == "success"
    assert mock_func.call_count == 3
