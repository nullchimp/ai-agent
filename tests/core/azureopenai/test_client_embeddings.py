import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from core.azureopenai.client import Client


@pytest.mark.asyncio
async def test_make_embeddings_request_success():
    """Test successful embedding request"""
    client = Client(api_key="test_key")
    
    # Mock the HTTP client post method
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": [{"embedding": [0.1, 0.2, 0.3]}],
        "model": "text-embedding-ada-002"
    }
    
    client.http_client.post = AsyncMock(return_value=mock_response)
    
    # Call the method
    result = await client.make_embeddings_request(
        input="test text",
        model="text-embedding-ada-002"
    )
    
    # Verify the result
    assert "data" in result
    assert len(result["data"]) == 1
    assert result["data"][0]["embedding"] == [0.1, 0.2, 0.3]
    
    # Verify the HTTP client was called correctly
    client.http_client.post.assert_called_once()
    args = client.http_client.post.call_args
    assert "text-embedding-ada-002" in args[1]["json"]["model"]


@pytest.mark.asyncio
async def test_make_embeddings_request_endpoint_formatting():
    """Test that the endpoint is correctly formatted for embeddings"""
    # Test various endpoint formats
    endpoint_tests = [
        # Original endpoint, expected result
        ("https://api.azure.com/openai/v1/chat/completions", 
         "https://api.azure.com/openai/v1/embeddings"),
        ("https://api.azure.com/openai/v1", 
         "https://api.azure.com/openai/v1/embeddings"),
        ("https://api.azure.com/openai/v1/", 
         "https://api.azure.com/openai/v1/embeddings"),
        ("https://api.azure.com/openai/v1/embeddings", 
         "https://api.azure.com/openai/v1/embeddings")
    ]
    
    for original, expected in endpoint_tests:
        client = Client(api_key="test_key", endpoint=original)
        
        # Mock the HTTP client post method
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [{"embedding": [0.1, 0.2, 0.3]}]
        }
        
        client.http_client.post = AsyncMock(return_value=mock_response)
        
        # Call the method
        await client.make_embeddings_request(input="test")
        
        # Verify the endpoint was correctly formatted
        client.http_client.post.assert_called_once()
        assert client.http_client.post.call_args[0][0] == expected


@pytest.mark.asyncio
async def test_make_embeddings_request_error():
    """Test error handling in embedding request"""
    client = Client(api_key="test_key")
    
    # Mock the HTTP client post method to return an error
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.json.return_value = {
        "error": {
            "message": "Invalid request"
        }
    }
    
    client.http_client.post = AsyncMock(return_value=mock_response)
    
    # Call the method and expect an exception
    with pytest.raises(Exception) as excinfo:
        await client.make_embeddings_request(input="test text")
    
    # Verify the exception message
    assert "Embeddings API error" in str(excinfo.value)
    assert "Invalid request" in str(excinfo.value)


@pytest.mark.asyncio
async def test_make_embeddings_request_batch():
    """Test embedding request with batched input"""
    client = Client(api_key="test_key")
    
    # Mock the HTTP client post method
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": [
            {"embedding": [0.1, 0.2, 0.3]},
            {"embedding": [0.4, 0.5, 0.6]}
        ]
    }
    
    client.http_client.post = AsyncMock(return_value=mock_response)
    
    # Call the method with a list of inputs
    result = await client.make_embeddings_request(
        input=["text1", "text2"],
        model="text-embedding-ada-002"
    )
    
    # Verify the result
    assert "data" in result
    assert len(result["data"]) == 2
    assert result["data"][0]["embedding"] == [0.1, 0.2, 0.3]
    assert result["data"][1]["embedding"] == [0.4, 0.5, 0.6]
    
    # Verify the HTTP client was called with the correct batch input
    client.http_client.post.assert_called_once()
    args = client.http_client.post.call_args
    assert args[1]["json"]["input"] == ["text1", "text2"]