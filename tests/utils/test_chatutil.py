import pytest
import os
import sys
from unittest.mock import patch, MagicMock, AsyncMock

# Ensure src/ is in sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import after path setup
from src.utils import chatutil

@pytest.mark.asyncio
async def test_chatutil_basic_functionality():
    """Test that chatutil correctly wraps an async function and processes input/output."""
    # Create a simple async function to decorate
    async def test_func(user_input, *args, **kwargs):
        return f"Response: {user_input}, args: {args}, kwargs: {kwargs}"
    
    # Apply decorator with a chat name
    chat_name = "TestChat"
    wrapped = chatutil(chat_name)(test_func)
    
    # Mock input/output
    test_input = "test input"
    with patch('builtins.input', return_value=test_input) as mock_input:
        with patch('builtins.print') as mock_print:
            # Run the wrapped function
            await wrapped("arg1", kwarg1="value1")
            
            # Verify input was prompted with correct chat name
            mock_input.assert_called_once_with(f"<{chat_name}> ")
            
            # Verify formatted output was printed
            hr = "\n" + "-" * 50 + "\n"
            expected_output = f"<Response> Response: {test_input}, args: ('arg1',), kwargs: {{'kwarg1': 'value1'}}"
            mock_print.assert_called_with(hr, expected_output, hr)

@pytest.mark.asyncio
async def test_chatutil_empty_input():
    """Test chatutil with empty user input."""
    # Create a simple async function
    async def test_func(user_input):
        return f"You said: '{user_input}'"
    
    # Apply decorator
    wrapped = chatutil("EmptyTest")(test_func)
    
    # Mock empty input
    with patch('builtins.input', return_value="") as mock_input:
        with patch('builtins.print') as mock_print:
            # Run the wrapped function
            await wrapped()
            
            # Verify correct response with empty input
            hr = "\n" + "-" * 50 + "\n"
            expected_output = "<Response> You said: ''"
            mock_print.assert_called_with(hr, expected_output, hr)

@pytest.mark.asyncio
async def test_chatutil_exception_handling():
    """Test chatutil handles exceptions in the decorated function."""
    # Create a function that raises an exception
    async def test_func(user_input):
        raise ValueError("Test error")
    
    # Apply decorator
    wrapped = chatutil("ErrorTest")(test_func)
    
    # Mock input and run with exception
    with patch('builtins.input', return_value="test input"):
        with patch('builtins.print') as mock_print:
            # Using try-except because we expect the exception to propagate
            try:
                await wrapped()
                assert False, "Expected ValueError was not raised"
            except ValueError:
                # Correct behavior: exception should propagate up
                pass
            
            # Verify no response was printed
            for call in mock_print.call_args_list:
                args, _ = call
                assert "<Response>" not in "".join(str(arg) for arg in args)