import pytest
import os
import sys
from unittest.mock import patch, MagicMock

# Ensure src/ is in sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import after path setup
from src.utils import graceful_exit

def test_graceful_exit_sync_function_normal():
    """Test graceful_exit with sync function in normal execution."""
    # Create a test sync function
    def test_func():
        return "sync result"
    
    # Apply decorator
    decorated = graceful_exit(test_func)
    
    # Test normal execution
    result = decorated()
    assert result == "sync result"

def test_graceful_exit_sync_function_exception():
    """Test graceful_exit with sync function that raises an exception."""
    # Create a test sync function that raises an exception
    def test_func():
        raise ValueError("Test error")
    
    # Apply decorator
    decorated = graceful_exit(test_func)
    
    # Test exception handling with print mock
    with patch('builtins.print') as mock_print:
        result = decorated()
        assert result is None
        mock_print.assert_called_once_with("Error: Test error")

def test_graceful_exit_sync_function_keyboard_interrupt():
    """Test graceful_exit with sync function that raises KeyboardInterrupt."""
    # Create a test sync function that raises KeyboardInterrupt
    def test_func():
        raise KeyboardInterrupt()
    
    # Apply decorator
    decorated = graceful_exit(test_func)
    
    # Mock both print and exit functions
    with patch('builtins.print') as mock_print:
        # Use side_effect to avoid SystemExit but still validate exit was called
        mock_exit = MagicMock(side_effect=lambda x: None)
        with patch('src.utils.exit', mock_exit):
            decorated()
            mock_print.assert_called_once_with("\nBye!")
            mock_exit.assert_called_once_with(0)

@pytest.mark.asyncio
async def test_graceful_exit_async_function_normal():
    """Test graceful_exit with async function in normal execution."""
    # Create a test async function
    async def test_func():
        return "async result"
    
    # Apply decorator
    decorated = graceful_exit(test_func)
    
    # Test normal execution
    result = await decorated()
    assert result == "async result"

@pytest.mark.asyncio
async def test_graceful_exit_async_function_exception():
    """Test graceful_exit with async function that raises an exception."""
    # Create a test async function that raises an exception
    async def test_func():
        raise ValueError("Test error")
    
    # Apply decorator
    decorated = graceful_exit(test_func)
    
    # Test exception handling with print mock
    with patch('builtins.print') as mock_print:
        result = await decorated()
        assert result is None
        mock_print.assert_called_once_with("Error: Test error")

@pytest.mark.asyncio
async def test_graceful_exit_async_function_keyboard_interrupt():
    """Test graceful_exit with async function that raises KeyboardInterrupt."""
    # Create a test async function that raises KeyboardInterrupt
    async def test_func():
        raise KeyboardInterrupt()
    
    # Apply decorator
    decorated = graceful_exit(test_func)
    
    # Mock both print and exit functions
    with patch('builtins.print') as mock_print:
        # Use side_effect to avoid SystemExit but still validate exit was called
        mock_exit = MagicMock(side_effect=lambda x: None)
        with patch('src.utils.exit', mock_exit):
            await decorated()
            mock_print.assert_called_once_with("\nBye!")
            mock_exit.assert_called_once_with(0)