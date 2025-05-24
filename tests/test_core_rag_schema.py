import pytest
import uuid
import hashlib
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from src.core.rag.schema import (
    Node, Source, Document, DocumentChunk, Interaction, VectorStore, Vector,
    ProcessingStatus, EdgeType
)


class TestProcessingStatus:
    def test_processing_status_enum_values(self):
        assert ProcessingStatus.PENDING.value == "pending"
        assert ProcessingStatus.PROCESSING.value == "processing"
        assert ProcessingStatus.COMPLETED.value == "completed"
        assert ProcessingStatus.FAILED.value == "failed"


class TestEdgeType:
    def test_edge_type_enum_values(self):
        assert EdgeType.CHUNK_OF.value == "CHUNK_OF"
        assert EdgeType.FOLLOWS.value == "FOLLOWS"
        assert EdgeType.SOURCED_FROM.value == "SOURCED_FROM"
        assert EdgeType.STORED_IN.value == "STORED_IN"
        assert EdgeType.EMBEDDING_OF.value == "EMBEDDING_OF"
        assert EdgeType.REFERENCES.value == "REFERENCES"


class TestNode:
    def test_node_label_class_method(self):
        assert Node.label() == "NODE"

    def test_node_init(self):
        node = Node()
        
        assert isinstance(node.id, uuid.UUID)
        assert isinstance(node.created_at, datetime)
        assert isinstance(node.updated_at, datetime)
        assert node.metadata == {}
        
        # Check timezone awareness
        assert node.created_at.tzinfo is not None
        assert node.updated_at.tzinfo is not None

    def test_node_fill_method(self):
        node = Node()
        node.fill("test_key", "test_value")
        
        assert node.test_key == "test_value"

    def test_node_add_metadata(self):
        node = Node()
        node.add_metadata(key1="value1", key2="value2")
        
        assert node.metadata["key1"] == "value1"
        assert node.metadata["key2"] == "value2"

    def test_node_to_dict(self):
        node = Node()
        node.test_attr = "test_value"
        node.test_uuid = uuid.uuid4()
        node.test_status = ProcessingStatus.PENDING
        
        result = node.to_dict()
        
        assert isinstance(result["id"], str)
        assert isinstance(result["created_at"], str)
        assert isinstance(result["updated_at"], str)
        assert result["test_attr"] == "test_value"
        assert isinstance(result["test_uuid"], str)
        assert result["test_status"] == "pending"

    def test_node_create_query(self):
        node = Node()
        query, params = node.create()
        
        expected_query = "MERGE (n:`NODE` {id: $id}) SET n += $props RETURN n.id"
        assert query == expected_query
        assert params["id"] == str(node.id)
        assert "props" in params
        assert isinstance(params["props"], dict)

    def test_node_link_query(self):
        node = Node()
        to_id = str(uuid.uuid4())
        
        query, params = node.link(EdgeType.CHUNK_OF, "DOCUMENT", to_id)
        
        expected_query = (
            "MATCH (a:`NODE` {id: $lid}), "
            "(b:`DOCUMENT` {id: $rid}) "
            "MERGE (a)-[r:`CHUNK_OF`]->(b)"
        )
        assert query == expected_query
        assert params["lid"] == str(node.id)
        assert params["rid"] == to_id

    def test_node_to_dict_excludes_private_and_callable(self):
        node = Node()
        node._private_attr = "private"
        node.public_attr = "public"
        
        def test_method():
            return "test"
        node.test_method = test_method
        
        result = node.to_dict()
        
        assert "_private_attr" not in result
        assert "test_method" not in result
        assert result["public_attr"] == "public"


class TestSource:
    def test_source_init(self):
        source = Source(
            name="test_source",
            type="website",
            uri="https://example.com"
        )
        
        assert source.name == "test_source"
        assert source.type == "website"
        assert source.uri == "https://example.com"
        assert isinstance(source.id, uuid.UUID)

    def test_source_init_with_defaults(self):
        source = Source(
            name="test_source",
            type="file"
        )
        
        assert source.name == "test_source"
        assert source.type == "file"
        assert source.uri == ""

    def test_source_label(self):
        assert Source.label() == "SOURCE"


class TestDocument:
    def test_document_init(self):
        content = "This is test content"
        doc = Document(
            path="/test/path",
            content=content,
            title="Test Document",
            source_id="source123"
        )
        
        assert doc.path == "/test/path"
        assert doc.content == content
        assert doc.title == "Test Document"
        assert doc.source_id == "source123"
        assert doc.content_hash == hashlib.sha256(content.encode()).hexdigest()
        assert doc._references == []

    def test_document_init_with_references(self):
        doc = Document(
            path="/test/path",
            content="content",
            references=["ref1", "ref2"]
        )
        
        assert doc._references == ["ref1", "ref2"]

    def test_document_init_with_defaults(self):
        doc = Document(
            path="/test/path",
            content="content"
        )
        
        assert doc.title == ""
        assert doc.source_id == ""
        assert doc._references == []

    def test_document_label(self):
        assert Document.label() == "DOCUMENT"

    def test_document_content_hash_consistency(self):
        content = "same content"
        doc1 = Document(path="/path1", content=content)
        doc2 = Document(path="/path2", content=content)
        
        assert doc1.content_hash == doc2.content_hash


class TestDocumentChunk:
    def test_document_chunk_init(self):
        content = "This is chunk content"
        chunk = DocumentChunk(
            path="/test/path",
            content=content,
            parent_id="parent123",
            chunk_index=5,
            token_count=100
        )
        
        assert chunk.path == "/test/path"
        assert chunk.content == content
        assert chunk.parent_id == "parent123"
        assert chunk.chunk_index == 5
        assert chunk.token_count == 100
        assert chunk.content_hash == hashlib.sha256(content.encode()).hexdigest()

    def test_document_chunk_init_with_defaults(self):
        chunk = DocumentChunk(
            path="/test/path",
            content="content",
            parent_id="parent123"
        )
        
        assert chunk.chunk_index == 0
        assert chunk.token_count == 0

    def test_document_chunk_label(self):
        assert DocumentChunk.label() == "DOCUMENTCHUNK"


class TestInteraction:
    def test_interaction_init(self):
        content = "Hello, how are you?"
        interaction = Interaction(
            session_id="session123",
            content=content,
            role="user"
        )
        
        assert interaction.session_id == "session123"
        assert interaction.content == content
        assert interaction.role == "user"
        assert interaction.content_hash == hashlib.sha256(content.encode()).hexdigest()

    def test_interaction_label(self):
        assert Interaction.label() == "INTERACTION"


class TestVectorStore:
    def test_vector_store_init(self):
        vector_store = VectorStore(
            model="text-embedding-ada-002",
            status=ProcessingStatus.COMPLETED
        )
        
        assert vector_store.model == "text-embedding-ada-002"
        assert vector_store.status == ProcessingStatus.COMPLETED

    def test_vector_store_init_with_defaults(self):
        vector_store = VectorStore(model="test-model")
        
        assert vector_store.status == ProcessingStatus.PENDING

    def test_vector_store_label(self):
        assert VectorStore.label() == "VECTORSTORE"


class TestVector:
    def test_vector_init(self):
        embedding = [0.1, 0.2, 0.3, 0.4]
        vector = Vector(
            chunk_id="chunk123",
            vector_store_id="store123",
            embedding=embedding
        )
        
        assert vector.chunk_id == "chunk123"
        assert vector.vector_store_id == "store123"
        assert vector.embedding == embedding

    def test_vector_label(self):
        assert Vector.label() == "VECTOR"

    def test_vector_embedding_reference(self):
        embedding = [0.1, 0.2, 0.3]
        vector = Vector(
            chunk_id="chunk123",
            vector_store_id="store123",
            embedding=embedding
        )
        
        # Modify original list to ensure it's not copied
        embedding.append(0.4)
        assert len(vector.embedding) == 4  # Should reflect the change


class TestNodeIntegration:
    def test_node_inheritance_consistency(self):
        """Test that all node types inherit Node functionality correctly"""
        nodes = [
            Source("test", "file"),
            Document("/path", "content"),
            DocumentChunk("/path", "content", "parent"),
            Interaction("session", "content", "user"),
            VectorStore("model"),
            Vector("chunk", "store", [0.1, 0.2])
        ]
        
        for node in nodes:
            # All should have UUID
            assert isinstance(node.id, uuid.UUID)
            
            # All should have timestamps
            assert isinstance(node.created_at, datetime)
            assert isinstance(node.updated_at, datetime)
            
            # All should have metadata
            assert hasattr(node, 'metadata')
            
            # All should be able to create queries
            query, params = node.create()
            assert isinstance(query, str)
            assert isinstance(params, dict)
            
            # All should be able to create link queries
            link_query, link_params = node.link(EdgeType.CHUNK_OF, "TEST", "test_id")
            assert isinstance(link_query, str)
            assert isinstance(link_params, dict)

    def test_to_dict_serialization_consistency(self):
        """Test that to_dict works consistently across all node types"""
        nodes = [
            Source("test", "file", "uri"),
            Document("/path", "content", "title"),
            DocumentChunk("/path", "content", "parent", 1, 50),
            Interaction("session", "content", "user"),
            VectorStore("model", ProcessingStatus.COMPLETED),
            Vector("chunk", "store", [0.1, 0.2, 0.3])
        ]
        
        for node in nodes:
            result = node.to_dict()
            
            # All should have basic node fields as strings
            assert isinstance(result["id"], str)
            assert isinstance(result["created_at"], str)
            assert isinstance(result["updated_at"], str)
            
            # Should not contain private or callable attributes
            for key in result.keys():
                assert not key.startswith('_')
                assert not callable(getattr(node, key, None))

    def test_edge_type_integration(self):
        """Test that edge types work correctly with link methods"""
        source_node = Source("test", "file")
        target_id = str(uuid.uuid4())
        
        for edge_type in EdgeType:
            query, params = source_node.link(edge_type, "TARGET", target_id)
            
            assert edge_type.value in query
            assert params["lid"] == str(source_node.id)
            assert params["rid"] == target_id
