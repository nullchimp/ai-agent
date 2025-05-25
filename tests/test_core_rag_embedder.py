import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from src.core.rag.embedder import EmbeddingService
from src.core.rag.embedder.text_embedding_3_small import TextEmbedding3Small
from src.core.rag.schema import DocumentChunk, Vector


class TestEmbeddingService:
    @pytest.fixture
    def mock_client(self):
        client = Mock()
        client.make_request = AsyncMock()
        return client

    @pytest.fixture
    def service(self, mock_client):
        with patch('src.core.rag.embedder.EmbeddingsClient', return_value=mock_client):
            return EmbeddingService()

    def test_init(self, service, mock_client):
        assert service._client == mock_client

    def test_get_index_config_not_implemented(self, service):
        with pytest.raises(NotImplementedError, match="Subclasses should implement this method"):
            service.get_index_config()

    @pytest.mark.asyncio
    async def test_get_embedding(self, service):
        with patch.object(service, '_make_embedding_request', return_value=[0.1, 0.2, 0.3]) as mock_request:
            result = await service.get_embedding("test text")

            assert result == [0.1, 0.2, 0.3]
            mock_request.assert_called_once_with("test text")

    @pytest.mark.asyncio
    async def test_process_chunk_success(self, service):
        chunk = DocumentChunk(path="test.txt", content="test content", parent_id="doc_1", chunk_index="chunk_1")
        chunk.id = "chunk_1"
        callback = Mock()
        
        with patch.object(service, '_make_embedding_request', return_value=[0.1, 0.2, 0.3]):
            await service.process_chunk(chunk, callback)

            callback.assert_called_once()
            vector_arg = callback.call_args[0][0]
            assert isinstance(vector_arg, Vector)
            assert vector_arg.chunk_id == "chunk_1"
            assert vector_arg.embedding == [0.1, 0.2, 0.3]

    @pytest.mark.asyncio
    async def test_process_chunk_embedding_error(self, service):
        chunk = DocumentChunk(path="test.txt", content="test content", parent_id="doc_1", chunk_index="chunk_1")
        
        with patch.object(service, '_make_embedding_request', side_effect=Exception("API error")):
            with pytest.raises(ValueError, match="Failed to get embedding: API error"):
                await service.process_chunk(chunk)

    @pytest.mark.asyncio
    async def test_process_chunk_no_callback(self, service):
        chunk = DocumentChunk(path="test.txt", content="test content", parent_id="doc_1", chunk_index="chunk_1")
        chunk.id = "chunk_1"
        
        with patch.object(service, '_make_embedding_request', return_value=[0.1, 0.2, 0.3]):
            await service.process_chunk(chunk)

    @pytest.mark.asyncio
    async def test_process_chunks(self, service):
        chunks = [
            DocumentChunk(path="test1.txt", content="content 1", parent_id="doc_1", chunk_index="chunk_1"),
            DocumentChunk(path="test2.txt", content="content 2", parent_id="doc_2", chunk_index="chunk_2"),
            DocumentChunk(path="test3.txt", content="content 3", parent_id="doc_3", chunk_index="chunk_3")
        ]
        callback = Mock()
        
        with patch.object(service, 'process_chunk') as mock_process:
            await service.process_chunks(chunks, callback)

            assert mock_process.call_count == 3
            for i, chunk in enumerate(chunks):
                mock_process.assert_any_call(chunk, callback)

    @pytest.mark.asyncio
    async def test_process_chunks_batching(self, service):
        # Test with more chunks than batch size to ensure batching works
        chunks = [DocumentChunk(path=f"test{i}.txt", content=f"content {i}", parent_id=f"doc_{i}", chunk_index=f"chunk_{i}") for i in range(7)]
        
        async def async_mock(*args, **kwargs):
            return None
        
        with patch.object(service, 'process_chunk', side_effect=async_mock) as mock_process:
            await service.process_chunks(chunks)

            # Should be called once for each chunk (7 total)
            assert mock_process.call_count == 7

    @pytest.mark.asyncio
    async def test_search_similar(self, service):
        mock_vector_store = Mock()
        mock_vector_store.search = AsyncMock(return_value=[{"chunk": "result"}])
        service._vector_store = mock_vector_store
        
        with patch.object(service, '_make_embedding_request', return_value=[0.1, 0.2, 0.3]):
            result = await service.search_similar("search text", limit=3)

            assert result == [{"chunk": "result"}]
            mock_vector_store.search.assert_called_once_with([0.1, 0.2, 0.3], 3)

    @pytest.mark.asyncio
    async def test_make_embedding_request_success(self, service):
        service._client.make_request.return_value = {
            "data": [{"embedding": [0.1, 0.2, 0.3]}]
        }

        result = await service._make_embedding_request("test text")

        assert result == [0.1, 0.2, 0.3]
        service._client.make_request.assert_called_once_with(["test text"])

    @pytest.mark.asyncio
    async def test_make_embedding_request_empty_response(self, service):
        service._client.make_request.return_value = {"data": []}

        with pytest.raises(ValueError, match="Failed to get embedding from Azure OpenAI"):
            await service._make_embedding_request("test text")

    @pytest.mark.asyncio
    async def test_make_embedding_request_no_data(self, service):
        service._client.make_request.return_value = {}

        with pytest.raises(ValueError, match="Failed to get embedding from Azure OpenAI"):
            await service._make_embedding_request("test text")

    @pytest.mark.asyncio
    async def test_make_embedding_request_retry_429(self, service):
        # First call raises 429 error, second succeeds
        service._client.make_request.side_effect = [
            Exception("429 Too Many Requests"),
            {"data": [{"embedding": [0.1, 0.2, 0.3]}]}
        ]

        with patch('asyncio.sleep') as mock_sleep:
            result = await service._make_embedding_request("test text", retry=2)

            assert result == [0.1, 0.2, 0.3]
            mock_sleep.assert_called_once_with(60)
            assert service._client.make_request.call_count == 2

    @pytest.mark.asyncio
    async def test_make_embedding_request_retry_exhausted(self, service):
        service._client.make_request.side_effect = Exception("429 Too Many Requests")

        with patch('asyncio.sleep'):
            with pytest.raises(Exception, match="429 Too Many Requests"):
                await service._make_embedding_request("test text", retry=1)

    @pytest.mark.asyncio
    async def test_make_embedding_request_non_429_error(self, service):
        service._client.make_request.side_effect = Exception("500 Server Error")

        with pytest.raises(Exception, match="500 Server Error"):
            await service._make_embedding_request("test text")


class TestTextEmbedding3Small:
    @pytest.fixture
    def mock_client(self):
        client = Mock()
        client.make_request = AsyncMock()
        return client

    @pytest.fixture
    def embedding_service(self, mock_client):
        with patch('src.core.rag.embedder.EmbeddingsClient', return_value=mock_client):
            return TextEmbedding3Small()

    def test_model_property(self, embedding_service):
        assert embedding_service.model == "text-embedding-3-small"

    def test_get_metadata(self, embedding_service):
        metadata = embedding_service.get_metadata()
        
        expected = {
            "index_name": "index_text_embedding_3_small",
            "label": DocumentChunk.label(),
            "property_name": "embedding",
            "dimension": 1536,
            "model": "text-embedding-3-small",
            "capacity": 4096,
            "metric": "cos",
            "resize_coefficient": 2
        }
        
        assert metadata == expected

    def test_inheritance(self, embedding_service):
        assert isinstance(embedding_service, EmbeddingService)

    @pytest.mark.asyncio
    async def test_inherited_functionality(self, embedding_service):
        # Test that inherited methods work correctly
        embedding_service._client.make_request.return_value = {
            "data": [{"embedding": [0.1, 0.2, 0.3]}]
        }

        result = await embedding_service.get_embedding("test text")
        assert result == [0.1, 0.2, 0.3]
