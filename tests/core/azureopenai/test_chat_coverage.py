import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json
import os
from core.azureopenai.chat import Chat
from tools import Tool

@pytest.fixture
def mock_client():
    client = AsyncMock()
    client.make_request = AsyncMock()
    return client

def test_chat_create_with_api_key():
    """Test successful Chat creation with API key in environment"""
    # Create a proper mock tool that has a name attribute
    mock_tool = MagicMock()
    mock_tool.name = "test_tool"
    mock_tool.define.return_value = {"name": "test_tool"}
    tools = [mock_tool]
    
    # Mock environment variables
    with patch.dict(os.environ, {"AZURE_OPENAI_API_KEY": "test_api_key"}), \
         patch("core.azureopenai.chat.Client") as mock_client_class, \
         patch("core.azureopenai.chat.DEBUG", False):  # Disable debug output for test
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        chat = Chat.create(tools)
        
        # Verify client was created with correct API key
        mock_client_class.assert_called_once_with(api_key="test_api_key")
        
        # Verify tools are properly added
        assert len(chat.tools) == 1
        assert chat.tools[0] == {"name": "test_tool"}
        assert chat.tool_map["test_tool"] == tools[0]

def test_chat_create_missing_api_key():
    """Test Chat creation fails when API key is missing from environment"""
    # Mock environment variables to remove API key
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="AZURE_OPENAI_API_KEY environment variable is required"):
            Chat.create([])

def test_add_tool():
    """Test adding a tool to an existing Chat instance"""
    mock_client = MagicMock()
    chat = Chat(mock_client)
    
    # Create a mock tool
    tool = MagicMock(spec=Tool)
    tool.name = "new_tool"
    tool.define.return_value = {"name": "new_tool", "description": "A new test tool"}
    
    # Add the tool
    chat.add_tool(tool)
    
    # Verify tool was added correctly
    assert chat.tool_map["new_tool"] == tool
    assert {"name": "new_tool", "description": "A new test tool"} in chat.tools

@pytest.mark.asyncio
async def test_send_messages(mock_client):
    """Test sending messages to the client"""
    chat = Chat(mock_client)
    messages = [{"role": "user", "content": "Hello"}]
    expected_response = {"choices": [{"message": {"content": "Hi there"}}]}
    mock_client.make_request.return_value = expected_response
    
    response = await chat.send_messages(messages)
    
    # Verify client.make_request was called with correct parameters
    mock_client.make_request.assert_called_once_with(
        messages=messages,
        temperature=0.7,
        max_tokens=32000,
        tools=[]
    )
    
    # Verify response is returned as-is
    assert response == expected_response

@pytest.mark.asyncio
async def test_process_tool_calls_no_tools():
    """Test processing tool calls when no tools are called"""
    chat = Chat(MagicMock())
    response = {"content": "No tool calls here"}
    callback = MagicMock()
    
    await chat.process_tool_calls(response, callback)
    
    # Verify callback was not called (no tool calls to process)
    callback.assert_not_called()

@pytest.mark.asyncio
async def test_process_tool_calls_tool_not_found():
    """Test processing tool calls when the called tool is not found"""
    chat = Chat(MagicMock())
    tool_call = {
        "id": "call1",
        "function": {
            "name": "nonexistent_tool",
            "arguments": "{}"
        }
    }
    response = {"tool_calls": [tool_call]}
    callback = MagicMock()
    
    await chat.process_tool_calls(response, callback)
    
    # Verify callback was called with error about tool not found
    callback.assert_called_once()
    call_args = callback.call_args[0][0]
    assert call_args["role"] == "tool"
    assert call_args["tool_call_id"] == "call1"
    assert "error" in json.loads(call_args["content"])
    assert "not found" in json.loads(call_args["content"])["error"]

@pytest.mark.asyncio
async def test_process_tool_calls_tool_execution_error():
    """Test processing tool calls when the tool execution raises an exception"""
    chat = Chat(MagicMock())
    
    # Create a mock tool that raises an exception when run
    mock_tool = MagicMock()
    mock_tool.name = "error_tool"
    mock_tool.run.side_effect = Exception("Tool execution failed")
    
    # Add the tool to the chat
    chat.tool_map = {"error_tool": mock_tool}
    
    tool_call = {
        "id": "call1",
        "function": {
            "name": "error_tool",
            "arguments": '{"param": "value"}'
        }
    }
    response = {"tool_calls": [tool_call]}
    callback = MagicMock()
    
    await chat.process_tool_calls(response, callback)
    
    # Verify tool.run was called with correct parameters
    mock_tool.run.assert_called_once_with(param="value")
    
    # Verify callback contains error message
    callback.assert_called_once()
    call_args = callback.call_args[0][0]
    assert call_args["role"] == "tool"
    assert call_args["tool_call_id"] == "call1"
    assert "error" in json.loads(call_args["content"])
    assert "Tool execution failed" in json.loads(call_args["content"])["error"]

@pytest.mark.asyncio
async def test_process_tool_calls_successful():
    """Test successful processing of tool calls"""
    chat = Chat(MagicMock())
    
    # Create a mock tool that returns a result
    mock_tool = MagicMock()
    mock_tool.name = "successful_tool"
    # Make the run method return a regular value (not a coroutine) to avoid awaiting issues
    mock_tool.run = AsyncMock(return_value={"result": "success"})
    
    # Add the tool to the chat
    chat.tool_map = {"successful_tool": mock_tool}
    
    tool_call = {
        "id": "call1",
        "function": {
            "name": "successful_tool",
            "arguments": '{"param": "value"}'
        }
    }
    response = {"tool_calls": [tool_call]}
    callback = MagicMock()
    
    await chat.process_tool_calls(response, callback)
    
    # Verify tool.run was called with correct parameters
    mock_tool.run.assert_called_once_with(param="value")
    
    # Verify callback contains success result
    callback.assert_called_once()
    call_args = callback.call_args[0][0]
    assert call_args["role"] == "tool"
    assert call_args["tool_call_id"] == "call1"
    content_json = json.loads(call_args["content"])
    assert content_json == {"result": "success"}

@pytest.mark.asyncio
async def test_process_tool_calls_invalid_json():
    """Test processing tool calls with invalid JSON arguments"""
    chat = Chat(MagicMock())
    
    # Create a mock tool
    mock_tool = MagicMock()
    mock_tool.name = "test_tool"
    
    # Add the tool to the chat
    chat.tool_map = {"test_tool": mock_tool}
    
    tool_call = {
        "id": "call1",
        "function": {
            "name": "test_tool",
            "arguments": "invalid{json"  # Invalid JSON
        }
    }
    response = {"tool_calls": [tool_call]}
    callback = MagicMock()
    
    await chat.process_tool_calls(response, callback)
    
    # Verify tool.run was called with empty args (fallback for invalid JSON)
    mock_tool.run.assert_called_once_with()
    
    # Verify callback was called
    callback.assert_called_once()
    call_args = callback.call_args[0][0]
    assert call_args["role"] == "tool"
    assert call_args["tool_call_id"] == "call1"