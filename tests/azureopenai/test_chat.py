"""
Tests for Azure OpenAI chat module.
"""
import os
from unittest import mock
import pytest

from src.azureopenai.chat import Chat, ResponseOptions
from src.azureopenai.client import Message, Response


@pytest.fixture
def mock_client():
    """Fixture for a mock chat client."""
    mock_client = mock.MagicMock()
    mock_client.get_completion.return_value = "Test completion response"
    
    mock_response = mock.MagicMock()
    mock_response.to_json.return_value = '{"choices":[{"message":{"content":"Test JSON response"}}]}'
    mock_client.make_request.return_value = mock_response
    
    return mock_client


def test_chat_create():
    """Test Chat.create with environment variables."""
    # Mock environment variables
    with mock.patch.dict(os.environ, {"AZURE_OPENAI_API_KEY": "test-key"}):
        with mock.patch("src.azureopenai.chat.Client") as mock_client_class:
            chat = Chat.create()
            
            # Verify client was created with the API key
            mock_client_class.assert_called_once_with(api_key="test-key")
            assert chat.client == mock_client_class.return_value


def test_chat_create_missing_api_key():
    """Test Chat.create without API key environment variable."""
    # Ensure environment variable is not set
    with mock.patch.dict(os.environ, clear=True):
        with pytest.raises(ValueError) as exc_info:
            Chat.create()
        
        assert "AZURE_OPENAI_API_KEY environment variable is required" in str(exc_info.value)


def test_send_prompt(mock_client):
    """Test sending a prompt and getting a response."""
    chat = Chat(mock_client)
    
    response = chat.send_prompt(
        system_role="You are a helpful assistant",
        user_prompt="Hello, world!"
    )
    
    # Verify correct messages were sent
    mock_client.get_completion.assert_called_once()
    args, kwargs = mock_client.get_completion.call_args
    
    assert len(args[0]) == 2  # Two messages
    assert args[0][0].role == "system"
    assert args[0][0].content == "You are a helpful assistant"
    assert args[0][1].role == "user"
    assert args[0][1].content == "Hello, world!"
    
    # Verify default parameters
    assert kwargs["temperature"] == 0.5
    assert kwargs["max_tokens"] == 500
    
    # Verify correct response is returned
    assert response == "Test completion response"


def test_send_prompt_with_options(mock_client):
    """Test sending a prompt with additional options."""
    chat = Chat(mock_client)
    
    options = ResponseOptions(
        temperature=0.8,
        max_tokens=1000,
        tools={"function": {"name": "test_function"}}
    )
    
    response = chat.send_prompt_with_options(
        system_role="You are a helpful assistant",
        user_prompt="Hello, world!",
        opts=options
    )
    
    # Verify correct messages were sent
    mock_client.make_request.assert_called_once()
    args, kwargs = mock_client.make_request.call_args
    
    assert len(args[0]) == 2  # Two messages
    assert kwargs["temperature"] == 0.8
    assert kwargs["max_tokens"] == 1000
    assert kwargs["tools"] == {"function": {"name": "test_function"}}
    
    # Verify response was converted to JSON
    mock_client.make_request.return_value.to_json.assert_called_once()
    assert response == '{"choices":[{"message":{"content":"Test JSON response"}}]}'


def test_send_followup(mock_client):
    """Test sending a follow-up with raw messages."""
    chat = Chat(mock_client)
    
    previous_messages = [
        {"role": "user", "content": "First message"},
        {"role": "assistant", "content": "First response"}
    ]
    
    response = chat.send_followup(
        messages=previous_messages,
        user_prompt="Follow-up question"
    )
    
    # Verify the raw messages were sent correctly
    mock_client.make_request.assert_called_once()
    args, kwargs = mock_client.make_request.call_args
    
    # Check that raw_messages were set correctly
    assert len(args[0]) == 1
    assert args[0][0].role == "user"
    assert args[0][0].content == "Follow-up question"
    assert args[0][0].raw_messages == previous_messages
    
    # Verify correct response is returned
    mock_client.make_request.return_value.choices[0].message.get.return_value = "Follow-up response"
    assert mock_client.make_request.return_value.choices[0].message.get.call_args[0][0] == "content"