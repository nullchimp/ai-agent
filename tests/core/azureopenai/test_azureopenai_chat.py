"""
Tests for Chat class in utils/azureopenai/chat.py
"""

import pytest
import sys
import os
from unittest.mock import patch, MagicMock, AsyncMock

# Ensure src/ is in sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../src')))

# Import necessary classes
from core.azureopenai.chat import Chat


def test_chat_create_env(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "key")
    chat = Chat.create()
    assert isinstance(chat, Chat)


def test_chat_create_no_env(monkeypatch):
    monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError):
        Chat.create()


@pytest.mark.asyncio
async def test_chat_send_messages(monkeypatch):
    chat = Chat(MagicMock())
    chat.client.make_request = AsyncMock(return_value={"choices": [{"message": {"content": "result"}}]})
    out = await chat.send_messages([{"role": "user", "content": "hi"}])
    assert out["choices"][0]["message"]["content"] == "result"
    chat.client.make_request.assert_called()


def test_chat_tools_property():
    """Test that Chat's tools property contains the tool definitions."""
    # Create a mock tool
    mock_tool = MagicMock()
    mock_tool.name = "test_tool"
    mock_tool.define.return_value = {"name": "test_tool", "description": "Test tool"}
    
    # Create a chat instance with the mock tool
    chat = Chat(MagicMock(), tool_list=[mock_tool])
    
    # Verify that tools contains the tool definition
    assert len(chat.tools) == 1
    assert chat.tools[0]["name"] == "test_tool"
    assert mock_tool.define.called


def test_chat_add_tool():
    """Test that add_tool adds a tool to the tool_map and tools list."""
    # Create initial chat with no tools
    chat = Chat(MagicMock(), tool_list=[])
    assert len(chat.tools) == 0
    assert len(chat.tool_map) == 0
    
    # Create a mock tool
    mock_tool = MagicMock()
    mock_tool.name = "new_tool"
    mock_tool.define.return_value = {"name": "new_tool", "description": "New tool"}
    
    # Add the tool
    chat.add_tool(mock_tool)
    
    # Verify the tool was added correctly
    assert len(chat.tools) == 1
    assert len(chat.tool_map) == 1
    assert chat.tools[0]["name"] == "new_tool"
    assert chat.tool_map["new_tool"] == mock_tool


def test_chat_create():
    """Test the Chat.create factory method."""
    # Mock the environment and client
    with patch('os.environ.get', return_value="test_api_key"), \
         patch('utils.azureopenai.chat.Client') as mock_client_class:
        
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Create mock tools
        mock_tool = MagicMock()
        mock_tool.name = "test_tool"
        mock_tool.define.return_value = {"name": "test_tool", "description": "Test tool"}
        
        # Call create
        chat = Chat.create([mock_tool])
        
        # Verify client was created with correct API key
        mock_client_class.assert_called_once_with(api_key="test_api_key")
        
        # Verify chat instance has correct attributes
        assert chat.client == mock_client
        assert len(chat.tools) == 1
        assert len(chat.tool_map) == 1
        assert mock_tool.name in chat.tool_map


def test_chat_create_missing_api_key():
    """Test that Chat.create raises ValueError when API key is missing."""
    # Mock the environment to return None for API key
    with patch('os.environ.get', return_value=None):
        # Expect ValueError
        with pytest.raises(ValueError, match="AZURE_OPENAI_API_KEY environment variable is required"):
            Chat.create([])


@pytest.mark.asyncio
async def test_chat_process_tool_calls():
    """Test processing tool calls in a response."""
    # Create a mock tool and client
    mock_tool = MagicMock()
    mock_tool.name = "test_tool"
    mock_tool.run = AsyncMock(return_value={"result": "success"})
    
    mock_client = MagicMock()
    
    # Create chat instance with mock tool
    chat = Chat(mock_client, [mock_tool])
    chat.tool_map = {"test_tool": mock_tool}
    
    # Create a response with a tool call
    response = {
        "tool_calls": [
            {
                "id": "call1",
                "function": {
                    "name": "test_tool",
                    "arguments": '{"arg1": "value1"}'
                }
            }
        ]
    }
    
    # Create a callback to record calls
    callback_results = []
    def callback(msg):
        callback_results.append(msg)
    
    # Process tool calls
    await chat.process_tool_calls(response, callback)
    
    # Verify tool was called with correct arguments
    mock_tool.run.assert_called_once_with(arg1="value1")
    
    # Verify callback was called with correct result
    assert len(callback_results) == 1
    assert callback_results[0]["role"] == "tool"
    assert callback_results[0]["tool_call_id"] == "call1"
    assert "success" in callback_results[0]["content"]


def test_placeholder():
    assert True
