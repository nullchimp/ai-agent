import pytest
import sys
import os
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

# Ensure src/ is in sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from utils import chatloop

def test_chatloop_decorator_creation():
    """Test that the chatloop decorator returns a proper wrapper function."""
    decorator = chatloop("Test")
    assert callable(decorator), "chatloop should return a callable decorator"
    
    # Create a simple async function to decorate
    async def test_func():
        return "Success"
    
    # Apply decorator
    wrapped = decorator(test_func)
    assert callable(wrapped), "Decorated function should be callable"

@pytest.mark.asyncio
async def test_chatloop_execution_flow():
    """Test the execution flow of the chatloop decorator with mocked input/output."""
    with patch('builtins.input', side_effect=["test input", KeyboardInterrupt]):
        with patch('builtins.print') as mock_print:
            # Create a simple async function to decorate
            async def test_func(user_input):
                return f"Response: {user_input}"
            
            # Apply decorator
            wrapped = chatloop("TestChat")(test_func)
            
            # Run the wrapped function (should loop until KeyboardInterrupt)
            await wrapped()
            
            # Verify print was called with expected output containing our response
            mock_print.assert_any_call("\n--------------------------------------------------\n", "<Response> Response: test input", "\n--------------------------------------------------\n")

@pytest.mark.asyncio
async def test_chatloop_exception_handling():
    """Test how chatloop handles exceptions during execution."""
    with patch('builtins.input', side_effect=["test input", KeyboardInterrupt]):
        with patch('builtins.print') as mock_print:
            # Create an async function that raises an exception
            async def test_func(user_input):
                raise ValueError("Test error")
            
            # Apply decorator
            wrapped = chatloop("TestChat")(test_func)
            
            # Run the wrapped function (should catch the exception and continue)
            await wrapped()
            
            # Verify print was called with error message
            mock_print.assert_any_call("Error: Test error")

@pytest.mark.asyncio
async def test_chatloop_keyboard_interrupt():
    """Test that chatloop exits gracefully on keyboard interrupt."""
    with patch('builtins.input', side_effect=[KeyboardInterrupt]):
        with patch('builtins.print') as mock_print:
            # Create a simple async function
            async def test_func(user_input):
                return "This should not be reached"
            
            # Apply decorator
            wrapped = chatloop("TestChat")(test_func)
            
            # Run the wrapped function (should exit on KeyboardInterrupt)
            await wrapped()
            
            # Verify bye message was printed
            mock_print.assert_called_once_with("\nBye!")

@pytest.mark.asyncio
async def test_chatloop_multiple_inputs():
    """Test chatloop with multiple inputs before interruption."""
    with patch('builtins.input', side_effect=["first input", "second input", KeyboardInterrupt]):
        with patch('builtins.print') as mock_print:
            # Create a simple async function that counts calls
            call_count = 0
            
            async def test_func(user_input):
                nonlocal call_count
                call_count += 1
                return f"Call {call_count}: {user_input}"
            
            # Apply decorator
            wrapped = chatloop("TestChat")(test_func)
            
            # Run the wrapped function
            await wrapped()
            
            # Verify function was called twice (once for each input)
            assert call_count == 2