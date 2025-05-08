"""
Tests for Azure OpenAI client module.
"""
import json
from unittest import mock
import pytest

# Import modules using relative imports
from src.azureopenai.client import Client, Message, Response


@pytest.fixture
def mock_response():
    """Fixture for a mock API response."""
    return {
        "choices": [
            {
                "message": {
                    "content": "This is a test response",
                    "role": "assistant"
                }
            }
        ]
    }


@pytest.fixture
def mock_httpx_client():
    """Fixture for a mock HTTPX client."""
    with mock.patch("httpx.Client") as mock_client:
        # Configure the mock post method response
        mock_client.return_value.post.return_value = mock.MagicMock(
            status_code=200,
            json=mock.MagicMock(return_value={"choices": [{"message": {"content": "This is a test response"}}]})
        )
        yield mock_client.return_value


def test_client_initialization():
    """Test client initialization with default parameters."""
    client = Client(api_key="test-key")
    
    assert client.api_key == "test-key"
    assert client.endpoint is not None
    assert client.timeout == 30.0


def test_make_request_success(mock_httpx_client):
    """Test successful API request."""
    client = Client(api_key="test-key")
    client.http_client = mock_httpx_client
    
    messages = [Message(role="user", content="Hello")]
    response = client.make_request(messages)
    
    # Verify the request was made with correct parameters
    mock_httpx_client.post.assert_called_once()
    _, kwargs = mock_httpx_client.post.call_args
    
    assert kwargs["headers"]["api-key"] == "test-key"
    assert kwargs["headers"]["Content-Type"] == "application/json"
    
    # Check the payload structure
    payload = kwargs["json"]
    assert payload["model"] == "custom-gpt-4.1"
    assert payload["temperature"] == 0.7
    assert len(payload["messages"]) == 1
    assert payload["messages"][0]["role"] == "user"
    assert payload["messages"][0]["content"] == "Hello"
    
    # Verify response parsing
    assert isinstance(response, Response)
    assert len(response.choices) == 1
    assert response.choices[0].message["content"] == "This is a test response"


def test_make_request_with_raw_messages(mock_httpx_client):
    """Test request with raw messages for tool responses."""
    client = Client(api_key="test-key")
    client.http_client = mock_httpx_client
    
    raw_messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": None, "tool_calls": [{"id": "1", "type": "function"}]}
    ]
    
    messages = [Message(role="user", raw_messages=raw_messages)]
    response = client.make_request(messages)
    
    # Verify raw messages were sent correctly
    _, kwargs = mock_httpx_client.post.call_args
    payload = kwargs["json"]
    assert payload["messages"] == raw_messages


def test_get_completion(mock_httpx_client):
    """Test get_completion convenience method."""
    client = Client(api_key="test-key")
    client.http_client = mock_httpx_client
    
    messages = [Message(role="user", content="Hello")]
    result = client.get_completion(messages)
    
    assert result == "This is a test response"


def test_response_to_json():
    """Test Response.to_json() method."""
    response_data = {
        "choices": [
            {
                "message": {
                    "content": "Test content",
                    "role": "assistant"
                }
            }
        ]
    }
    
    response = Response(response_data)
    json_output = response.to_json()
    
    # Verify JSON serialization
    parsed = json.loads(json_output)
    assert "choices" in parsed
    assert len(parsed["choices"]) == 1
    assert parsed["choices"][0]["message"]["content"] == "Test content"


def test_make_request_error(mock_httpx_client):
    """Test error handling in make_request."""
    client = Client(api_key="test-key")
    client.http_client = mock_httpx_client
    
    # Configure mock to return an error
    mock_httpx_client.post.return_value = mock.MagicMock(
        status_code=400,
        json=mock.MagicMock(return_value={"error": {"message": "Invalid request"}})
    )
    
    messages = [Message(role="user", content="Hello")]
    
    # Test that exception is raised with proper error message
    with pytest.raises(Exception) as exc_info:
        client.make_request(messages)
    
    assert "API error (400): Invalid request" in str(exc_info.value)