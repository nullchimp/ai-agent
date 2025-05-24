import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import List

from src.core.rag.embedder import EmbeddingService
from src.core.rag.embedder.text_embedding_3_small import TextEmbedding3Small
from src.core.rag.schema import DocumentChunk, Vector


class TestEmbeddingService:
    def test_embedding_service_init(self):
        with patch('src.core.rag.embedder.EmbeddingsClient') as mock_client_class:
            service = EmbeddingService()
            assert service._client is not None
            mock_client_class.assert_called_once()

    def test_get_index_config_not_implemented(self):
        service = EmbeddingService()
        
        with pytest.raises(NotImplementedError, match="Subclasses should implement this method"):
            service.get_index_config()

    @pytest.mark.asyncio
    async def test_get_embedding(self):
        with patch('src.core.rag.embedder.EmbeddingsClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            
            service = EmbeddingService()
            service._make_embedding_request = AsyncMock(return_value=[0.1, 0.2, 0.3])
            
            result = await service.get_embedding("test text")
            
            assert result == [0.1, 0.2, 0.3]
            service._make_embedding_request.assert_called_once_with("test text")

    @pytest.mark.asyncio
    async def test_process_chunk_success(self):
        with patch('src.core.rag.embedder.EmbeddingsClient'):
            service = EmbeddingService()
            service._make_embedding_request = AsyncMock(return_value=[0.1, 0.2, 0.3])
            
            chunk = DocumentChunk(
                path="/test/path",
                content="test content",
                parent_id="parent123"
            )
            
            callback_results = []
            def callback(vector):
                callback_results.append(vector)
            
            await service.process_chunk(chunk, callback)
            
            assert len(callback_results) == 1
            vector = callback_results[0]
            assert isinstance(vector, Vector)
            assert vector.chunk_id == chunk.id
            assert vector.embedding == [0.1, 0.2, 0.3]
            assert vector.vector_store_id is None

    @pytest.mark.asyncio
    async def test_process_chunk_without_callback(self):
        with patch('src.core.rag.embedder.EmbeddingsClient'):
            service = EmbeddingService()
            service._make_embedding_request = AsyncMock(return_value=[0.1, 0.2, 0.3])
            
            chunk = DocumentChunk(
                path="/test/path",
                content="test content",
                parent_id="parent123"
            )
            
            # Should not raise an exception
            await service.process_chunk(chunk)

    @pytest.mark.asyncio
    async def test_process_chunk_embedding_error(self):
        with patch('src.core.rag.embedder.EmbeddingsClient'):
            service = EmbeddingService()
            service._make_embedding_request = AsyncMock(side_effect=Exception("API Error"))
            
            chunk = DocumentChunk(
                path="/test/path",
                content="test content",
                parent_id="parent123"
            )
            
            with pytest.raises(ValueError, match="Failed to get embedding: API Error"):
                await service.process_chunk(chunk)

    @pytest.mark.asyncio
    async def test_process_chunks_batch_processing(self):
        with patch('src.core.rag.embedder.EmbeddingsClient'):
            service = EmbeddingService()
            service._make_embedding_request = AsyncMock(return_value=[0.1, 0.2, 0.3])
            
            chunks = [
                DocumentChunk(path=f"/test/path{i}", content=f"content{i}", parent_id="parent")
                for i in range(3)
            ]
            
            callback_results = []
            def callback(vector):
                callback_results.append(vector)
            
            await service.process_chunks(chunks, callback)
            
            assert len(callback_results) == 3
            assert all(isinstance(v, Vector) for v in callback_results)

    @pytest.mark.asyncio
    async def test_process_chunks_large_batch(self):
        with patch('src.core.rag.embedder.EmbeddingsClient'):
            service = EmbeddingService()
            service._make_embedding_request = AsyncMock(return_value=[0.1, 0.2, 0.3])
            
            # Create 12 chunks to test batching (default batch size is 5)
            chunks = [
                DocumentChunk(path=f"/test/path{i}", content=f"content{i}", parent_id="parent")
                for i in range(12)
            ]
            
            callback_results = []
            def callback(vector):
                callback_results.append(vector)
            
            await service.process_chunks(chunks, callback)
            
            assert len(callback_results) == 12

    @pytest.mark.asyncio
    async def test_search_similar(self):
        with patch('src.core.rag.embedder.EmbeddingsClient'):
            service = EmbeddingService()
            service._make_embedding_request = AsyncMock(return_value=[0.1, 0.2, 0.3])
            
            mock_vector_store = AsyncMock()
            mock_vector_store.search.return_value = [
                {"id": "1", "similarity": 0.9},
                {"id": "2", "similarity": 0.8}
            ]
            service._vector_store = mock_vector_store
            
            result = await service.search_similar("test query", limit=2)
            
            assert len(result) == 2
            assert result[0]["similarity"] == 0.9
            service._make_embedding_request.assert_called_once_with("test query")
            mock_vector_store.search.assert_called_once_with([0.1, 0.2, 0.3], 2)

    @pytest.mark.asyncio
    async def test_make_embedding_request_success(self):
        with patch('src.core.rag.embedder.EmbeddingsClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = {
                "data": [{"embedding": [0.1, 0.2, 0.3]}]
            }
            mock_client.make_request.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            service = EmbeddingService()
            result = await service._make_embedding_request("test text")
            
            assert result == [0.1, 0.2, 0.3]
            mock_client.make_request.assert_called_once_with(["test text"])

    @pytest.mark.asyncio
    async def test_make_embedding_request_empty_response(self):
        with patch('src.core.rag.embedder.EmbeddingsClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.make_request.return_value = {"data": []}
            mock_client_class.return_value = mock_client
            
            service = EmbeddingService()
            
            with pytest.raises(ValueError, match="Failed to get embedding from Azure OpenAI"):
                await service._make_embedding_request("test text")

    @pytest.mark.asyncio
    async def test_make_embedding_request_no_data(self):
        with patch('src.core.rag.embedder.EmbeddingsClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.make_request.return_value = {}
            mock_client_class.return_value = mock_client
            
            service = EmbeddingService()
            
            with pytest.raises(ValueError, match="Failed to get embedding from Azure OpenAI"):
                await service._make_embedding_request("test text")

    @pytest.mark.asyncio
    async def test_make_embedding_request_rate_limit_retry(self):
        with patch('src.core.rag.embedder.EmbeddingsClient') as mock_client_class, \
             patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            
            mock_client = AsyncMock()
            # First call raises 429 error, second succeeds
            mock_client.make_request.side_effect = [
                Exception("429 Rate limit exceeded"),
                {"data": [{"embedding": [0.1, 0.2, 0.3]}]}
            ]
            mock_client_class.return_value = mock_client
            
            service = EmbeddingService()
            result = await service._make_embedding_request("test text")
            
            assert result == [0.1, 0.2, 0.3]
            mock_sleep.assert_called_once_with(60)
            assert mock_client.make_request.call_count == 2

    @pytest.mark.asyncio
    async def test_make_embedding_request_non_429_error(self):
        with patch('src.core.rag.embedder.EmbeddingsClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.make_request.side_effect = Exception("Server error")
            mock_client_class.return_value = mock_client
            
            service = EmbeddingService()
            
            with pytest.raises(Exception, match="Server error"):
                await service._make_embedding_request("test text")


class TestTextEmbedding3Small:
    def test_text_embedding_3_small_model_property(self):
        service = TextEmbedding3Small()
        assert service.model == "text-embedding-3-small"

    def test_text_embedding_3_small_get_metadata(self):
        service = TextEmbedding3Small()
        metadata = service.get_metadata()
        
        expected_metadata = {
            "index_name": "index_text_embedding_3_small",
            "label": "DOCUMENTCHUNK",
            "property_name": "embedding",
            "dimension": 1536,
            "model": "text-embedding-3-small",
            "capacity": 4096,
            "metric": "cos",
            "resize_coefficient": 2
        }
        
        assert metadata == expected_metadata

    def test_text_embedding_3_small_inheritance(self):
        service = TextEmbedding3Small()
        assert isinstance(service, EmbeddingService)

    @pytest.mark.asyncio
    async def test_text_embedding_3_small_integration(self):
        """Test that TextEmbedding3Small inherits EmbeddingService functionality"""
        with patch('src.core.rag.embedder.EmbeddingsClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = {
                "data": [{"embedding": [0.1] * 1536}]  # Dimension matching the model
            }
            mock_client.make_request.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            service = TextEmbedding3Small()
            result = await service.get_embedding("test text")
            
            assert len(result) == 1536
            assert all(x == 0.1 for x in result)


class TestEmbeddingServiceEdgeCases:
    @pytest.mark.asyncio
    async def test_process_chunks_empty_list(self):
        with patch('src.core.rag.embedder.EmbeddingsClient'):
            service = EmbeddingService()
            
            callback_results = []
            def callback(vector):
                callback_results.append(vector)
            
            await service.process_chunks([], callback)
            
            assert len(callback_results) == 0

    @pytest.mark.asyncio
    async def test_process_chunk_with_empty_content(self):
        with patch('src.core.rag.embedder.EmbeddingsClient'):
            service = EmbeddingService()
            service._make_embedding_request = AsyncMock(return_value=[0.0, 0.0, 0.0])
            
            chunk = DocumentChunk(
                path="/test/path",
                content="",
                parent_id="parent123"
            )
            
            callback_results = []
            def callback(vector):
                callback_results.append(vector)
            
            await service.process_chunk(chunk, callback)
            
            assert len(callback_results) == 1
            vector = callback_results[0]
            assert vector.embedding == [0.0, 0.0, 0.0]

    @pytest.mark.asyncio
    async def test_search_similar_default_limit(self):
        with patch('src.core.rag.embedder.EmbeddingsClient'):
            service = EmbeddingService()
            service._make_embedding_request = AsyncMock(return_value=[0.1, 0.2, 0.3])
            
            mock_vector_store = AsyncMock()
            mock_vector_store.search.return_value = []
            service._vector_store = mock_vector_store
            
            await service.search_similar("test query")
            
            # Should use default limit of 5
            mock_vector_store.search.assert_called_once_with([0.1, 0.2, 0.3], 5)

    @pytest.mark.asyncio
    async def test_make_embedding_request_retry_exhausted(self):
        with patch('src.core.rag.embedder.EmbeddingsClient') as mock_client_class, \
             patch('asyncio.sleep', new_callable=AsyncMock):
            
            mock_client = AsyncMock()
            mock_client.make_request.side_effect = Exception("429 Rate limit exceeded")
            mock_client_class.return_value = mock_client
            
            service = EmbeddingService()
            
            # Start with retry=1 to test exhaustion
            with pytest.raises(Exception, match="429 Rate limit exceeded"):
                await service._make_embedding_request("test text", retry=1)
