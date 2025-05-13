"""
Tests for utility functions in core/__init__.py
"""

import pytest
import sys
import os
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock, call

# Ensure src/ is in sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

# Import the functions being tested
from core import chatutil


def test_chatutil_decorator():
    """Test that chatutil correctly wraps async functions."""
    # Define a simple test function
    test_func_called = False
    
    @chatutil("TestDecorator")
    async def test_func(input_str):
        nonlocal test_func_called
        test_func_called = True
        assert input_str == "test input"
    
    # Mock the input function to return test input
    with patch('builtins.input', return_value="test input"):
        # Run the function
        asyncio.run(test_func())
        
        # Verify function was called with the input
        assert test_func_called


def test_graceful_exit_async():
    """Test the graceful_exit decorator on asynchronous functions."""
    from core import graceful_exit
    
    # Create a test coroutine function
    @graceful_exit
    async def test_coro():
        return "async success"
    
    # Test normal execution
    assert asyncio.run(test_coro()) == "async success"
    
    # Test exception handling
    @graceful_exit
    async def error_coro():
        raise Exception("Async test error")
    
    # Should return None and not raise
    with patch('builtins.print') as mock_print:
        result = asyncio.run(error_coro())
        assert result is None
        mock_print.assert_called_with("Error: Async test error")
    
    # Test keyboard interrupt handling
    @graceful_exit
    async def interrupt_coro():
        raise KeyboardInterrupt()
    
    # Should exit gracefully
    with patch('builtins.print') as mock_print, \
         patch('builtins.exit') as mock_exit:
        asyncio.run(interrupt_coro())
        mock_print.assert_called_with("\nBye!")
        mock_exit.assert_called_with(0)


def test_graceful_exit_sync():
    """Test the graceful_exit decorator on synchronous functions."""
    from core import graceful_exit
    
    # Create a test function
    @graceful_exit
    def test_func():
        return "success"
    
    # Test normal execution
    assert test_func() == "success"
    
    # Test exception handling
    @graceful_exit
    def error_func():
        raise Exception("Test error")
    
    # Should return None and not raise
    with patch('builtins.print') as mock_print:
        result = error_func()
        assert result is None
        mock_print.assert_called_with("Error: Test error")
    
    # Test keyboard interrupt handling
    @graceful_exit
    def interrupt_func():
        raise KeyboardInterrupt()
    
    # Should exit gracefully
    with patch('builtins.print') as mock_print, \
         patch('builtins.exit') as mock_exit:
        interrupt_func()
        mock_print.assert_called_with("\nBye!")
        mock_exit.assert_called_with(0)


def test_mainloop():
    """Test the mainloop decorator functionality without causing infinite loop."""
    from core import mainloop
    
    # Mock asyncio functions to verify behavior
    with patch('asyncio.get_event_loop') as mock_get_loop:
        # Create a simple counter for testing
        counter = [0]
        
        # Create a mock function
        mock_func = AsyncMock()
        mock_func.side_effect = lambda: counter[0].__setitem__(0, counter[0] + 1)
        
        # Apply the decorator
        decorated = mainloop(mock_func)
        
        # Assert it returns a function
        assert callable(decorated)
        
        # Simulate running it with a KeyboardInterrupt after first execution
        mock_func.side_effect = KeyboardInterrupt()
        
        # Run with exception handling
        with pytest.raises(KeyboardInterrupt):
            asyncio.run(decorated())
        
        # Verify the mock was called
        mock_func.assert_called_once()


def test_set_debug():
    """Test the set_debug function."""
    # Use the direct import approach to test module-level variables
    import src.core as core_mod
    
    # Save the original value
    original_debug = core_mod.DEBUG
    
    try:
        # Reset to a known state
        core_mod.DEBUG = False
        assert core_mod.DEBUG is False
        
        # Call the function
        core_mod.set_debug(True)
        
        # Verify it changed
        assert core_mod.DEBUG is True
        
        # Reset again
        core_mod.set_debug(False)
        assert core_mod.DEBUG is False
        
    finally:
        # Restore the original value
        core_mod.DEBUG = original_debug