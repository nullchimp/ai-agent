import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from datetime import datetime

from core.rag.indexer import Indexer, Document


@pytest.fixture
def mock_graph_client():
    client = AsyncMock()
    client.find_document = AsyncMock(return_value=None)
    client.upsert_document = AsyncMock(return_value={"id": "doc-123", "path": "test/path"})
    client.create_symbol = AsyncMock(return_value={"id": "sym-123", "name": "TestSymbol"})
    client.link_document_to_resource = AsyncMock(return_value={"id": "rel-123"})
    client.create_relationship = AsyncMock(return_value={"id": "rel-456"})
    return client


@pytest.fixture
def mock_embedding_service():
    service = AsyncMock()
    service.get_embedding = AsyncMock(return_value=[0.1, 0.2, 0.3])
    return service


@pytest.fixture
def indexer(mock_graph_client, mock_embedding_service):
    return Indexer(
        graph_client=mock_graph_client,
        embedding_service=mock_embedding_service,
        batch_size=2
    )


@pytest.mark.asyncio
async def test_index_document_new_document(indexer, mock_graph_client, mock_embedding_service):
    # Test indexing a new document
    result = await indexer.index_document(
        path="test/document.md",
        content="This is a test document",
        metadata={
            "title": "Test Document",
            "author": "Test Author",
            "mime_type": "text/markdown",
            "source_type": "web",
            "source_uri": "https://example.com/docs"
        }
    )
    
    # Verify that the embedding was generated
    mock_embedding_service.get_embedding.assert_called_once_with("This is a test document")
    
    # Verify document was stored
    mock_graph_client.upsert_document.assert_called_once()
    assert result == {"id": "doc-123", "path": "test/path"}


@pytest.mark.asyncio
async def test_index_document_existing_document(indexer, mock_graph_client):
    # Set up mock to return an existing document with matching hash
    mock_graph_client.find_document.return_value = {
        "id": "doc-456",
        "path": "existing/doc.md",
        "content_hash": "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"  # SHA256 of "test"
    }
    
    # Test indexing a document that already exists with same content
    result = await indexer.index_document(
        path="existing/doc.md",
        content="test",
        metadata={"title": "Existing Doc"}
    )
    
    # Verify document lookup was performed
    mock_graph_client.find_document.assert_called_once_with("existing/doc.md")
    
    # Verify no embedding or upsert was performed for existing doc
    mock_graph_client.upsert_document.assert_not_called()
    assert result == {
        "id": "doc-456",
        "path": "existing/doc.md",
        "content_hash": "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"
    }


@pytest.mark.asyncio
async def test_index_documents_batch_processing(indexer, mock_graph_client, mock_embedding_service):
    # Test indexing multiple documents in batches
    docs = [
        {"path": "doc1.md", "content": "Document 1", "metadata": {"title": "Doc 1"}},
        {"path": "doc2.md", "content": "Document 2", "metadata": {"title": "Doc 2"}},
        {"path": "doc3.md", "content": "Document 3", "metadata": {"title": "Doc 3"}},
        {"path": "doc4.md", "content": "Document 4", "metadata": {"title": "Doc 4"}},
        {"path": "doc5.md", "content": "Document 5", "metadata": {"title": "Doc 5"}},
    ]
    
    results = await indexer.index_documents(docs)
    
    # Verify that all documents were processed (batch size is 2)
    assert mock_graph_client.upsert_document.call_count == 5
    assert len(results) == 5


@pytest.mark.asyncio
async def test_extract_and_index_symbols(indexer, mock_graph_client):
    # Test extracting and indexing symbols
    symbols = ["ClassA", "function_b", "CONSTANT_C"]
    results = await indexer.extract_and_index_symbols("path/to/doc.py", symbols)
    
    # Verify each symbol was created
    assert mock_graph_client.create_symbol.call_count == 3
    assert len(results) == 3


@pytest.mark.asyncio
async def test_extract_and_index_resources(indexer, mock_graph_client):
    # Set up mock to return a document
    mock_graph_client.find_document.return_value = {"id": "doc-789", "path": "path/to/doc.md"}
    
    # Test linking resources to document
    resources = [
        {"uri": "https://example.com/api", "type": "web", "description": "API docs"},
        {"uri": "data://internal/dataset", "type": "dataset", "description": "Training data"}
    ]
    
    results = await indexer.extract_and_index_resources("path/to/doc.md", resources)
    
    # Verify resources were linked
    assert mock_graph_client.link_document_to_resource.call_count == 2
    assert len(results) == 2


@pytest.mark.asyncio
async def test_index_document_relations(indexer, mock_graph_client):
    # Set up mocks to return documents
    mock_graph_client.find_document.side_effect = lambda path: {
        "doc1.md": {"id": "doc-1", "path": "doc1.md"},
        "doc2.md": {"id": "doc-2", "path": "doc2.md"},
        "doc3.md": {"id": "doc-3", "path": "doc3.md"}
    }.get(path)
    
    # Test creating relations between documents
    results = await indexer.index_document_relations(
        "doc1.md",
        ["doc2.md", "doc3.md"],
        "REFERENCES"
    )
    
    # Verify relationships were created
    assert mock_graph_client.create_relationship.call_count == 2
    assert len(results) == 2
    mock_graph_client.create_relationship.assert_any_call(
        from_id="doc-1", to_id="doc-2", relationship_type="REFERENCES"
    )


@pytest.mark.asyncio
async def test_index_different_source_types(indexer):
    # Test that the indexer works with documents from different sources
    
    # Web document
    web_doc: Document = {
        "path": "web/example.com/article.html",
        "content": "<p>This is a web article</p>",
        "metadata": {
            "title": "Web Article",
            "author": "Web Author",
            "source_type": "web",
            "source_uri": "https://example.com/article",
            "mime_type": "text/html"
        }
    }
    
    # API response document
    api_doc: Document = {
        "path": "api/responses/user-data.json",
        "content": '{"name": "Test User", "id": 123}',
        "metadata": {
            "title": "User Data",
            "source_type": "api",
            "source_uri": "https://api.example.com/users/123",
            "mime_type": "application/json"
        }
    }
    
    # Database document
    db_doc: Document = {
        "path": "db/products/567",
        "content": "Product description for item 567",
        "metadata": {
            "title": "Product 567",
            "source_type": "database",
            "source_uri": "postgresql://example.com/products/567",
            "updated_at": datetime.now().isoformat()
        }
    }
    
    # Use patch to prevent actual embedding generation or graph calls
    with patch.object(indexer, 'index_document', AsyncMock()) as mock_index:
        mock_index.side_effect = lambda path, content, metadata: {"path": path, "status": "indexed"}
        
        # Index documents from different sources in a batch
        await indexer.index_documents([web_doc, api_doc, db_doc])
        
        # Verify all documents were indexed regardless of source
        assert mock_index.call_count == 3
        mock_index.assert_any_call(
            path="web/example.com/article.html",
            content="<p>This is a web article</p>",
            metadata=web_doc["metadata"]
        )
        mock_index.assert_any_call(
            path="api/responses/user-data.json",
            content='{"name": "Test User", "id": 123}',
            metadata=api_doc["metadata"]
        )
        mock_index.assert_any_call(
            path="db/products/567",
            content="Product description for item 567",
            metadata=db_doc["metadata"]
        )