import pytest
from unittest.mock import Mock, patch, MagicMock
from src.core.rag.dbhandler import GraphClient
from src.core.rag.schema import (
    Document, DocumentChunk, Source, Vector, VectorStore, 
    Interaction, EdgeType, ProcessingStatus
)


class TestGraphClient:
    @pytest.fixture
    def client(self):
        return GraphClient(host="localhost", port=7687, username="user", password="pass")

    @pytest.fixture
    def mock_connection(self):
        conn = Mock()
        cursor = Mock()
        cursor.fetchall.return_value = []
        cursor.fetchone.return_value = None
        conn.cursor.return_value = cursor
        return conn, cursor

    def test_init(self, client):
        assert client.host == "localhost"
        assert client.port == 7687
        assert client.username == "user"
        assert client.password == "pass"
        assert client._conn is None
        assert client._cur is None

    def test_connect_not_implemented(self, client):
        with pytest.raises(ConnectionError, match="Not implemented"):
            client.connect()

    def test_close(self, client, mock_connection):
        conn, cursor = mock_connection
        client._conn = conn
        client._cur = cursor

        client.close()

        cursor.close.assert_called_once()
        conn.close.assert_called_once()

    def test_context_manager_success(self, client):
        with patch.object(client, 'connect') as mock_connect:
            with patch.object(client, 'close') as mock_close:
                with client:
                    pass

        mock_connect.assert_called_once()
        mock_close.assert_called_once()

    def test_context_manager_connection_error(self, client):
        with patch.object(client, 'connect', side_effect=Exception("Connection failed")):
            with pytest.raises(ConnectionError, match="Failed to connect to Memgraph"):
                with client:
                    pass

    def test_execute_success(self, client, mock_connection):
        conn, cursor = mock_connection
        client._cur = cursor

        client._execute("MATCH (n) RETURN n")

        cursor.execute.assert_called_once_with("MATCH (n) RETURN n")

    def test_execute_with_params(self, client, mock_connection):
        conn, cursor = mock_connection
        client._cur = cursor
        params = {"id": "test"}

        client._execute("MATCH (n {id: $id}) RETURN n", params)

        cursor.execute.assert_called_once_with("MATCH (n {id: $id}) RETURN n", params)

    def test_execute_error(self, client, mock_connection):
        conn, cursor = mock_connection
        client._cur = cursor
        cursor.execute.side_effect = Exception("Query error")

        with pytest.raises(Exception, match="Query error"):
            client._execute("INVALID QUERY")

    def test_create_document(self, client, mock_connection):
        conn, cursor = mock_connection
        client._cur = cursor
        
        doc = Mock(spec=Document)
        doc.create.return_value = ("CREATE (d:Document)", {})
        doc.source_id = None
        doc._references = []

        client.create_document(doc)

        doc.create.assert_called_once()

    def test_create_document_with_source(self, client, mock_connection):
        conn, cursor = mock_connection
        client._cur = cursor
        
        doc = Mock(spec=Document)
        doc.create.return_value = ("CREATE (d:Document)", {})
        doc.source_id = "source123"
        doc.link.return_value = ("MATCH ... CREATE", {})
        doc._references = []

        with patch.object(Source, 'label', return_value="SOURCE"):
            client.create_document(doc)

            doc.create.assert_called_once()
            # Verify the call was made with the right arguments
            assert doc.link.call_count == 1
            call_args = doc.link.call_args[0]
            assert str(call_args[0]) == "EdgeType.SOURCED_FROM"
            assert call_args[1] == "SOURCE"
            assert call_args[2] == "source123"

    def test_create_chunk_success(self, client, mock_connection):
        conn, cursor = mock_connection
        client._cur = cursor
        
        chunk = Mock(spec=DocumentChunk)
        chunk.create.return_value = ("CREATE (c:Chunk)", {})
        chunk.parent_id = "doc123"
        chunk.link.return_value = ("MATCH ... CREATE", {})

        with patch.object(Document, 'label', return_value="DOCUMENT"):
            client.create_chunk(chunk)

            chunk.create.assert_called_once()
            # Verify the call was made with the right arguments
            assert chunk.link.call_count == 1
            call_args = chunk.link.call_args[0]
            assert str(call_args[0]) == "EdgeType.CHUNK_OF"
            assert call_args[1] == "DOCUMENT"
            assert call_args[2] == "doc123"

    def test_create_chunk_no_parent_id(self, client, mock_connection):
        conn, cursor = mock_connection
        client._cur = cursor
        
        chunk = Mock(spec=DocumentChunk)
        chunk.create.return_value = ("CREATE (c:Chunk)", {})
        chunk.parent_id = None

        with pytest.raises(ValueError, match="DocumentChunk must have a parent_id"):
            client.create_chunk(chunk)

    def test_create_vector_success(self, client, mock_connection):
        conn, cursor = mock_connection
        client._cur = cursor
        
        vector = Mock(spec=Vector)
        vector.create.return_value = ("CREATE (v:Vector)", {})
        vector.chunk_id = "chunk123"
        vector.vector_store_id = "store123"
        vector.link.return_value = ("MATCH ... CREATE", {})

        with patch.object(DocumentChunk, 'label', return_value="DocumentChunk"):
            with patch.object(VectorStore, 'label', return_value="VectorStore"):
                client.create_vector(vector)

                vector.create.assert_called_once()
                assert vector.link.call_count == 2

    def test_create_vector_no_chunk_id(self, client, mock_connection):
        conn, cursor = mock_connection
        client._cur = cursor
        
        vector = Mock(spec=Vector)
        vector.chunk_id = None
        vector.vector_store_id = "store123"

        with pytest.raises(ValueError, match="Vector must have a chunk_id"):
            client.create_vector(vector)

    def test_create_vector_no_store_id(self, client, mock_connection):
        conn, cursor = mock_connection
        client._cur = cursor
        
        vector = Mock(spec=Vector)
        vector.chunk_id = "chunk123"
        vector.vector_store_id = None

        with pytest.raises(ValueError, match="Vector must have a vector_store_id"):
            client.create_vector(vector)

    def test_vector_search(self, client, mock_connection):
        conn, cursor = mock_connection
        client._cur = cursor
        
        mock_node = Mock()
        mock_node.properties = {"id": "node1", "content": "test"}
        cursor.fetchall.return_value = [
            (mock_node, 0.1, 0.9),
            (mock_node, 0.2, 0.8)
        ]

        result = client.vector_search([0.1, 0.2, 0.3], "test_index", k=2)

        assert len(result) == 2
        assert result[0]["distance"] == 0.1
        assert result[0]["similarity"] == 0.9
        assert result[0]["node"]["id"] == "node1"

    def test_get_vectors_for_chunk_basic(self, client, mock_connection):
        conn, cursor = mock_connection
        client._cur = cursor
        
        mock_node = Mock()
        mock_node.properties = {"id": "vector1", "embedding": [0.1, 0.2]}
        cursor.fetchall.return_value = [(mock_node,)]

        with patch.object(Vector, 'label', return_value="Vector"):
            with patch.object(DocumentChunk, 'label', return_value="DocumentChunk"):
                result = client.get_vectors_for_chunk("chunk123")

                assert len(result) == 1
                assert result[0]["id"] == "vector1"

    def test_get_vectors_for_chunk_with_filters(self, client, mock_connection):
        conn, cursor = mock_connection
        client._cur = cursor
        cursor.fetchall.return_value = []

        with patch.object(Vector, 'label', return_value="Vector"):
            with patch.object(DocumentChunk, 'label', return_value="DocumentChunk"):
                client.get_vectors_for_chunk("chunk123", vector_store_id="store123", model="test-model")

                cursor.execute.assert_called_once()
                args, kwargs = cursor.execute.call_args
                params = args[1] if len(args) > 1 else kwargs.get('params', {})
                assert "vector_store_id" in params
                assert "model" in params

    def test_search_chunks(self, client, mock_connection):
        conn, cursor = mock_connection
        client._cur = cursor
        
        # Mock vector search results
        vector_results = [
            {"node": {"chunk_id": "chunk1"}, "distance": 0.1, "similarity": 0.9}
        ]
        
        # Mock chunk data
        chunk_data = {"id": "chunk1", "content": "test content"}
        
        with patch.object(client, 'vector_search', return_value=vector_results):
            with patch.object(client, 'get_by_id', return_value=chunk_data):
                result = client.search_chunks([0.1, 0.2, 0.3])

                assert len(result) == 1
                assert result[0]["chunk"] == chunk_data
                assert result[0]["distance"] == 0.1

    def test_get_document_chunks(self, client, mock_connection):
        conn, cursor = mock_connection
        client._cur = cursor
        
        mock_node = Mock()
        mock_node.properties = {"id": "chunk1", "content": "test"}
        cursor.fetchall.return_value = [(mock_node,)]

        with patch.object(DocumentChunk, 'label', return_value="DocumentChunk"):
            with patch.object(Document, 'label', return_value="Document"):
                result = client.get_document_chunks("doc123")

                assert len(result) == 1
                assert result[0]["id"] == "chunk1"

    def test_get_by_id(self, client, mock_connection):
        conn, cursor = mock_connection
        client._cur = cursor
        
        mock_node = Mock()
        mock_node.properties = {"id": "test123", "name": "test"}
        cursor.fetchone.return_value = (mock_node,)

        with patch.object(Document, 'label', return_value="Document"):
            result = client.get_by_id(Document, "test123")

            assert result["id"] == "test123"
            assert result["name"] == "test"

    def test_get_by_id_not_found(self, client, mock_connection):
        conn, cursor = mock_connection
        client._cur = cursor
        cursor.fetchone.return_value = None

        with patch.object(Document, 'label', return_value="Document"):
            result = client.get_by_id(Document, "nonexistent")

            assert result is None

    def test_get_by_property_fetch_one(self, client, mock_connection):
        conn, cursor = mock_connection
        client._cur = cursor
        
        mock_node = Mock()
        mock_node.properties = {"name": "test", "value": "data"}
        cursor.fetchone.return_value = (mock_node,)

        with patch.object(Document, 'label', return_value="Document"):
            result = client.get_by_property(Document, "name", "test", fetch_one=True)

            assert result["name"] == "test"
            assert result["value"] == "data"

    def test_get_by_property_fetch_all(self, client, mock_connection):
        conn, cursor = mock_connection
        client._cur = cursor
        
        mock_node = Mock()
        mock_node.properties = {"name": "test", "value": "data"}
        cursor.fetchall.return_value = [(mock_node,), (mock_node,)]

        with patch.object(Document, 'label', return_value="Document"):
            result = client.get_by_property(Document, "name", "test", fetch_one=False)

            assert len(result) == 2
            assert result[0]["name"] == "test"

    def test_load_vector_store_by_id(self, client, mock_connection):
        conn, cursor = mock_connection
        client._cur = cursor
        
        vs_data = {"id": "store123", "model": "test-model", "dimension": 1536}
        
        with patch.object(client, 'get_by_property', return_value=vs_data):
            result = client.load_vector_store(vector_store_id="store123")

            assert result.model == "test-model"

    def test_load_vector_store_by_model(self, client, mock_connection):
        conn, cursor = mock_connection
        client._cur = cursor
        
        vs_data = {"id": "store123", "model": "test-model", "dimension": 1536}
        
        with patch.object(client, 'get_by_property', return_value=vs_data):
            result = client.load_vector_store(model="test-model")

            assert result.model == "test-model"

    def test_load_vector_store_not_found(self, client, mock_connection):
        conn, cursor = mock_connection
        client._cur = cursor
        
        with patch.object(client, 'get_by_property', return_value=None):
            result = client.load_vector_store(vector_store_id="nonexistent")

            assert result is None

    def test_load_vector_store_no_params(self, client):
        with pytest.raises(ValueError, match="Either model or vector_store_id must be provided"):
            client.load_vector_store()
