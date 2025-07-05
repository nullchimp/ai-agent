from typing import Optional
import threading
import queue
from contextlib import contextmanager

from .handler.memgraph import MemGraphClient

class ConnectionPool:
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 7687,
        username: Optional[str] = None,
        password: Optional[str] = None,
        min_connections: int = 2,
        max_connections: int = 10,
        connection_timeout: float = 30.0,
        idle_timeout: float = 300.0,
    ) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.connection_timeout = connection_timeout
        self.idle_timeout = idle_timeout
        
        self._pool: queue.Queue[MemGraphClient] = queue.Queue(maxsize=max_connections)
        self._created_connections = 0
        self._lock = threading.RLock()
        self._shutdown = False
        
        self._initialize_pool()

    def _initialize_pool(self) -> None:
        for _ in range(self.min_connections):
            connection = self._create_connection()
            if connection:
                self._pool.put(connection)

    def _create_connection(self) -> Optional[MemGraphClient]:
        try:
            print(f"Creating new database connection to {self.host}:{self.port}")
            print(f"Using credentials: {self.username}:{self.password}")
            client = MemGraphClient(
                host=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
            )
            client.connect()
            with self._lock:
                self._created_connections += 1
            return client
        except Exception as e:
            print(f"Failed to create database connection: {e}")
            return None

    def _validate_connection(self, connection: MemGraphClient) -> bool:
        try:
            connection._execute("RETURN 1")
            return True
        except Exception:
            return False

    @contextmanager
    def get_connection(self):
        connection = None
        try:
            connection = self._pool.get(timeout=self.connection_timeout)
            
            if not self._validate_connection(connection):
                connection.close()
                with self._lock:
                    self._created_connections -= 1
                connection = self._create_connection()
                if not connection:
                    raise ConnectionError("Failed to create valid database connection")
            
            yield connection
            
        except queue.Empty:
            if self._created_connections < self.max_connections:
                connection = self._create_connection()
                if connection:
                    yield connection
                else:
                    raise ConnectionError("Unable to create new database connection")
            else:
                raise ConnectionError("Connection pool exhausted")
                
        finally:
            if connection and not self._shutdown:
                try:
                    self._pool.put_nowait(connection)
                except queue.Full:
                    connection.close()
                    with self._lock:
                        self._created_connections -= 1

    def close_all(self) -> None:
        self._shutdown = True
        connections_to_close = []
        
        while not self._pool.empty():
            try:
                connection = self._pool.get_nowait()
                connections_to_close.append(connection)
            except queue.Empty:
                break
        
        for connection in connections_to_close:
            try:
                connection.close()
            except Exception as e:
                print(f"Error closing connection: {e}")
        
        with self._lock:
            self._created_connections = 0


_connection_pool: Optional[ConnectionPool] = None
_pool_lock = threading.Lock()

def new_connection_pool() -> ConnectionPool:
    import os
    return ConnectionPool(
        host=os.environ.get("MEMGRAPH_URI", "localhost"),
        port=int(os.environ.get("MEMGRAPH_PORT", 7687)),
        username=os.environ.get("MEMGRAPH_USERNAME", "memgraph"),
        password=os.environ.get("MEMGRAPH_PASSWORD", "memgraph")
    )

def get_connection_pool() -> ConnectionPool:
    global _connection_pool
    if _connection_pool is None:
        with _pool_lock:
            if _connection_pool is None:
                _connection_pool = new_connection_pool()
    return _connection_pool

def close_connection_pool() -> None:
    global _connection_pool
    if _connection_pool:
        _connection_pool.close_all()
        _connection_pool = None
