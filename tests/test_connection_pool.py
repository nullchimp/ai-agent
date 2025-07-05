import pytest
from unittest.mock import Mock, patch
import threading
import time

from src.core.db.connection_pool import ConnectionPool, get_connection_pool, close_connection_pool


class TestConnectionPool:
    @pytest.fixture
    def mock_memgraph_client(self):
        with patch('src.core.db.connection_pool.MemGraphClient') as mock_class:
            mock_instance = Mock()
            mock_instance.connect.return_value = mock_instance
            mock_instance._execute.return_value = None
            mock_class.return_value = mock_instance
            yield mock_class, mock_instance

    def test_pool_initialization(self, mock_memgraph_client):
        mock_class, mock_instance = mock_memgraph_client
        
        pool = ConnectionPool(min_connections=2, max_connections=5)
        
        assert mock_class.call_count == 2
        assert pool._created_connections == 2

    def test_get_connection_success(self, mock_memgraph_client):
        mock_class, mock_instance = mock_memgraph_client
        
        pool = ConnectionPool(min_connections=1, max_connections=3)
        
        with pool.get_connection() as conn:
            assert conn is not None
            mock_instance._execute.assert_called_with("RETURN 1")

    def test_connection_validation_and_recreation(self, mock_memgraph_client):
        mock_class, mock_instance = mock_memgraph_client
        
        pool = ConnectionPool(min_connections=1, max_connections=3)
        
        mock_instance._execute.side_effect = [Exception("Connection lost"), None]
        
        with pool.get_connection() as conn:
            assert conn is not None
            assert mock_class.call_count >= 2

    def test_pool_exhaustion_handling(self, mock_memgraph_client):
        mock_class, mock_instance = mock_memgraph_client
        
        pool = ConnectionPool(min_connections=1, max_connections=1, connection_timeout=0.1)
        
        with pool.get_connection():
            with pytest.raises(ConnectionError, match="Connection pool exhausted"):
                with pool.get_connection():
                    pass

    def test_concurrent_connection_access(self, mock_memgraph_client):
        mock_class, mock_instance = mock_memgraph_client
        
        pool = ConnectionPool(min_connections=2, max_connections=5)
        results = []
        
        def worker():
            try:
                with pool.get_connection() as conn:
                    time.sleep(0.1)
                    results.append("success")
            except Exception as e:
                results.append(f"error: {e}")
        
        threads = [threading.Thread(target=worker) for _ in range(3)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        assert len(results) == 3
        assert all(result == "success" for result in results)

    def test_close_all_connections(self, mock_memgraph_client):
        mock_class, mock_instance = mock_memgraph_client
        
        pool = ConnectionPool(min_connections=2, max_connections=5)
        pool.close_all()
        
        assert mock_instance.close.call_count >= 2
        assert pool._shutdown is True
        assert pool._created_connections == 0

    def test_global_pool_singleton(self, mock_memgraph_client):
        close_connection_pool()
        
        pool1 = get_connection_pool()
        pool2 = get_connection_pool()
        
        assert pool1 is pool2
        
        close_connection_pool()

    def test_pool_thread_safety(self, mock_memgraph_client):
        mock_class, mock_instance = mock_memgraph_client
        close_connection_pool()
        
        pools = []
        
        def get_pool():
            pools.append(get_connection_pool())
        
        threads = [threading.Thread(target=get_pool) for _ in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        assert len(set(id(pool) for pool in pools)) == 1
        
        close_connection_pool()
