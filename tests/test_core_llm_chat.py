import asyncio
import json
import os
import pytest
from unittest.mock import patch, Mock, AsyncMock, MagicMock
from typing import Dict, Any, List

from core.llm.chat import Chat
from core.llm.client import ChatClient
from tools import Tool


class MockTool(Tool):
    def __init__(self, name="test_tool", description="Test tool", parameters=None):
        super().__init__(name, description, parameters or {})
    
    async def run(self, **kwargs):
        return {"result": "test success", "args": kwargs}


class TestChat:
    def setup_method(self):
        self.mock_tool = MockTool()
        self.tools = [self.mock_tool]

    @patch.dict(os.environ, {"AZURE_OPENAI_API_KEY": "test_key"})
    def test_chat_init(self):
        chat = Chat(self.tools)
        assert len(chat.tool_map) == 1
        assert "test_tool" in chat.tool_map
        assert len(chat.tools) == 1

    def test_add_tool(self):
        chat = Chat()
        new_tool = MockTool("new_tool")
        chat.add_tool(new_tool)
        
        assert "new_tool" in chat.tool_map
        assert len(chat.tools) == 1

    @patch.dict(os.environ, {"AZURE_OPENAI_API_KEY": "test_key"})
    def test_create_chat_success(self):
        chat = Chat.create(self.tools)
        assert isinstance(chat, Chat)
        assert len(chat.tool_map) == 1

    def test_create_chat_missing_api_key(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="AZURE_OPENAI_API_KEY"):
                Chat.create(self.tools)

    @pytest.mark.asyncio
    async def test_send_messages(self):
        chat = Chat()
        mock_response = {"choices": [{"message": {"content": "test response"}}]}
        
        with patch.object(chat.chat_client, 'make_request', return_value=mock_response) as mock_request:
            messages = [{"role": "user", "content": "test"}]
            result = await chat.send_messages(messages)
            
            assert result == mock_response
            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_tool_calls_with_valid_tool(self):
        chat = Chat(self.tools)
        response = {
            "tool_calls": [{
                "id": "test_id",
                "function": {
                    "name": "test_tool",
                    "arguments": '{"param": "value"}'
                }
            }]
        }
        
        messages = []
        await chat.process_tool_calls(response, messages.append)
        
        assert len(messages) == 1
        assert messages[0]["role"] == "tool"
        assert messages[0]["tool_call_id"] == "test_id"

    @pytest.mark.asyncio
    async def test_process_tool_calls_with_unknown_tool(self):
        chat = Chat()
        response = {
            "tool_calls": [{
                "id": "test_id",
                "function": {
                    "name": "unknown_tool",
                    "arguments": '{"param": "value"}'
                }
            }]
        }
        
        messages = []
        await chat.process_tool_calls(response, messages.append)
        
        assert len(messages) == 1
        tool_result = json.loads(messages[0]["content"])
        assert "error" in tool_result
        assert "not found" in tool_result["error"]

    @pytest.mark.asyncio
    async def test_process_tool_calls_with_exception(self):
        failing_tool = MockTool("failing_tool")
        
        async def failing_run(**kwargs):
            raise ValueError("Tool execution failed")
        
        failing_tool.run = failing_run
        chat = Chat([failing_tool])
        
        response = {
            "tool_calls": [{
                "id": "test_id",
                "function": {
                    "name": "failing_tool",
                    "arguments": '{"param": "value"}'
                }
            }]
        }
        
        messages = []
        await chat.process_tool_calls(response, messages.append)
        
        assert len(messages) == 1
        tool_result = json.loads(messages[0]["content"])
        assert "error" in tool_result

    @pytest.mark.asyncio
    async def test_process_tool_calls_with_no_tool_calls(self):
        chat = Chat()
        response = {}
        
        messages = []
        await chat.process_tool_calls(response, messages.append)
        
        assert len(messages) == 0

    @pytest.mark.asyncio
    async def test_process_tool_calls_invalid_json_arguments(self):
        chat = Chat(self.tools)
        response = {
            "tool_calls": [{
                "id": "test_id",
                "function": {
                    "name": "test_tool",
                    "arguments": 'invalid json'
                }
            }]
        }
        
        messages = []
        await chat.process_tool_calls(response, messages.append)
        
        assert len(messages) == 1
        assert messages[0]["role"] == "tool"
