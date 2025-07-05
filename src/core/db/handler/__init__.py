from __future__ import annotations

from typing import Any, Dict, Optional

# ════════════════════════════════════════════════════════════════════════
#  GraphClient
# ════════════════════════════════════════════════════════════════════════
class GraphClient:
    # ───── Connection boilerplate ─────
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 7687,
        username: str | None = None,
        password: str | None = None,
        **kwargs,
    ) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self._conn = None
        self._cur = None

    def connect(self, *args, **kwargs) -> None:
        raise ConnectionError("Not implemented")

    def close(self) -> None:
        self._cur.close()
        self._conn.close()

    # Context-manager support
    def __enter__(self, *args, **kwargs) -> GraphClient:
        try:
            self.connect(**kwargs)
        except Exception as e:
            print(f"Connection error: {str(e)}")
            raise ConnectionError(f"Failed to connect to Memgraph at {self.host}:{self.port}: {str(e)}") from e

        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def _execute(self, query: str, params: Optional[Dict[str, Any]] = None) -> None:
        try:
            if params:
                self._cur.execute(query, params)
            else:
                self._cur.execute(query)
        except Exception as e:
            print(f"Query execution error: {str(e)}")
            print(f"Query: {query}")
            if params:
                print(f"Params: {params}")
            raise

    def _fetch_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        query = f"MATCH (n {{id: $id}}) RETURN n"
        self._execute(query, {"id": str(id)})
        result = self._cur.fetchone()
        if result:
            return result[0].properties