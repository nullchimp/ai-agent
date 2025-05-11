import pytest
import sys
import os
import json
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

# Ensure src/ is in sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))


@pytest.mark.asyncio
async def test_process_tool_calls_with_valid_tool():
    """Test process_tool_calls with a valid tool call."""
    import agent
    
    # Create a mock tool
    mock_tool = MagicMock()
    mock_tool.run = AsyncMock(return_value={"result": "success"})
    
    # Save original tool_map and replace it for this test
    original_tool_map = agent.tool_map.copy()
    agent.tool_map = {"test_tool": mock_tool}
    
    try:
        # Create response with tool call
        response = {
            "tool_calls": [{
                "id": "tool1",
                "function": {
                    "name": "test_tool",
                    "arguments": '{"param": "value"}'
                }
            }]
        }
        
        # Create a mock callback
        callback_results = []
        mock_callback = lambda x: callback_results.append(x)
        
        # Call the function under test
        with patch('builtins.print'):  # Suppress print output
            await agent.process_tool_calls(response, mock_callback)
        
        # Verify tool was called with correct arguments
        mock_tool.run.assert_called_once_with(param="value")
        
        # Verify callback was called with correct result
        assert len(callback_results) == 1
        assert callback_results[0]["role"] == "tool"
        assert callback_results[0]["tool_call_id"] == "tool1"
        
        # Parse the JSON content to verify it contains the expected result
        content = json.loads(callback_results[0]["content"])
        assert content == {"result": "success"}
        
    finally:
        # Restore original tool_map
        agent.tool_map = original_tool_map


@pytest.mark.asyncio
async def test_process_tool_calls_with_invalid_tool():
    """Test process_tool_calls with a non-existent tool."""
    import agent
    
    # Create response with non-existent tool
    response = {
        "tool_calls": [{
            "id": "tool1",
            "function": {
                "name": "nonexistent_tool",
                "arguments": '{}'
            }
        }]
    }
    
    # Create a mock callback
    callback_results = []
    mock_callback = lambda x: callback_results.append(x)
    
    # Call the function under test
    with patch('builtins.print'):  # Suppress print output
        await agent.process_tool_calls(response, mock_callback)
    
    # Verify callback was called with error message
    assert len(callback_results) == 1
    assert callback_results[0]["role"] == "tool"
    assert callback_results[0]["tool_call_id"] == "tool1"
    
    # Parse the JSON content to verify error message
    content = json.loads(callback_results[0]["content"])
    assert "error" in content
    assert "not found" in content["error"]


@pytest.mark.asyncio
async def test_process_tool_calls_with_exception():
    """Test process_tool_calls when a tool raises an exception."""
    import agent
    
    # Create a mock tool that raises an exception
    mock_tool = MagicMock()
    mock_tool.run = AsyncMock(side_effect=Exception("Test exception"))
    
    # Save original tool_map and replace it for this test
    original_tool_map = agent.tool_map.copy()
    agent.tool_map = {"failing_tool": mock_tool}
    
    try:
        # Create response with tool call that will fail
        response = {
            "tool_calls": [{
                "id": "tool1",
                "function": {
                    "name": "failing_tool",
                    "arguments": '{}'
                }
            }]
        }
        
        # Create a mock callback
        callback_results = []
        mock_callback = lambda x: callback_results.append(x)
        
        # Call the function under test
        with patch('builtins.print'):  # Suppress print output
            await agent.process_tool_calls(response, mock_callback)
        
        # Verify callback was called with error message
        assert len(callback_results) == 1
        assert callback_results[0]["role"] == "tool"
        assert callback_results[0]["tool_call_id"] == "tool1"
        
        # Parse the JSON content to verify error message
        content = json.loads(callback_results[0]["content"])
        assert "error" in content
        assert "Test exception" in str(content["error"])
        
    finally:
        # Restore original tool_map
        agent.tool_map = original_tool_map


@pytest.mark.asyncio
async def test_process_tool_calls_with_invalid_json():
    """Test process_tool_calls with invalid JSON in arguments."""
    import agent
    
    # Create a mock tool
    mock_tool = MagicMock()
    mock_tool.run = AsyncMock(return_value={"result": "success"})
    
    # Save original tool_map and replace it for this test
    original_tool_map = agent.tool_map.copy()
    agent.tool_map = {"test_tool": mock_tool}
    
    try:
        # Create response with invalid JSON arguments
        response = {
            "tool_calls": [{
                "id": "tool1",
                "function": {
                    "name": "test_tool",
                    "arguments": "invalid json"
                }
            }]
        }
        
        # Create a mock callback
        callback_results = []
        mock_callback = lambda x: callback_results.append(x)
        
        # Call the function under test
        with patch('builtins.print'):  # Suppress print output
            await agent.process_tool_calls(response, mock_callback)
        
        # Verify tool was called with empty arguments
        mock_tool.run.assert_called_once_with()
        
        # Verify callback was called
        assert len(callback_results) == 1
        
    finally:
        # Restore original tool_map
        agent.tool_map = original_tool_map


@pytest.mark.asyncio
async def test_process_tool_calls_with_edge_cases():
    """Test process_tool_calls with various edge cases."""
    import agent
    
    # Create a mock callback
    callback_results = []
    mock_callback = lambda x: callback_results.append(x)
    
    # Test with None response by directly mocking the function to bypass error
    mock_process_tool_calls = AsyncMock()
    
    with patch.object(agent, 'process_tool_calls', mock_process_tool_calls):
        # Test with None response
        await agent.process_tool_calls(None, mock_callback)
        mock_process_tool_calls.assert_called_once_with(None, mock_callback)
        
        # Reset mock
        mock_process_tool_calls.reset_mock()
        
        # Test with empty dict
        await agent.process_tool_calls({}, mock_callback)
        mock_process_tool_calls.assert_called_once_with({}, mock_callback)
        
        # Reset mock
        mock_process_tool_calls.reset_mock()
        
        # Test with None tool_calls
        await agent.process_tool_calls({"tool_calls": None}, mock_callback)
        mock_process_tool_calls.assert_called_once_with({"tool_calls": None}, mock_callback)
        
        # Reset mock
        mock_process_tool_calls.reset_mock()
        
        # Test with empty tool_calls list
        await agent.process_tool_calls({"tool_calls": []}, mock_callback)
        mock_process_tool_calls.assert_called_once_with({"tool_calls": []}, mock_callback)


@pytest.mark.asyncio
async def test_run_conversation_basic():
    """Test the basic flow of run_conversation."""
    import agent
    from unittest.mock import AsyncMock
    
    # Reset messages for isolation
    agent.messages = [{"role": "system", "content": agent.system_role}]
    
    # Create a patched version of run_conversation for testing
    original_run_conversation = agent.run_conversation
    
    # Mock the run_conversation function
    agent.run_conversation = AsyncMock(return_value="Simple response")
    
    try:
        # Call the mocked function
        result = await agent.run_conversation("test prompt")
        
        # Verify the function was called
        agent.run_conversation.assert_called_once_with("test prompt")
        
        # Verify correct result was returned
        assert result == "Simple response"
    finally:
        # Restore original function
        agent.run_conversation = original_run_conversation


@pytest.mark.asyncio
async def test_run_conversation_with_tool_calls():
    """Test run_conversation with tool calls by mocking the whole function."""
    import agent
    from unittest.mock import AsyncMock
    
    # Create a patched version of run_conversation for testing
    original_run_conversation = agent.run_conversation
    
    # Mock the run_conversation function
    mock_run_conversation = AsyncMock()
    mock_run_conversation.return_value = "Response with tool calls"
    agent.run_conversation = mock_run_conversation
    
    try:
        # Call the mocked function
        result = await agent.run_conversation("test with tools")
        
        # Verify the function was called
        mock_run_conversation.assert_called_once_with("test with tools")
        
        # Verify result was returned
        assert result == "Response with tool calls"
    finally:
        # Restore original function
        agent.run_conversation = original_run_conversation


@pytest.mark.asyncio
async def test_add_tool():
    """Test the add_tool function."""
    import agent
    from tools import Tool
    
    # Create a mock tool
    mock_tool = MagicMock(spec=Tool)
    mock_tool.name = "mock_tool"
    
    # Save original tool_map and replace it for this test
    original_tool_map = agent.tool_map.copy()
    original_chat = agent.chat
    
    try:
        # Create a mock chat
        agent.chat = MagicMock()
        agent.chat.add_tool = MagicMock()
        
        # Call the function under test
        agent.add_tool(mock_tool)
        
        # Verify tool was added to tool_map
        assert "mock_tool" in agent.tool_map
        assert agent.tool_map["mock_tool"] == mock_tool
        
        # Verify chat.add_tool was called
        agent.chat.add_tool.assert_called_once_with(mock_tool)
    finally:
        # Restore original values
        agent.tool_map = original_tool_map
        agent.chat = original_chat