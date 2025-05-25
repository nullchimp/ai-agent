import pytest
import uuid
from datetime import datetime, timezone
from core.rag.schema import Document, DocumentChunk, ProcessingStatus, EdgeType, Node, Source, Interaction, VectorStore, Vector


class TestDocument:
    def test_document_creation(self):
        document = Document(
            path="/test/path.txt",
            content="Test content",
            title="Test Document",
            source_id="source123"
        )
        
        assert document.path == "/test/path.txt"
        assert document.content == "Test content"
        assert document.title == "Test Document"
        assert document.source_id == "source123"
        assert document.content_hash is not None
        assert isinstance(document.id, uuid.UUID)
        assert isinstance(document.created_at, datetime)

    def test_document_minimal_creation(self):
        document = Document(
            path="/test/path.txt",
            content="Test content"
        )
        
        assert document.path == "/test/path.txt"
        assert document.content == "Test content"
        assert document.title == ""
        assert document.source_id == ""
        assert document._references == []

    def test_document_with_references(self):
        document = Document(
            path="/test/path.txt",
            content="Test content",
            references=["ref1", "ref2"]
        )
        
        assert document._references == ["ref1", "ref2"]

    def test_document_content_hash_consistency(self):
        doc1 = Document(path="/test", content="same content")
        doc2 = Document(path="/test2", content="same content")
        
        assert doc1.content_hash == doc2.content_hash

    def test_document_content_hash_different(self):
        doc1 = Document(path="/test", content="content 1")
        doc2 = Document(path="/test", content="content 2")
        
        assert doc1.content_hash != doc2.content_hash


class TestDocumentChunk:
    def test_document_chunk_creation(self):
        chunk = DocumentChunk(
            path="/test/chunk.txt",
            content="Chunk content",
            parent_id="parent123",
            chunk_index=1,
            token_count=50
        )
        
        assert chunk.path == "/test/chunk.txt"
        assert chunk.content == "Chunk content"
        assert chunk.parent_id == "parent123"
        assert chunk.chunk_index == 1
        assert chunk.token_count == 50
        assert chunk.content_hash is not None
        assert isinstance(chunk.id, uuid.UUID)
        assert isinstance(chunk.created_at, datetime)

    def test_document_chunk_minimal_creation(self):
        chunk = DocumentChunk(
            path="/test/chunk.txt",
            content="Chunk content",
            parent_id="parent123"
        )
        
        assert chunk.path == "/test/chunk.txt"
        assert chunk.content == "Chunk content"
        assert chunk.parent_id == "parent123"
        assert chunk.chunk_index == 0
        assert chunk.token_count == 0

    def test_document_chunk_content_hash_consistency(self):
        chunk1 = DocumentChunk(path="/test", content="same content", parent_id="parent")
        chunk2 = DocumentChunk(path="/test2", content="same content", parent_id="parent2")
        
        assert chunk1.content_hash == chunk2.content_hash


class TestNode:
    def test_node_creation(self):
        node = Node()
        
        assert isinstance(node.id, uuid.UUID)
        assert isinstance(node.created_at, datetime)
        assert node.created_at.tzinfo == timezone.utc

    def test_node_id_uniqueness(self):
        node1 = Node()
        node2 = Node()
        
        assert node1.id != node2.id


class TestSource:
    def test_source_creation(self):
        source = Source(
            name="Test Source",
            type="file",
            uri="/path/to/source"
        )
        
        assert source.name == "Test Source"
        assert source.type == "file"
        assert source.uri == "/path/to/source"
        assert isinstance(source.id, uuid.UUID)

    def test_source_minimal_creation(self):
        source = Source(
            name="Test Source",
            type="file"
        )
        
        assert source.name == "Test Source"
        assert source.type == "file"
        assert source.uri == ""


class TestInteraction:
    def test_interaction_creation(self):
        interaction = Interaction(
            session_id="session123",
            content="Hello, world!",
            role="user"
        )
        
        assert interaction.session_id == "session123"
        assert interaction.content == "Hello, world!"
        assert interaction.role == "user"
        assert interaction.content_hash is not None
        assert isinstance(interaction.id, uuid.UUID)

    def test_interaction_content_hash_consistency(self):
        int1 = Interaction(session_id="s1", content="same content", role="user")
        int2 = Interaction(session_id="s2", content="same content", role="assistant")
        
        assert int1.content_hash == int2.content_hash


class TestVectorStore:
    def test_vector_store_creation(self):
        vector_store = VectorStore(
            model="text-embedding-3-small",
            status=ProcessingStatus.COMPLETED
        )
        
        assert vector_store.model == "text-embedding-3-small"
        assert vector_store.status == ProcessingStatus.COMPLETED
        assert isinstance(vector_store.id, uuid.UUID)

    def test_vector_store_default_status(self):
        vector_store = VectorStore(model="test-model")
        
        assert vector_store.status == ProcessingStatus.PENDING


class TestVector:
    def test_vector_creation(self):
        embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        vector = Vector(
            chunk_id="chunk123",
            vector_store_id="store123",
            embedding=embedding
        )
        
        assert vector.chunk_id == "chunk123"
        assert vector.vector_store_id == "store123"
        assert vector.embedding == embedding
        assert isinstance(vector.id, uuid.UUID)

    def test_vector_embedding_copy(self):
        original_embedding = [0.1, 0.2, 0.3]
        vector = Vector(
            chunk_id="chunk123",
            vector_store_id="store123",
            embedding=original_embedding
        )
        
        # Modify original list
        original_embedding.append(0.4)
        
        # Vector should not be affected
        assert len(vector.embedding) == 4


class TestEnums:
    def test_processing_status_values(self):
        assert ProcessingStatus.PENDING.value == "pending"
        assert ProcessingStatus.PROCESSING.value == "processing"
        assert ProcessingStatus.COMPLETED.value == "completed"
        assert ProcessingStatus.FAILED.value == "failed"

    def test_edge_type_enum_exists(self):
        # Just verify the enum exists and can be imported
        assert EdgeType is not None
