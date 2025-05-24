import pytest
import asyncio
import json
import os
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, List

from src.core.llm.chat import Chat
from src.core.llm.client import Client, ChatClient, EmbeddingsClient
from src.tools import Tool


class TestClient:
    def test_client_init_success(self):
        with patch.dict(os.environ, {
            'AZURE_OPENAI_API_KEY': 'test-key'
        }):
            client = Client(
                model="test-model",
                endpoint="https://test.endpoint.com",
                timeout=60.0
            )
            assert client.api_key == "test-key"
            assert client.model == "test-model"
            assert client.endpoint == "https://test.endpoint.com"
            assert client.timeout == 60.0

    def test_client_init_missing_api_key(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="API key, model, and endpoint must be provided"):
                Client(
                    model="test-model",
                    endpoint="https://test.endpoint.com"
                )
                
    def test_client_init_missing_model(self):
        with patch.dict(os.environ, {
            'AZURE_OPENAI_API_KEY': 'test-key'
        }):
            with pytest.raises(ValueError, match="API key, model, and endpoint must be provided"):
                Client(
                    model=None,
                    endpoint="https://test.endpoint.com"
                )

    def test_client_init_missing_endpoint(self):
        with patch.dict(os.environ, {
            'AZURE_OPENAI_API_KEY': 'test-key'
        }):
            with pytest.raises(ValueError, match="API key, model, and endpoint must be provided"):
                Client(
                    model="test-model",
                    endpoint=None
                )

    @pytest.mark.asyncio
    async def test_client_make_request_not_implemented(self):
        with patch.dict(os.environ, {
            'AZURE_OPENAI_API_KEY': 'test-key'
        }):
            client = Client(
                model="test-model", 
                endpoint="https://test.endpoint.com"
            )
            with pytest.raises(NotImplementedError, match="Subclasses should implement this method"):
                await client.make_request([{"content": "test"}])

    def test_client_init_missing_model(self):
        with patch.dict(os.environ, {
            'AZURE_OPENAI_API_KEY': 'test-key'
        }):
            with pytest.raises(ValueError, match="API key, model, and endpoint must be provided"):
                Client(
                    model=None,
                    endpoint="https://test.endpoint.com"
                )

    def test_client_init_missing_endpoint(self):
        with patch.dict(os.environ, {
            'AZURE_OPENAI_API_KEY': 'test-key'
        }):
            with pytest.raises(ValueError, match="API key, model, and endpoint must be provided"):
                Client(
                    model="test-model",
                    endpoint=None
                )

    @pytest.mark.asyncio
    async def test_client_make_request_not_implemented(self):
        with patch.dict(os.environ, {
            'AZURE_OPENAI_API_KEY': 'test-key'
        }):
            client = Client(
                model="test-model",
                endpoint="https://test.endpoint.com"
            )
            
            with pytest.raises(NotImplementedError):
                await client.make_request([])


class TestChatClient:
    @patch.dict(os.environ, {
        'AZURE_OPENAI_API_KEY': 'test-key',
        'AZURE_OPENAI_CHAT_MODEL': 'gpt-4',
        'AZURE_OPENAI_CHAT_ENDPOINT': 'https://test.endpoint.com'
    })
    def test_chat_client_init_with_env_vars(self):
        client = ChatClient()
        assert client.api_key == "test-key"
        assert client.model == "gpt-4"
        assert client.endpoint == "https://test.endpoint.com"

    @patch.dict(os.environ, {
        'AZURE_OPENAI_API_KEY': 'test-key',
    })
    def test_chat_client_init_with_params(self):
        client = ChatClient(
            model="custom-gpt-3",
            timeout=120.0
        )
        # The model can be overridden by environment variable AZURE_OPENAI_CHAT_MODEL
        assert client.timeout == 120.0

    @patch.dict(os.environ, {
        'AZURE_OPENAI_API_KEY': 'test-key',
        'AZURE_OPENAI_CHAT_MODEL': 'gpt-4',
        'AZURE_OPENAI_CHAT_ENDPOINT': 'https://test.endpoint.com'
    })
    @pytest.mark.asyncio
    async def test_chat_client_make_request_simple_messages(self):
        client = ChatClient()
        
        # Mock the http_client post method
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": [{"message": {"content": "Response"}}]}
        client.http_client.post = AsyncMock(return_value=mock_response)
        
        messages = [
            {"role": "system", "content": "You are an assistant"},
            {"role": "user", "content": "Hello"}
        ]
        
        result = await client.make_request(messages)
        
        assert result == {"choices": [{"message": {"content": "Response"}}]}
        
        # Check that post was called with the right arguments
        client.http_client.post.assert_called_once()
        call_args = client.http_client.post.call_args
        assert call_args[0][0] == "https://test.endpoint.com"
        
        # Check payload
        json_payload = call_args[1]["json"]
        assert json_payload["model"] == "gpt-4"
        assert json_payload["messages"] == messages
        assert json_payload["temperature"] == 0.7
        assert json_payload["max_tokens"] == 2000
        assert json_payload["top_p"] == 1.0

    @patch.dict(os.environ, {
        'AZURE_OPENAI_API_KEY': 'test-key',
        'AZURE_OPENAI_CHAT_MODEL': 'gpt-4',
        'AZURE_OPENAI_CHAT_ENDPOINT': 'https://test.endpoint.com'
    })
    @pytest.mark.asyncio
    async def test_chat_client_make_request_with_tools(self):
        client = ChatClient()
        
        # Mock the http_client post method
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": [{"message": {"content": "Response"}}]}
        client.http_client.post = AsyncMock(return_value=mock_response)
        
        messages = [
            {"role": "system", "content": "You are an assistant"},
            {"role": "user", "content": "Hello"}
        ]
        
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "test_tool",
                    "description": "A test tool",
                    "parameters": {"type": "object", "properties": {}}
                }
            }
        ]
        
        result = await client.make_request(messages, tools=tools)
        
        assert result == {"choices": [{"message": {"content": "Response"}}]}
        
        # Check payload
        json_payload = client.http_client.post.call_args[1]["json"]
        assert "tools" in json_payload
        assert json_payload["tools"] == tools

    @patch.dict(os.environ, {
        'AZURE_OPENAI_API_KEY': 'test-key',
        'AZURE_OPENAI_CHAT_MODEL': 'gpt-4',
        'AZURE_OPENAI_CHAT_ENDPOINT': 'https://test.endpoint.com'
    })
    @pytest.mark.asyncio
    async def test_chat_client_make_request_error(self):
        client = ChatClient()
        
        # Mock the http_client post method to return an error
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": {"message": "Invalid request"}}
        client.http_client.post = AsyncMock(return_value=mock_response)
        
        messages = [{"role": "user", "content": "Hello"}]
        
        with pytest.raises(Exception, match="API error \\(400\\): Invalid request"):
            await client.make_request(messages)

    @patch.dict(os.environ, {
        'AZURE_OPENAI_API_KEY': 'test-key',
        'AZURE_OPENAI_CHAT_MODEL': 'gpt-4',
        'AZURE_OPENAI_CHAT_ENDPOINT': 'https://test.endpoint.com'
    })
    @pytest.mark.asyncio
    async def test_chat_client_make_request_with_name_field(self):
        client = ChatClient()
        
        # Mock the http_client post method
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": [{"message": {"content": "Response"}}]}
        client.http_client.post = AsyncMock(return_value=mock_response)
        
        messages = [
            {"role": "function", "name": "test_function", "content": "Function result"}
        ]
        
        await client.make_request(messages)
        
        # Check that name field was included in the message
        json_payload = client.http_client.post.call_args[1]["json"]
        assert json_payload["messages"][0]["name"] == "test_function"

    @patch.dict(os.environ, {
        'AZURE_OPENAI_API_KEY': 'test-key',
        'AZURE_OPENAI_CHAT_MODEL': 'gpt-4',
        'AZURE_OPENAI_CHAT_ENDPOINT': 'https://test.endpoint.com'
    })
    @pytest.mark.asyncio
    async def test_chat_client_make_request_with_tool_calls(self):
        client = ChatClient()
        
        # Mock the http_client post method
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": [{"message": {"content": "Response"}}]}
        client.http_client.post = AsyncMock(return_value=mock_response)
        
        messages = [
            {"role": "assistant", "tool_calls": [{"id": "1", "type": "function", "function": {"name": "test_function"}}]}
        ]
        
        await client.make_request(messages)
        
        # Check that tool_calls field was included in the message
        json_payload = client.http_client.post.call_args[1]["json"]
        assert "tool_calls" in json_payload["messages"][0]
        
    @patch.dict(os.environ, {
        'AZURE_OPENAI_API_KEY': 'test-key',
        'AZURE_OPENAI_CHAT_MODEL': 'gpt-4',
        'AZURE_OPENAI_CHAT_ENDPOINT': 'https://test.endpoint.com'
    })
    @pytest.mark.asyncio
    async def test_chat_client_make_request_with_tool_call_id(self):
        client = ChatClient()
        
        # Mock the http_client post method
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": [{"message": {"content": "Response"}}]}
        client.http_client.post = AsyncMock(return_value=mock_response)
        
        messages = [
            {"role": "tool", "tool_call_id": "test_id", "content": "Tool result"}
        ]
        
        await client.make_request(messages)
        
        # Check that tool_call_id field was included in the message
        json_payload = client.http_client.post.call_args[1]["json"]
        assert json_payload["messages"][0]["tool_call_id"] == "test_id"


class TestEmbeddingsClient:
    def test_embeddings_client_init(self):
        with patch.dict(os.environ, {
            'AZURE_OPENAI_API_KEY': 'test-key',
            'AZURE_OPENAI_EMBEDDINGS_MODEL': 'text-embedding-ada-002',
            'AZURE_OPENAI_EMBEDDINGS_ENDPOINT': 'https://test.endpoint.com'
        }):
            client = EmbeddingsClient()
            assert client.model == "text-embedding-ada-002"
            assert client.endpoint == "https://test.endpoint.com"

    @pytest.mark.asyncio
    async def test_embeddings_client_make_request_success(self):
        with patch.dict(os.environ, {
            'AZURE_OPENAI_API_KEY': 'test-key',
            'AZURE_OPENAI_EMBEDDINGS_MODEL': 'text-embedding-ada-002',
            'AZURE_OPENAI_EMBEDDINGS_ENDPOINT': 'https://test.endpoint.com'
        }):
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "data": [{"embedding": [0.1, 0.2, 0.3]}]
            }

            with patch('httpx.AsyncClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client.post.return_value = mock_response
                mock_client_class.return_value = mock_client

                client = EmbeddingsClient()
                messages = ["Test text for embedding"]
                
                result = await client.make_request(messages)
                
                assert result == {"data": [{"embedding": [0.1, 0.2, 0.3]}]}
                
                call_args = mock_client.post.call_args
                payload = call_args[1]['json']
                assert payload['input'] == "Test text for embedding"
                assert payload['model'] == "text-embedding-ada-002"

    @pytest.mark.asyncio
    async def test_embeddings_client_make_request_error(self):
        with patch.dict(os.environ, {
            'AZURE_OPENAI_API_KEY': 'test-key',
            'AZURE_OPENAI_EMBEDDINGS_MODEL': 'text-embedding-ada-002',
            'AZURE_OPENAI_EMBEDDINGS_ENDPOINT': 'https://test.endpoint.com'
        }):
            mock_response = Mock()
            mock_response.status_code = 429
            mock_response.json.return_value = {
                "error": {"message": "Rate limit exceeded"}
            }

            with patch('httpx.AsyncClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client.post.return_value = mock_response
                mock_client_class.return_value = mock_client

                client = EmbeddingsClient()
                messages = ["Test text"]
                
                with pytest.raises(Exception, match="Embeddings API error \\(429\\): Rate limit exceeded"):
                    await client.make_request(messages)

    @patch.dict(os.environ, {
        'AZURE_OPENAI_API_KEY': 'test-key',
        'AZURE_OPENAI_EMBEDDINGS_MODEL': 'text-embedding-ada-002',
        'AZURE_OPENAI_EMBEDDINGS_ENDPOINT': 'https://test-embedding.endpoint.com'
    })
    def test_embeddings_client_init_with_env_vars(self):
        client = EmbeddingsClient()
        assert client.api_key == "test-key"
        assert client.model == "text-embedding-ada-002"
        assert client.endpoint == "https://test-embedding.endpoint.com"

    @patch.dict(os.environ, {
        'AZURE_OPENAI_API_KEY': 'test-key',
    })
    def test_embeddings_client_init_with_params(self):
        client = EmbeddingsClient(
            model="custom-embedding-model",
            timeout=90.0
        )
        # The model can be overridden by environment variable AZURE_OPENAI_EMBEDDINGS_MODEL
        assert client.timeout == 90.0

    @patch.dict(os.environ, {
        'AZURE_OPENAI_API_KEY': 'test-key',
        'AZURE_OPENAI_EMBEDDINGS_MODEL': 'text-embedding-ada-002',
        'AZURE_OPENAI_EMBEDDINGS_ENDPOINT': 'https://test-embedding.endpoint.com'
    })
    @pytest.mark.asyncio
    async def test_embeddings_client_make_request(self):
        client = EmbeddingsClient()
        
        # Mock the http_client post method
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [{"embedding": [0.1, 0.2, 0.3]}],
            "model": "text-embedding-ada-002"
        }
        client.http_client.post = AsyncMock(return_value=mock_response)
        
        messages = ["This is a test text"]
        
        result = await client.make_request(messages)
        
        assert result == {
            "data": [{"embedding": [0.1, 0.2, 0.3]}],
            "model": "text-embedding-ada-002"
        }
        
        # Check that post was called with the right arguments
        client.http_client.post.assert_called_once()
        call_args = client.http_client.post.call_args
        assert call_args[0][0] == "https://test-embedding.endpoint.com"
        
        # Check payload
        json_payload = call_args[1]["json"]
        assert json_payload["model"] == "text-embedding-ada-002"
        assert json_payload["input"] == "This is a test text"

    @patch.dict(os.environ, {
        'AZURE_OPENAI_API_KEY': 'test-key',
        'AZURE_OPENAI_EMBEDDINGS_MODEL': 'text-embedding-ada-002',
        'AZURE_OPENAI_EMBEDDINGS_ENDPOINT': 'https://test-embedding.endpoint.com'
    })
    @pytest.mark.asyncio
    async def test_embeddings_client_make_request_error(self):
        client = EmbeddingsClient()
        
        # Mock the http_client post method to return an error
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": {"message": "Invalid input"}}
        client.http_client.post = AsyncMock(return_value=mock_response)
        
        messages = ["This is a test text"]
        
        with pytest.raises(Exception, match="Embeddings API error \\(400\\): Invalid input"):
            await client.make_request(messages)


class TestChat:
    def test_chat_init(self):
        mock_tool = Mock(spec=Tool)
        mock_tool.name = "mock_tool"
        mock_tool.define.return_value = {"type": "function", "function": {"name": "mock_tool"}}
        
        with patch('src.core.llm.chat.ChatClient') as mock_client_class:
            chat = Chat([mock_tool])
            
            # Verify ChatClient was initialized
            mock_client_class.assert_called_once()
            
            # Verify tool was added correctly
            assert "mock_tool" in chat.tool_map
            assert chat.tool_map["mock_tool"] == mock_tool
            assert len(chat.tools) == 1
            assert chat.tools[0] == {"type": "function", "function": {"name": "mock_tool"}}

    def test_chat_add_tool(self):
        mock_tool1 = Mock(spec=Tool)
        mock_tool1.name = "tool1"
        mock_tool1.define.return_value = {"type": "function", "function": {"name": "tool1"}}
        
        mock_tool2 = Mock(spec=Tool)
        mock_tool2.name = "tool2"
        mock_tool2.define.return_value = {"type": "function", "function": {"name": "tool2"}}
        
        with patch('src.core.llm.chat.ChatClient'):
            chat = Chat([mock_tool1])
            chat.add_tool(mock_tool2)
            
            # Verify both tools are in the map
            assert "tool1" in chat.tool_map
            assert "tool2" in chat.tool_map
            assert len(chat.tools) == 2
            
            tool_names = [t["function"]["name"] for t in chat.tools]
            assert "tool1" in tool_names
            assert "tool2" in tool_names

    @patch.dict(os.environ, {
        'AZURE_OPENAI_API_KEY': 'test-key',
    })
    def test_chat_create_classmethod(self):
        mock_tool = Mock(spec=Tool)
        mock_tool.name = "mock_tool"
        mock_tool.define.return_value = {"type": "function", "function": {"name": "mock_tool"}}
        
        with patch('src.core.llm.chat.ChatClient'):
            chat = Chat.create([mock_tool])
            
            # Verify it created a Chat instance with the tools
            assert isinstance(chat, Chat)
            assert "mock_tool" in chat.tool_map
            assert len(chat.tools) == 1

    @patch.dict(os.environ, {
        'AZURE_OPENAI_API_KEY': 'test-key',
    })
    @pytest.mark.asyncio
    async def test_chat_send_messages(self):
        with patch('src.core.llm.chat.ChatClient') as mock_client_class:
            # Setup mock client
            mock_client = Mock()
            mock_client.make_request = AsyncMock(return_value={"choices": [{"message": {"content": "Response"}}]})
            mock_client_class.return_value = mock_client
            
            # Create chat and test send_messages
            chat = Chat()
            messages = [
                {"role": "system", "content": "You are an assistant"},
                {"role": "user", "content": "Hello"}
            ]
            
            result = await chat.send_messages(messages)
            
            # Verify make_request was called correctly
            mock_client.make_request.assert_called_once()
            call_args = mock_client.make_request.call_args
            assert "messages" in call_args.kwargs
            assert call_args.kwargs["messages"] == messages
            assert call_args.kwargs["tools"] == []  # No tools passed
            
            # Verify result
            assert result == {"choices": [{"message": {"content": "Response"}}]}

    @patch.dict(os.environ, {
        'AZURE_OPENAI_API_KEY': 'test-key',
    })
    @pytest.mark.asyncio
    async def test_chat_send_messages_with_tools(self):
        with patch('src.core.llm.chat.ChatClient') as mock_client_class:
            # Setup mock client
            mock_client = Mock()
            mock_client.make_request = AsyncMock(return_value={"choices": [{"message": {"content": "Response"}}]})
            mock_client_class.return_value = mock_client
            
            # Setup mock tool
            mock_tool = Mock(spec=Tool)
            mock_tool.name = "mock_tool"
            mock_tool.define.return_value = {"type": "function", "function": {"name": "mock_tool"}}
            
            # Create chat and test send_messages
            chat = Chat([mock_tool])
            messages = [{"role": "user", "content": "Use the tool"}]
            
            result = await chat.send_messages(messages)
            
            # Verify make_request was called with tools
            mock_client.make_request.assert_called_once()
            call_args = mock_client.make_request.call_args
            assert call_args[1]["tools"] == [{"type": "function", "function": {"name": "mock_tool"}}]

    @patch.dict(os.environ, {
        'AZURE_OPENAI_API_KEY': 'test-key',
    })
    @pytest.mark.asyncio
    async def test_chat_process_tool_calls(self):
        with patch('src.core.llm.chat.ChatClient'):
            # Setup mock tool
            mock_tool = Mock(spec=Tool)
            mock_tool.name = "mock_tool"
            mock_tool.run = AsyncMock(return_value={"result": "Tool executed"})
            mock_tool.define.return_value = {"type": "function", "function": {"name": "mock_tool"}}
            
            # Create chat instance
            chat = Chat([mock_tool])
            
            # Setup message with tool calls
            message = {
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": "call_123",
                        "type": "function",
                        "function": {
                            "name": "mock_tool",
                            "arguments": '{"param": "value"}'
                        }
                    }
                ]
            }
            
            # Mock callback function
            callback_mock = Mock()
            
            # Process tool calls
            await chat.process_tool_calls(message, callback_mock)
            
            # Verify tool was called
            mock_tool.run.assert_called_once_with(param="value")
            
            # Verify callback was called with appropriate messages
            assert callback_mock.call_count == 1
            tool_response_msg = callback_mock.call_args[0][0]
            assert tool_response_msg["role"] == "tool"
            assert tool_response_msg["tool_call_id"] == "call_123"
            assert json.loads(tool_response_msg["content"])["result"] == "Tool executed"

    @patch.dict(os.environ, {
        'AZURE_OPENAI_API_KEY': 'test-key',
    })
    @pytest.mark.asyncio
    async def test_chat_process_tool_calls_with_invalid_json(self):
        with patch('src.core.llm.chat.ChatClient'):
            # Setup mock tool
            mock_tool = Mock(spec=Tool)
            mock_tool.name = "mock_tool"
            mock_tool.run = AsyncMock(return_value={"result": "Tool executed"})
            mock_tool.define.return_value = {"type": "function", "function": {"name": "mock_tool"}}
            
            # Create chat instance
            chat = Chat([mock_tool])
            
            # Setup message with tool calls but invalid JSON arguments
            message = {
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": "call_123",
                        "type": "function",
                        "function": {
                            "name": "mock_tool",
                            "arguments": '{invalid json}'  # Invalid JSON
                        }
                    }
                ]
            }
            
            # Mock callback function
            callback_mock = Mock()
            
            # Process tool calls should handle the error gracefully
            await chat.process_tool_calls(message, callback_mock)
            
            # Verify tool was called with empty dict due to invalid JSON
            mock_tool.run.assert_called_once_with()
            
            # Verify callback was called
            assert callback_mock.call_count == 1
            tool_response_msg = callback_mock.call_args[0][0]
            assert tool_response_msg["role"] == "tool"
            assert tool_response_msg["tool_call_id"] == "call_123"
            # The implementation doesn't include an error message for JSON decode errors,
            # it just uses an empty dict for args

    @patch.dict(os.environ, {
        'AZURE_OPENAI_API_KEY': 'test-key',
    })
    @pytest.mark.asyncio
    async def test_chat_process_tool_calls_tool_not_found(self):
        with patch('src.core.llm.chat.ChatClient'):
            # Create chat instance with no tools
            chat = Chat()
            
            # Setup message with tool calls for non-existent tool
            message = {
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": "call_123",
                        "type": "function",
                        "function": {
                            "name": "nonexistent_tool",
                            "arguments": '{}'
                        }
                    }
                ]
            }
            
            # Mock callback function
            callback_mock = Mock()
            
            # Process tool calls
            await chat.process_tool_calls(message, callback_mock)
            
            # Verify callback was called with error message
            assert callback_mock.call_count == 1
            tool_response_msg = callback_mock.call_args[0][0]
            assert tool_response_msg["role"] == "tool"
            assert tool_response_msg["tool_call_id"] == "call_123"
            error_content = json.loads(tool_response_msg["content"])
            assert "error" in error_content
            # The actual error message includes the full tool name
            assert "Tool 'nonexistent_tool' not found" in error_content["error"]

    @patch.dict(os.environ, {
        'AZURE_OPENAI_API_KEY': 'test-key',
    })
    @pytest.mark.asyncio
    async def test_chat_process_tool_calls_exception_in_tool(self):
        with patch('src.core.llm.chat.ChatClient'):
            # Setup mock tool that raises an exception
            mock_tool = Mock(spec=Tool)
            mock_tool.name = "mock_tool"
            mock_tool.run = AsyncMock(side_effect=Exception("Tool execution failed"))
            mock_tool.define.return_value = {"type": "function", "function": {"name": "mock_tool"}}
            
            # Create chat instance
            chat = Chat([mock_tool])
            
            # Setup message with tool calls
            message = {
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": "call_123",
                        "type": "function",
                        "function": {
                            "name": "mock_tool",
                            "arguments": '{}'
                        }
                    }
                ]
            }
            
            # Mock callback function
            callback_mock = Mock()
            
            # Process tool calls should handle the exception
            await chat.process_tool_calls(message, callback_mock)
            
            # Verify callback was called with error message
            assert callback_mock.call_count == 1
            tool_response_msg = callback_mock.call_args[0][0]
            assert tool_response_msg["role"] == "tool"
            assert tool_response_msg["tool_call_id"] == "call_123"
            error_content = json.loads(tool_response_msg["content"])
            assert "error" in error_content
            assert "Tool execution failed" in error_content["error"]
