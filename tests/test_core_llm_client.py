import asyncio
import os
import pytest
from unittest.mock import patch, Mock, AsyncMock
import httpx

from core.llm.client import Client, ChatClient, EmbeddingsClient


class TestClient:
    def test_client_init_success(self):
        with patch.dict(os.environ, {"AZURE_OPENAI_API_KEY": "test_key"}):
            client = Client("test_model", "https://test.endpoint.com")
            assert client.model == "test_model"
            assert client.endpoint == "https://test.endpoint.com"
            assert client.api_key == "test_key"

    def test_client_init_missing_api_key(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="API key, model, and endpoint must be provided"):
                Client("test_model", "https://test.endpoint.com")

    def test_client_init_missing_model(self):
        with patch.dict(os.environ, {"AZURE_OPENAI_API_KEY": "test_key"}):
            with pytest.raises(ValueError, match="API key, model, and endpoint must be provided"):
                Client(None, "https://test.endpoint.com")

    def test_client_init_missing_endpoint(self):
        with patch.dict(os.environ, {"AZURE_OPENAI_API_KEY": "test_key"}):
            with pytest.raises(ValueError, match="API key, model, and endpoint must be provided"):
                Client("test_model", None)

    def test_client_timeout_setting(self):
        with patch.dict(os.environ, {"AZURE_OPENAI_API_KEY": "test_key"}):
            client = Client("test_model", "https://test.endpoint.com", timeout=60.0)
            assert client.timeout == 60.0

    @pytest.mark.asyncio
    async def test_client_make_request_not_implemented(self):
        with patch.dict(os.environ, {"AZURE_OPENAI_API_KEY": "test_key"}):
            client = Client("test_model", "https://test.endpoint.com")
            with pytest.raises(NotImplementedError):
                await client.make_request([])


class TestEmbeddingsClient:
    def setup_method(self):
        self.env_vars = {
            "AZURE_OPENAI_API_KEY": "test_key",
            "AZURE_OPENAI_EMBEDDINGS_MODEL": "test_embedding_model",
            "AZURE_OPENAI_EMBEDDINGS_ENDPOINT": "https://test.embeddings.endpoint.com"
        }

    @patch.dict(os.environ, {})
    def test_embeddings_client_init_with_env_vars(self):
        with patch.dict(os.environ, self.env_vars):
            client = EmbeddingsClient()
            assert client.model == "test_embedding_model"
            assert client.endpoint == "https://test.embeddings.endpoint.com"

    @patch.dict(os.environ, {"AZURE_OPENAI_API_KEY": "test_key", "AZURE_OPENAI_EMBEDDINGS_ENDPOINT": "test_endpoint"}, clear=True)
    def test_embeddings_client_init_with_params(self):
        client = EmbeddingsClient("custom_model")
        assert client.model == "custom_model"

    @pytest.mark.asyncio
    async def test_embeddings_client_make_request_success(self):
        with patch.dict(os.environ, self.env_vars):
            client = EmbeddingsClient()
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "data": [{"embedding": [0.1, 0.2, 0.3]}]
            }
            
            with patch.object(client.http_client, 'post', return_value=mock_response) as mock_post:
                result = await client.make_request(["test text"])
                
                assert result == {"data": [{"embedding": [0.1, 0.2, 0.3]}]}
                mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_embeddings_client_make_request_error(self):
        with patch.dict(os.environ, self.env_vars):
            client = EmbeddingsClient()
            
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.json.return_value = {
                "error": {"message": "Bad request"}
            }
            
            with patch.object(client.http_client, 'post', return_value=mock_response):
                with pytest.raises(Exception, match="Embeddings API error"):
                    await client.make_request(["test text"])


class TestChatClient:
    def setup_method(self):
        self.env_vars = {
            "AZURE_OPENAI_API_KEY": "test_key",
            "AZURE_OPENAI_CHAT_MODEL": "test_chat_model",
            "AZURE_OPENAI_CHAT_ENDPOINT": "https://test.chat.endpoint.com"
        }

    @patch.dict(os.environ, {})
    def test_chat_client_init_with_env_vars(self):
        with patch.dict(os.environ, self.env_vars):
            client = ChatClient()
            assert client.model == "test_chat_model"
            assert client.endpoint == "https://test.chat.endpoint.com"

    @patch.dict(os.environ, {"AZURE_OPENAI_API_KEY": "test_key", "AZURE_OPENAI_CHAT_ENDPOINT": "test_endpoint"}, clear=True)
    def test_chat_client_init_with_params(self):
        client = ChatClient("custom_model")
        assert client.model == "custom_model"

    @pytest.mark.asyncio
    async def test_chat_client_make_request_success(self):
        with patch.dict(os.environ, self.env_vars):
            client = ChatClient()
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "test response"}}]
            }
            
            with patch.object(client.http_client, 'post', return_value=mock_response) as mock_post:
                messages = [{"role": "user", "content": "test"}]
                result = await client.make_request(messages)
                
                assert result == {"choices": [{"message": {"content": "test response"}}]}
                mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_chat_client_make_request_with_tools(self):
        with patch.dict(os.environ, self.env_vars):
            client = ChatClient()
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"choices": []}
            
            with patch.object(client.http_client, 'post', return_value=mock_response) as mock_post:
                messages = [{"role": "user", "content": "test"}]
                tools = [{"type": "function", "function": {"name": "test_tool"}}]
                
                await client.make_request(messages, tools=tools)
                
                call_args = mock_post.call_args
                payload = call_args[1]['json']
                assert "tools" in payload
                assert payload["tools"] == tools

    @pytest.mark.asyncio
    async def test_chat_client_make_request_error(self):
        with patch.dict(os.environ, self.env_vars):
            client = ChatClient()
            
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.json.return_value = {
                "error": {"message": "Internal server error"}
            }
            
            with patch.object(client.http_client, 'post', return_value=mock_response):
                with pytest.raises(Exception, match="API error"):
                    await client.make_request([{"role": "user", "content": "test"}])

    @pytest.mark.asyncio
    async def test_chat_client_message_processing(self):
        with patch.dict(os.environ, self.env_vars):
            client = ChatClient()
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"choices": []}
            
            with patch.object(client.http_client, 'post', return_value=mock_response) as mock_post:
                messages = [
                    {"role": "user", "content": "test", "name": "user1"},
                    {"role": "tool", "content": "result", "tool_call_id": "123"},
                    {"role": "assistant", "content": None, "tool_calls": [{"id": "call_123", "function": {"name": "test"}}]}
                ]
                
                await client.make_request(messages)
                
                call_args = mock_post.call_args
                payload = call_args[1]['json']
                processed_messages = payload["messages"]
                
                # Check that None content is not included
                assert len(processed_messages) == 3
                assert "name" in processed_messages[0]
                assert "tool_call_id" in processed_messages[1]
                assert "tool_calls" in processed_messages[2]
