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
    # Define a simple test function
    test_func_called = False
    
    @chatutil("TestModule")
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


def test_chatutil_empty_input():
    """Test chatutil decorator with empty input string."""
    # Define a simple test function
    test_func_called = False
    
    @chatutil("EmptyTest")
    async def test_func(input_str):
        nonlocal test_func_called
        test_func_called = True
        assert input_str == ""
    
    # Mock the input function to return empty string
    with patch('builtins.input', return_value=""):
        # Run the function
        asyncio.run(test_func())
        
        # Verify function was called with the empty input
        assert test_func_called


def test_chatutil_with_exception():
    """Test chatutil decorator when the wrapped function raises an exception."""
    # Define test function with chatutil decorator that raises an exception
    @chatutil("ExceptionTest")
    async def test_func_error(input_str):
        raise ValueError("Test error")
    
    # Mock the input function
    with patch('builtins.input', return_value="test input"):
        # Call the function and expect exception to be propagated
        with pytest.raises(ValueError, match="Test error"):
            asyncio.run(test_func_error())


def test_chatutil_with_args():
    """Test chatutil decorator with additional arguments."""
    # Define a simple test function with additional arguments
    test_func_called = False
    
    @chatutil("ArgsTest")
    async def test_func_with_args(input_str, extra_arg):
        nonlocal test_func_called
        test_func_called = True
        assert input_str == "test input"
        assert extra_arg == "extra"
    
    # Mock the input function to return test input
    with patch('builtins.input', return_value="test input"):
        # Run the function with additional arguments
        asyncio.run(test_func_with_args("extra"))
        
        # Verify function was called
        assert test_func_called


def test_chatutil_with_kwargs():
    """Test chatutil decorator with keyword arguments."""
    # Define a simple test function with keyword arguments
    test_func_called = False
    
    @chatutil("KwargsTest")
    async def test_func_with_kwargs(input_str, **kwargs):
        nonlocal test_func_called
        test_func_called = True
        assert input_str == "test input"
        assert kwargs["key"] == "value"
    
    # Mock the input function to return test input
    with patch('builtins.input', return_value="test input"):
        # Run the function with keyword arguments
        asyncio.run(test_func_with_kwargs(key="value"))
        
        # Verify function was called
        assert test_func_called


def test_placeholder():
    """This test is just here to ensure pytest doesn't complain."""
    assert True