import pytest
from unittest.mock import Mock, patch, MagicMock

from src.core.rag.dbhandler import GraphClient
from src.core.rag.dbhandler.memgraph import MemGraphClient


class TestGraphClient:
    def test_graph_client_init(self):
        client = GraphClient(
            host="test-host",
            port=1234,
            username="test-user",
            password="test-pass"
        )
        
        assert client.host == "test-host"
        assert client.port == 1234
        assert client.username == "test-user"
        assert client.password == "test-pass"
        assert client._conn is None
        assert client._cur is None

    def test_graph_client_init_defaults(self):
        client = GraphClient()
        
        assert client.host == "127.0.0.1"
        assert client.port == 7687
        assert client.username is None
        assert client.password is None

    def test_graph_client_connect_not_implemented(self):
        client = GraphClient()
        
        with pytest.raises(ConnectionError, match="Not implemented"):
            client.connect()

    def test_graph_client_close(self):
        client = GraphClient()
        
        # Mock connection and cursor
        mock_conn = Mock()
        mock_cur = Mock()
        client._conn = mock_conn
        client._cur = mock_cur
        
        client.close()
        
        mock_cur.close.assert_called_once()
        mock_conn.close.assert_called_once()


class TestMemGraphClient:
    def test_memgraph_client_inheritance(self):
        client = MemGraphClient()
        assert isinstance(client, GraphClient)

    def test_memgraph_client_init(self):
        client = MemGraphClient(
            host="memgraph-host",
            port=7688,
            username="memgraph-user",
            password="memgraph-pass"
        )
        
        assert client.host == "memgraph-host"
        assert client.port == 7688
        assert client.username == "memgraph-user"
        assert client.password == "memgraph-pass"

    def test_memgraph_client_init_defaults(self):
        client = MemGraphClient()
        
        assert client.host == "127.0.0.1"
        assert client.port == 7687
        assert client.username is None
        assert client.password is None

    @patch('src.core.rag.dbhandler.memgraph.mgclient.connect')
    @patch('builtins.print')
    def test_memgraph_client_connect_success(self, mock_print, mock_mgclient_connect):
        mock_conn = Mock()
        mock_cur = Mock()
        mock_conn.cursor.return_value = mock_cur
        mock_mgclient_connect.return_value = mock_conn
        
        client = MemGraphClient(host="test-host", port=7687)
        result = client.connect()
        
        # Should return self for chaining
        assert result == client
        
        # Check connection setup
        mock_mgclient_connect.assert_called_once_with(
            host="test-host",
            port=7687,
            username=None,
            password=None
        )
        
        assert mock_conn.autocommit is True
        assert client._conn == mock_conn
        assert client._cur == mock_cur
        
        # Check print statements
        assert mock_print.call_count == 2
        mock_print.assert_any_call("Connecting to Memgraph at test-host:7687")
        mock_print.assert_any_call("Connected successfully to Memgraph")

    @patch('src.core.rag.dbhandler.memgraph.mgclient.connect')
    @patch('builtins.print')
    def test_memgraph_client_connect_bolt_protocol_stripping(self, mock_print, mock_mgclient_connect):
        mock_conn = Mock()
        mock_cur = Mock()
        mock_conn.cursor.return_value = mock_cur
        mock_mgclient_connect.return_value = mock_conn
        
        client = MemGraphClient(host="bolt://test-host")
        client.connect()
        
        # Should strip bolt:// prefix
        mock_mgclient_connect.assert_called_once_with(
            host="test-host",
            port=7687,
            username=None,
            password=None
        )
        
        mock_print.assert_any_call("Connecting to Memgraph at test-host:7687")

    @patch('src.core.rag.dbhandler.memgraph.mgclient.connect')
    @patch('builtins.print')
    def test_memgraph_client_connect_localhost_conversion(self, mock_print, mock_mgclient_connect):
        mock_conn = Mock()
        mock_cur = Mock()
        mock_conn.cursor.return_value = mock_cur
        mock_mgclient_connect.return_value = mock_conn
        
        client = MemGraphClient(host="localhost")
        client.connect()
        
        # Should convert localhost to 127.0.0.1
        mock_mgclient_connect.assert_called_once_with(
            host="127.0.0.1",
            port=7687,
            username=None,
            password=None
        )
        
        mock_print.assert_any_call("Connecting to Memgraph at 127.0.0.1:7687")

    @patch('src.core.rag.dbhandler.memgraph.mgclient.connect')
    @patch('builtins.print')
    def test_memgraph_client_connect_with_credentials(self, mock_print, mock_mgclient_connect):
        mock_conn = Mock()
        mock_cur = Mock()
        mock_conn.cursor.return_value = mock_cur
        mock_mgclient_connect.return_value = mock_conn
        
        client = MemGraphClient(
            host="secure-host",
            port=7688,
            username="admin",
            password="secret"
        )
        client.connect()
        
        mock_mgclient_connect.assert_called_once_with(
            host="secure-host",
            port=7688,
            username="admin",
            password="secret"
        )

    @patch('src.core.rag.dbhandler.memgraph.mgclient.connect')
    @patch('builtins.print')
    def test_memgraph_client_connect_with_kwargs(self, mock_print, mock_mgclient_connect):
        mock_conn = Mock()
        mock_cur = Mock()
        mock_conn.cursor.return_value = mock_cur
        mock_mgclient_connect.return_value = mock_conn
        
        client = MemGraphClient()
        client.connect(sslmode="disable", connect_timeout=30)
        
        mock_mgclient_connect.assert_called_once_with(
            host="127.0.0.1",
            port=7687,
            username=None,
            password=None,
            sslmode="disable",
            connect_timeout=30
        )

    @patch('src.core.rag.dbhandler.memgraph.mgclient.connect')
    def test_memgraph_client_connect_error_handling(self, mock_mgclient_connect):
        mock_mgclient_connect.side_effect = Exception("Connection failed")
        
        client = MemGraphClient()
        
        with pytest.raises(Exception, match="Connection failed"):
            client.connect()

    def test_memgraph_client_host_processing_edge_cases(self):
        # Test various host formats
        test_cases = [
            ("bolt://localhost", "127.0.0.1"),
            ("bolt://example.com", "example.com"),
            ("localhost", "127.0.0.1"),
            ("127.0.0.1", "127.0.0.1"),
            ("example.com", "example.com"),
            ("", ""),  # Edge case: empty host
        ]
        
        for input_host, expected_host in test_cases:
            with patch('src.core.rag.dbhandler.memgraph.mgclient.connect') as mock_connect:
                mock_conn = Mock()
                mock_cur = Mock()
                mock_conn.cursor.return_value = mock_cur
                mock_connect.return_value = mock_conn
                
                client = MemGraphClient(host=input_host)
                
                with patch('builtins.print'):  # Suppress print statements
                    client.connect()
                
                # Verify the processed host was used
                call_args = mock_connect.call_args
                assert call_args[1]['host'] == expected_host


class TestGraphClientEdgeCases:
    def test_graph_client_close_with_none_connections(self):
        client = GraphClient()
        
        # Test that close doesn't fail when connections are None
        client._conn = None
        client._cur = None
        
        with pytest.raises(AttributeError):
            # This should fail because we're calling close() on None
            client.close()

    def test_graph_client_close_partial_connections(self):
        client = GraphClient()
        
        # Test case where only cursor exists
        mock_cur = Mock()
        client._cur = mock_cur
        client._conn = None
        
        with pytest.raises(AttributeError):
            # This should fail when trying to close None connection
            client.close()

    def test_memgraph_client_inheritance_chain(self):
        """Test that MemGraphClient properly inherits from GraphClient"""
        client = MemGraphClient()
        
        # Should have all GraphClient attributes
        assert hasattr(client, 'host')
        assert hasattr(client, 'port')
        assert hasattr(client, 'username')
        assert hasattr(client, 'password')
        assert hasattr(client, '_conn')
        assert hasattr(client, '_cur')
        
        # Should have GraphClient methods
        assert hasattr(client, 'close')
        
        # Should override connect method
        assert client.connect != GraphClient.connect


class TestMemGraphClientIntegration:
    @patch('src.core.rag.dbhandler.memgraph.mgclient.connect')
    @patch('builtins.print')
    def test_memgraph_client_full_workflow(self, mock_print, mock_mgclient_connect):
        """Test a complete connect -> close workflow"""
        mock_conn = Mock()
        mock_cur = Mock()
        mock_conn.cursor.return_value = mock_cur
        mock_mgclient_connect.return_value = mock_conn
        
        client = MemGraphClient(
            host="bolt://localhost",
            port=7687,
            username="test",
            password="pass"
        )
        
        # Connect
        result = client.connect()
        assert result == client
        assert client._conn == mock_conn
        assert client._cur == mock_cur
        
        # Verify connection was configured properly
        assert mock_conn.autocommit is True
        mock_mgclient_connect.assert_called_once_with(
            host="127.0.0.1",  # Should be converted from bolt://localhost
            port=7687,
            username="test",
            password="pass"
        )
        
        # Close
        client.close()
        mock_cur.close.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch('src.core.rag.dbhandler.memgraph.mgclient.connect')
    def test_memgraph_client_connection_state_tracking(self, mock_mgclient_connect):
        """Test that connection state is properly tracked"""
        mock_conn = Mock()
        mock_cur = Mock()
        mock_conn.cursor.return_value = mock_cur
        mock_mgclient_connect.return_value = mock_conn
        
        client = MemGraphClient()
        
        # Initially no connection
        assert client._conn is None
        assert client._cur is None
        
        # After connect
        with patch('builtins.print'):
            client.connect()
        
        assert client._conn == mock_conn
        assert client._cur == mock_cur
