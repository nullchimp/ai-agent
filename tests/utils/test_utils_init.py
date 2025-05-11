import pytest
import sys
import os
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

# Ensure src/ is in sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from src.utils import mainloop, graceful_exit, chatutil

def test_mainloop_decorator_creation():
    """Test that the mainloop decorator returns a proper wrapper function."""
    # Create a simple async function to decorate
    async def test_func():
        return "Success"
    
    # Apply decorator
    wrapped = mainloop(test_func)
    assert callable(wrapped), "Decorated function should be callable"


@pytest.mark.asyncio
async def test_mainloop_execution_flow():
    """Test the execution flow of the mainloop decorator."""
    # Create a simple async function
    async def test_func(*args, **kwargs):
        return "test result"
    
    # Apply decorator
    wrapped = mainloop(test_func)
    
    # Mock the while loop to exit after one iteration
    with patch('asyncio.sleep', side_effect=KeyboardInterrupt):
        try:
            # Run the wrapped function (should loop until KeyboardInterrupt)
            await wrapped("arg1", kwarg1="value1")
        except KeyboardInterrupt:
            pass  # Expected behavior


def test_graceful_exit_sync_decorator():
    """Test the graceful_exit decorator with synchronous functions."""
    # Create a test function that raises an exception
    @graceful_exit
    def test_func():
        raise ValueError("Test error")
    
    # Run and verify it catches the exception
    with patch('builtins.print') as mock_print:
        result = test_func()
        
        # Verify error message was printed and function returned None
        mock_print.assert_called_with("Error: Test error")
        assert result is None


@pytest.mark.asyncio
async def test_graceful_exit_async_decorator():
    """Test the graceful_exit decorator with async functions."""
    # Create a test async function that raises an exception
    @graceful_exit
    async def test_func():
        raise ValueError("Test async error")
    
    # Run and verify it catches the exception
    with patch('builtins.print') as mock_print:
        result = await test_func()
        
        # Verify error message was printed and function returned None
        mock_print.assert_called_with("Error: Test async error")
        assert result is None


@pytest.mark.asyncio
async def test_graceful_exit_keyboard_interrupt():
    """Test graceful_exit handles KeyboardInterrupt."""
    # Create a test async function that raises KeyboardInterrupt
    @graceful_exit
    async def test_func():
        raise KeyboardInterrupt()
    
    # Mock the exit function to prevent test termination
    with patch('sys.exit') as mock_exit:
        with patch('builtins.print') as mock_print:
            await test_func()
            
            # Verify bye message was printed and exit was called
            mock_print.assert_called_with("\nBye!")
            mock_exit.assert_called_once_with(0)


@pytest.mark.asyncio
async def test_chatutil_decorator_execution():
    """Test the chatutil decorator's execution flow."""
    # Create a simple async function to decorate
    async def test_func(user_input, *args, **kwargs):
        return f"Response: {user_input}, args: {args}, kwargs: {kwargs}"
    
    # Apply decorator
    wrapped = chatutil("TestChat")(test_func)
    
    # Mock input/output
    with patch('builtins.input', return_value="test input"):
        with patch('builtins.print') as mock_print:
            # Run the wrapped function
            await wrapped("arg1", kwarg1="value1")
            
            # Verify the function prints with correct formatting
            hr = "\n" + "-" * 50 + "\n"
            mock_print.assert_called_with(
                hr, 
                "<Response> Response: test input, args: ('arg1',), kwargs: {'kwarg1': 'value1'}", 
                hr
            )