import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import os

from core.azureopenai.client import Client
from core.rag.embedding_service import EmbeddingService


@pytest.mark.asyncio
async def test_get_embedding_with_openai():
    """Test getting embeddings using Azure OpenAI"""
    # Mock the Azure OpenAI client
    mock_client = MagicMock()
    mock_client.make_embeddings_request = AsyncMock(return_value={
        "data": [{"embedding": [0.1, 0.2, 0.3]}],
    })
    
    # Create the embedding service with local fallback disabled
    service = EmbeddingService(mock_client, use_local_fallback=False)
    
    # Get embedding
    embedding = await service.get_embedding("test text", use_openai=True)
    
    # Verify the result
    assert embedding == [0.1, 0.2, 0.3]
    
    # Verify the client was called correctly
    mock_client.make_embeddings_request.assert_called_once_with(
        input="test text",
        model="text-embedding-3-small"
    )


@pytest.mark.asyncio
async def test_get_embedding_with_fallback():
    """Test fallback to local model when Azure OpenAI fails"""
    # Mock the Azure OpenAI client to raise an exception
    mock_client = MagicMock()
    mock_client.make_embeddings_request = AsyncMock(side_effect=Exception("API error"))
    
    # Mock the SentenceTransformer
    with patch("sentence_transformers.SentenceTransformer") as mock_transformer_class:
        mock_model = MagicMock()
        mock_model.encode.return_value = [0.4, 0.5, 0.6]
        mock_transformer_class.return_value = mock_model
        
        # Create the embedding service
        service = EmbeddingService(mock_client)
        
        # Get embedding
        embedding = await service.get_embedding("test text", use_openai=True)
        
        # Verify the result
        assert embedding == [0.4, 0.5, 0.6]
        
        # Verify the local model was used
        mock_model.encode.assert_called_once_with("test text")


@pytest.mark.asyncio
async def test_get_embedding_no_models_available():
    """Test error when no models are available"""
    # Mock the Azure OpenAI client to raise an exception
    mock_client = MagicMock()
    mock_client.make_embeddings_request = AsyncMock(side_effect=Exception("API error"))
    
    # Create the embedding service with local fallback disabled
    service = EmbeddingService(mock_client, use_local_fallback=False)
    
    # Attempt to get embedding
    with pytest.raises(ValueError, match="No embedding model available"):
        await service.get_embedding("test text", use_openai=False)


@pytest.mark.asyncio
async def test_get_embeddings_batch():
    """Test getting embeddings for a batch of texts"""
    # Mock the Azure OpenAI client
    mock_client = MagicMock()
    mock_client.make_embeddings_request = AsyncMock()
    mock_client.make_embeddings_request.side_effect = [
        {"data": [{"embedding": [0.1, 0.2, 0.3]}]},
        {"data": [{"embedding": [0.4, 0.5, 0.6]}]}
    ]
    
    # Create the embedding service with local fallback disabled
    service = EmbeddingService(mock_client, use_local_fallback=False)
    
    # Get embeddings for a batch of texts
    embeddings = await service.get_embeddings(["text1", "text2"], use_openai=True)
    
    # Verify the results
    assert embeddings == [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
    
    # Verify the client was called correctly
    assert mock_client.make_embeddings_request.call_count == 2


@pytest.mark.asyncio
async def test_direct_local_model():
    """Test using the local model directly without trying OpenAI"""
    # Mock the SentenceTransformer
    with patch("sentence_transformers.SentenceTransformer") as mock_transformer_class:
        mock_model = MagicMock()
        mock_model.encode.return_value = [0.4, 0.5, 0.6]
        mock_transformer_class.return_value = mock_model
        
        # Create the embedding service
        service = EmbeddingService(MagicMock())
        
        # Get embedding using local model directly
        embedding = await service.get_embedding("test text", use_openai=False)
        
        # Verify the result
        assert embedding == [0.4, 0.5, 0.6]
        
        # Verify the local model was used
        mock_model.encode.assert_called_once_with("test text")