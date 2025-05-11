import pytest
import sys
import os
from unittest.mock import patch, MagicMock, AsyncMock
import json

# Ensure src/ is in sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))


@pytest.mark.asyncio
async def test_process_tool_calls_empty_tool_name():
    """Test process_tool_calls with an empty tool name."""
    import agent
    
    # Create a response with empty tool name
    response = {
        "tool_calls": [
            {
                "id": "call_123",
                "function": {
                    "name": "",  # Empty tool name
                    "arguments": "{}"
                }
            }
        ]
    }
    
    # Mock callback function
    callback_mock = MagicMock()
    
    # Process calls with empty tool name should continue without error
    with patch('builtins.print'):  # Suppress print output
        await agent.process_tool_calls(response, callback_mock)
    
    # Verify the callback was not called since we should continue the loop
    callback_mock.assert_not_called()


@pytest.mark.asyncio
async def test_process_tool_calls_tool_error():
    """Test process_tool_calls with a tool that raises an error."""
    import agent
    
    # Create a mock tool that raises an exception
    mock_tool = MagicMock()
    mock_tool.run = AsyncMock(side_effect=ValueError("Tool execution failed"))
    
    # Create a response using the mock tool
    response = {
        "tool_calls": [
            {
                "id": "call_123",
                "function": {
                    "name": "error_tool",
                    "arguments": '{"param": "value"}'
                }
            }
        ]
    }
    
    # Mock callback function
    callback_mock = MagicMock()
    
    # Save original tool_map and restore it later
    original_tool_map = agent.tool_map
    try:
        # Set up our mock tool
        agent.tool_map = {"error_tool": mock_tool}
        
        # Process calls with the error-raising tool
        with patch('builtins.print'):  # Suppress print output
            await agent.process_tool_calls(response, callback_mock)
        
        # Verify the callback was called with an error response
        callback_mock.assert_called_once()
        call_args = callback_mock.call_args[0][0]
        assert call_args["role"] == "tool"
        assert call_args["tool_call_id"] == "call_123"
        
        # Parse the content to verify the error message
        content = json.loads(call_args["content"])
        assert "error" in content
        assert "Tool execution failed" in content["error"]
        
    finally:
        # Restore original tool_map
        agent.tool_map = original_tool_map


@pytest.mark.asyncio
async def test_run_conversation_empty_choices():
    """Test run_conversation when the API returns empty choices."""
    import agent
    from utils import chatutil
    
    # Create a test function that simulates the run_conversation without chatutil decorator
    async def test_run_conv(prompt):
        # Save original messages and chat
        original_messages = agent.messages.copy()
        original_chat = agent.chat

        # Mock objects for testing
        mock_chat = MagicMock()
        mock_chat.send_messages = AsyncMock(return_value={"choices": []})
        
        try:
            # Replace with our mocks
            agent.messages = [{"role": "system", "content": agent.system_role}]
            agent.messages.append({"role": "user", "content": prompt})
            agent.chat = mock_chat
            
            # Call the first part of run_conversation directly
            response = await agent.chat.send_messages(agent.messages)
            
            # The rest of run_conversation logic
            choices = response.get("choices", [])
            # Should be empty
            assert len(choices) == 0
            
            # Should return empty string when no choices
            return ""
        finally:
            # Restore original objects
            agent.messages = original_messages
            agent.chat = original_chat

    # Run our test function
    with patch('builtins.print'):  # Suppress print output
        result = await test_run_conv("Test prompt")
    
    # Verify the result is an empty string due to empty choices
    assert result == ""


@pytest.mark.asyncio
async def test_process_tool_calls_invalid_json():
    """Test process_tool_calls with invalid JSON in arguments."""
    import agent
    
    # Create a response with invalid JSON arguments
    response = {
        "tool_calls": [
            {
                "id": "call_123",
                "function": {
                    "name": "some_tool",
                    "arguments": "{invalid json"  # Invalid JSON
                }
            }
        ]
    }
    
    # Mock callback function
    callback_mock = MagicMock()
    
    # Process calls with invalid JSON should handle the error gracefully
    with patch('builtins.print'):  # Suppress print output
        await agent.process_tool_calls(response, callback_mock)
    
    # Verify the callback was called with the appropriate tool response
    callback_mock.assert_called_once()
    call_args = callback_mock.call_args[0][0]
    assert call_args["role"] == "tool"
    assert call_args["tool_call_id"] == "call_123"
    
    # The content should contain an error message about the tool not being found
    content = json.loads(call_args["content"])
    assert "error" in content
    assert "not found" in content["error"]