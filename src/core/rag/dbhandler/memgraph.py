import mgclient
from . import GraphClient

# ════════════════════════════════════════════════════════════════════════
#  MemGraphClient
# ════════════════════════════════════════════════════════════════════════
class MemGraphClient(GraphClient):
    # ───── Connection boilerplate ─────
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 7687,
        username: str | None = None,
        password: str | None = None,
        **kwargs,
    ) -> None:
        super().__init__(
            host=host,
            port=port,
            username=username,
            password=password,
            **kwargs,
        )
    
    def connect(self, *args, **kwargs) -> None:
        host = self.host
        if self.host.startswith("bolt://"):
            host = self.host.replace("bolt://", "")
            
        # Handle localhost -> 127.0.0.1 conversion (more reliable)
        if host == "localhost":
            host = "127.0.0.1"
            
        print(f"Connecting to Memgraph at {host}:{self.port}")
        self._conn = mgclient.connect(
            host=host,
            port=self.port,
            username=self.username,
            password=self.password,
            **kwargs,
        )
        self._conn.autocommit = True
        self._cur = self._conn.cursor()
        print(f"Connected successfully to Memgraph")

        return self
        