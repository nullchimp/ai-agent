import pytest
import asyncio
import os
import sys
from unittest.mock import patch, MagicMock, AsyncMock

# Ensure src/ is in sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import after path setup
from src.utils import mainloop

def test_mainloop_decorator_creation():
    """Test that mainloop returns a proper decorator function."""
    # Create a simple async function to decorate
    async def test_func():
        return "Success"
    
    # Apply decorator
    wrapped = mainloop(test_func)
    assert callable(wrapped)
    assert asyncio.iscoroutinefunction(wrapped)

@pytest.mark.asyncio
async def test_mainloop_calls_decorated_function():
    """Test that mainloop calls the decorated function at least once."""
    # Create a mock function
    mock_func = AsyncMock()
    mock_func.side_effect = [1, 2, KeyboardInterrupt]  # Will run twice then raise exception
    
    # Apply decorator
    wrapped = mainloop(mock_func)
    
    # Run wrapped function with exception to break out of the infinite loop
    try:
        await wrapped("arg1", kwarg1="value1")
    except KeyboardInterrupt:
        pass
    
    # Verify function was called with expected args
    mock_func.assert_called_with("arg1", kwarg1="value1")
    assert mock_func.call_count >= 1