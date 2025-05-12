import pytest
import sys
import os
from unittest.mock import MagicMock, AsyncMock

# Ensure src/ is in sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

# Import Tool class
from tools import Tool


def test_tool_base_class_inheritance():
    """Test that a class can inherit from Tool."""
    class CustomTool(Tool):
        def define(self):
            return {
                "type": "function",
                "function": {
                    "name": "custom",
                    "description": "Custom tool",
                    "parameters": {}
                }
            }
    
    tool = CustomTool("custom_tool")  # Provide required name parameter
    assert tool.name == "custom_tool"  # Name is set via constructor
    assert tool._structure is None  # Structure is none until define is called explicitly
    
    # The structure is returned by define(), not stored directly
    structure = tool.define()
    assert structure is not None
    assert structure["function"]["name"] == "custom"


@pytest.mark.asyncio
async def test_tool_base_class_methods():
    """Test that the Tool base class methods can be called."""
    # Create an instance of the Tool base class
    tool = Tool("test_tool")  # Provide required name parameter
    
    # Test the define method
    result_define = tool.define()
    assert result_define is None, "Tool.define() should return None by default"
    
    # Test the async run method
    result_run = await tool.run()
    assert result_run == {}, "Tool.run() should return empty dict by default"


@pytest.mark.asyncio
async def test_tool_run_with_args():
    """Test the Tool.run method with positional and keyword arguments."""
    tool = Tool("test_tool")  # Provide required name parameter
    
    # Test with positional arguments
    result1 = await tool.run("arg1", "arg2")
    assert result1 == {}
    
    # Test with keyword arguments
    result2 = await tool.run(key1="value1", key2="value2")
    assert result2 == {}


@pytest.mark.asyncio
async def test_tool_run_with_session():
    """Test the Tool.run method with a mocked session."""
    # Create a mock session
    mock_session = MagicMock()
    mock_session.call_tool = AsyncMock(return_value=[["content", [MagicMock(text="result")]]])
    
    # Create a tool with the mock session
    tool = Tool(name="test_tool", session=mock_session)
    
    # Test the run method
    result = await tool.run(param1="value1")
    
    # Verify the session.call_tool method was called
    mock_session.call_tool.assert_called_once_with("test_tool", {"param1": "value1"})
    
    # Verify the result is as expected
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["content"] == "result"