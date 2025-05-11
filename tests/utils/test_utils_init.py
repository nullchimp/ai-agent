"""
Tests for utility functions in utils/__init__.py
"""

import pytest
import sys
import os
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock, call

# Ensure src/ is in sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

# Import the functions being tested
from utils import chatutil


def test_chatutil_decorator():
    """Test that chatutil correctly wraps async functions."""
    # Use patch to mock print function
    with patch('builtins.print') as mock_print:
        # Define a test function with the chatutil decorator
        @chatutil("TestDecorator")
        async def decorated_func(input_text):
            return f"Output: {input_text}"
        
        # Call the decorated function
        result = asyncio.run(decorated_func("test input"))
        
        # Verify the function executed correctly
        assert result == "Output: test input"
        
        # Verify print was called with expected formatting
        expected_calls = [
            call('\n--------------------------------------------------\n', '<TestDecorator> test input'),
            call('\n--------------------------------------------------\n', '<Response> Output: test input')
        ]
        mock_print.assert_has_calls(expected_calls)


def test_graceful_exit():
    """This is a placeholder test for the graceful_exit decorator."""
    # Import graceful_exit now to avoid circular import issues
    from utils import graceful_exit
    
    assert callable(graceful_exit)
    
    # Define a simple function with the decorator
    @graceful_exit
    async def sample_func():
        return "test"
    
    # Verify the function is still callable
    assert callable(sample_func)
    
    # We won't test the exit handling, as that would terminate the process


def test_placeholder():
    """This test is just here to ensure pytest doesn't complain."""
    assert True