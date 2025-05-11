"""
Tests for chatutil decorator in utils/__init__.py
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


def test_chatutil_basic_functionality():
    """Test that chatutil decorator properly wraps a function."""
    # Use patch to mock print function
    with patch('builtins.print') as mock_print:
        # Define test function with chatutil decorator
        @chatutil("TestModule")
        async def test_func(input_str):
            return f"Response: {input_str}"
        
        # Call the function
        result = asyncio.run(test_func("test input"))
        
        # Verify result is correct
        assert result == "Response: test input"
        
        # Check that print was called with expected formatting
        expected_calls = [
            call('\n--------------------------------------------------\n', '<TestModule> test input'),
            call('\n--------------------------------------------------\n', '<Response> Response: test input')
        ]
        mock_print.assert_has_calls(expected_calls)


def test_chatutil_empty_input():
    """Test chatutil decorator with empty input string."""
    # Use patch to mock print function
    with patch('builtins.print') as mock_print:
        # Define test function with chatutil decorator
        @chatutil("EmptyTest")
        async def test_func(input_str=""):
            return f"Empty response: '{input_str}'"
        
        # Call the function with empty input
        result = asyncio.run(test_func(""))
        
        # Verify result is correct
        assert result == "Empty response: ''"
        
        # Check that print was called with expected formatting
        expected_calls = [
            call('\n--------------------------------------------------\n', '<EmptyTest> '),
            call('\n--------------------------------------------------\n', "<Response> Empty response: ''")
        ]
        mock_print.assert_has_calls(expected_calls)


def test_chatutil_with_exception():
    """Test chatutil decorator when the wrapped function raises an exception."""
    # Use patch to mock print function
    with patch('builtins.print') as mock_print:
        # Define test function with chatutil decorator that raises an exception
        @chatutil("ExceptionTest")
        async def test_func_error():
            raise ValueError("Test error")
        
        # Call the function and expect exception to be propagated
        with pytest.raises(ValueError, match="Test error"):
            asyncio.run(test_func_error())
        
        # Check that only the input was printed, not the response
        mock_print.assert_called_once_with('\n--------------------------------------------------\n', '<ExceptionTest> ')


def test_chatutil_no_module_name():
    """Test chatutil decorator without providing a module name."""
    # Use patch to mock print function
    with patch('builtins.print') as mock_print:
        # Define test function with chatutil decorator without module name
        @chatutil()
        async def test_func_no_module(input_str):
            return f"Response: {input_str}"
        
        # Call the function
        result = asyncio.run(test_func_no_module("test input"))
        
        # Verify result is correct
        assert result == "Response: test input"
        
        # Check that print was called with appropriate default module name
        expected_calls = [
            call('\n--------------------------------------------------\n', '<Function> test input'),
            call('\n--------------------------------------------------\n', '<Response> Response: test input')
        ]
        mock_print.assert_has_calls(expected_calls)


def test_placeholder():
    """This test is just here to ensure pytest doesn't complain."""
    assert True