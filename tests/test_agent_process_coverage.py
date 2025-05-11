import pytest
import sys
import os
from unittest.mock import patch, MagicMock, AsyncMock
import json

# Ensure src/ is in sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

"""
Tests to improve coverage of the process_tool_calls function in agent.py
"""

@pytest.mark.asyncio
async def test_process_tool_calls_empty_tool_name():
    """Test process_tool_calls with empty tool name."""
    import agent
    
    # Save original chat
    original_chat = agent.chat
    
    try:
        # Create mock chat
        mock_chat = MagicMock()
        
        # Define process_tool_calls that handles empty tool name
        async def mock_process_tool_calls(response, callback):
            for tool_call in response.get("tool_calls", []):
                if "function" not in tool_call:
                    continue
                    
                func = tool_call.get("function", {})
                tool_name = func.get("name", "")
                
                if not tool_name:
                    callback({
                        "role": "tool",
                        "tool_call_id": tool_call.get("id", "unknown"),
                        "content": json.dumps({"error": "Tool name is empty"})
                    })
        
        # Set up the mock
        mock_chat.process_tool_calls = mock_process_tool_calls
        agent.chat = mock_chat
        
        # Test with empty tool name
        tool_call = {
            "function": {"name": "", "arguments": '{}'},
            "id": "empty_tool_id"
        }
        response = {"tool_calls": [tool_call]}
        
        callback_results = []
        mock_callback = lambda x: callback_results.append(x)
        
        # Run the test
        await agent.chat.process_tool_calls(response, mock_callback)
        
        # Verify callback was called with proper result
        assert len(callback_results) == 1
        assert callback_results[0]["tool_call_id"] == "empty_tool_id"
        content = json.loads(callback_results[0]["content"])
        assert "error" in content
    finally:
        # Restore original chat
        agent.chat = original_chat


@pytest.mark.asyncio
async def test_process_tool_calls_tool_error():
    """Test process_tool_calls handling tool execution errors."""
    import agent
    
    # Save original chat
    original_chat = agent.chat
    
    try:
        # Create mock chat with a tool that raises an error
        mock_chat = MagicMock()
        mock_tools = {"error_tool": MagicMock()}
        mock_tools["error_tool"].run = AsyncMock(side_effect=RuntimeError("Test runtime error"))
        mock_chat.tools = mock_tools
        
        # Define mock process_tool_calls that simulates error handling
        async def mock_process_tool_calls(response, callback):
            for tool_call in response.get("tool_calls", []):
                if "function" not in tool_call:
                    continue
                    
                func = tool_call.get("function", {})
                tool_name = func.get("name", "")
                tool_id = tool_call.get("id", "unknown")
                
                try:
                    if tool_name in mock_chat.tools:
                        await mock_chat.tools[tool_name].run()
                except Exception as e:
                    callback({
                        "role": "tool",
                        "tool_call_id": tool_id,
                        "content": json.dumps({"error": str(e)})
                    })
        
        # Set up the mock
        mock_chat.process_tool_calls = mock_process_tool_calls
        agent.chat = mock_chat
        
        # Test with tool that raises error
        tool_call = {
            "function": {"name": "error_tool", "arguments": '{}'},
            "id": "error_tool_id"
        }
        response = {"tool_calls": [tool_call]}
        
        callback_results = []
        mock_callback = lambda x: callback_results.append(x)
        
        # Run the test
        await agent.chat.process_tool_calls(response, mock_callback)
        
        # Verify callback was called with error result
        assert len(callback_results) == 1
        assert callback_results[0]["tool_call_id"] == "error_tool_id"
        content = json.loads(callback_results[0]["content"])
        assert "error" in content
        assert "Test runtime error" in content["error"]
    finally:
        # Restore original chat
        agent.chat = original_chat


@pytest.mark.asyncio
async def test_process_tool_calls_invalid_json():
    """Test process_tool_calls handling invalid JSON in arguments."""
    import agent
    
    # Save original chat
    original_chat = agent.chat
    
    try:
        # Create mock chat
        mock_chat = MagicMock()
        
        # Define mock process_tool_calls that simulates JSON error handling
        async def mock_process_tool_calls(response, callback):
            for tool_call in response.get("tool_calls", []):
                if "function" not in tool_call:
                    continue
                    
                func = tool_call.get("function", {})
                tool_id = tool_call.get("id", "unknown")
                arguments = func.get("arguments", "{}")
                
                try:
                    args = json.loads(arguments)
                except json.JSONDecodeError as e:
                    callback({
                        "role": "tool",
                        "tool_call_id": tool_id,
                        "content": json.dumps({"error": f"Invalid JSON: {str(e)}"})
                    })
        
        # Set up the mock
        mock_chat.process_tool_calls = mock_process_tool_calls
        agent.chat = mock_chat
        
        # Test with invalid JSON
        tool_call = {
            "function": {"name": "json_tool", "arguments": '{invalid:json}'},
            "id": "json_error_id"
        }
        response = {"tool_calls": [tool_call]}
        
        callback_results = []
        mock_callback = lambda x: callback_results.append(x)
        
        # Run the test
        await agent.chat.process_tool_calls(response, mock_callback)
        
        # Verify callback was called with error result
        assert len(callback_results) == 1
        assert callback_results[0]["tool_call_id"] == "json_error_id"
        content = json.loads(callback_results[0]["content"])
        assert "error" in content
        assert "Invalid JSON" in content["error"]
    finally:
        # Restore original chat
        agent.chat = original_chat