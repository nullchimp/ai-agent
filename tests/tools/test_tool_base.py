import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Ensure src/ is in sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from tools import Tool

def test_tool_base_class_methods():
    """Test that the Tool base class methods can be called."""
    # Create an instance of the Tool base class
    tool = Tool()
    
    # Test the define method
    result_define = tool.define()
    assert result_define is None, "Tool.define() should return None by default"
    
    # Test the run method
    result_run = tool.run()
    assert result_run is None, "Tool.run() should return None by default"

def test_tool_base_class_inheritance():
    """Test that Tool can be properly inherited."""
    
    # Define a custom tool class that inherits from Tool
    class CustomTool(Tool):
        def define(self):
            return {"name": "custom_tool", "description": "A custom tool"}
            
        def run(self, param1=None, param2=None):
            return {"result": f"Ran with {param1} and {param2}"}
    
    # Create an instance of the custom tool
    custom_tool = CustomTool()
    
    # Test the overridden define method
    definition = custom_tool.define()
    assert definition == {"name": "custom_tool", "description": "A custom tool"}
    
    # Test the overridden run method with parameters
    result = custom_tool.run(param1="value1", param2="value2")
    assert result == {"result": "Ran with value1 and value2"}

def test_tool_run_with_args():
    """Test the Tool.run method with positional and keyword arguments."""
    tool = Tool()
    
    # Test with positional arguments
    result1 = tool.run("arg1", "arg2")
    assert result1 is None
    
    # Test with keyword arguments
    result2 = tool.run(key1="val1", key2="val2")
    assert result2 is None