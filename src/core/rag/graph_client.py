 # one-off: ensure an index exists (once per DB)
# mg.create_vector_index(
#     index_name="chunk_embedding_index",
#     label=NodeLabel.CHUNK,
#     property_name="embedding",
#     dimension=len(q_vec),
# )

from __future__ import annotations

import mgclient
from dataclasses import asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Sequence

# ────────────────  IMPORT YOUR ACTUAL DATACLASSES HERE  ────────────────
# from schema import NodeLabel, EdgeType, Document, DocumentChunk, Tag, Interaction
# (The Enum stubs below are only to keep this file self-contained.)

class NodeLabel(str, Enum):
    DOCUMENT = "Document"
    CHUNK = "DocumentChunk"
    TAG = "Tag"
    INTERACTION = "Interaction"

class EdgeType(str, Enum):
    CHUNK_OF = "CHUNK_OF"
    TAGGED_AS = "TAGGED_AS"
    FOLLOWS = "FOLLOWS"

# Base dataclass protocol (only for type hints in this file)
class BaseNode:  # pragma: no cover
    id: str
    def to_dict(self) -> Dict[str, Any]: ...

# ════════════════════════════════════════════════════════════════════════
#  MemGraphClient
# ════════════════════════════════════════════════════════════════════════
class MemGraphClient:


    # ───── Connection boilerplate ─────
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 7687,
        username: str | None = None,
        password: str | None = None,
        **kwargs,
    ) -> None:
        self._conn = mgclient.connect(
            host=host,
            port=port,
            user=username,
            password=password,
            **kwargs,
        )
        self._conn.autocommit = True
        self._cur = self._conn.cursor()

    def close(self) -> None:
        self._cur.close()
        self._conn.close()

    # Context-manager support
    def __enter__(self) -> "MemGraphClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    # ───── Private utilities ─────
    @staticmethod
    def _props(node: BaseNode) -> Dict[str, Any]:
        out = asdict(node)
        for k, v in out.items():
            if isinstance(v, datetime):
                out[k] = v.isoformat()
        return out

    def _create_node(self, label: NodeLabel, props: Dict[str, Any]) -> str:
        q = f"CREATE (n:`{label.value}`) SET n += $props RETURN n.id"
        self._cur.execute(q, {"props": props})
        return self._cur.fetchone()[0]

    def _link(
        self,
        left_label: NodeLabel,
        left_id: str,
        edge: EdgeType,
        right_label: NodeLabel,
        right_id: str,
    ) -> None:
        q = (
            f"MATCH (a:`{left_label.value}` {{id: $lid}}), "
            f"(b:`{right_label.value}` {{id: $rid}}) "
            f"MERGE (a)-[r:`{edge.value}`]->(b)"
        )
        self._cur.execute(q, {"lid": left_id, "rid": right_id})

    # ───── CRUD helpers (unchanged) ─────
    def create_document(self, doc: BaseNode) -> str:
        return self._create_node(NodeLabel.DOCUMENT, self._props(doc))

    def create_chunk(self, chunk: BaseNode, link_to_document: bool = True) -> str:
        node_id = self._create_node(NodeLabel.CHUNK, self._props(chunk))
        if link_to_document:
            self._link(
                NodeLabel.CHUNK,
                chunk.id,
                EdgeType.CHUNK_OF,
                NodeLabel.DOCUMENT,
                chunk.parent_document_id,
            )
        return node_id

    def create_tag(self, tag: BaseNode) -> str:
        return self._create_node(NodeLabel.TAG, self._props(tag))

    def create_interaction(
        self, interaction: BaseNode, prev_interaction_id: str | None = None
    ) -> str:
        node_id = self._create_node(NodeLabel.INTERACTION, self._props(interaction))
        if prev_interaction_id:
            self._link(
                NodeLabel.INTERACTION,
                prev_interaction_id,
                EdgeType.FOLLOWS,
                NodeLabel.INTERACTION,
                interaction.id,
            )
        return node_id

    def tag_node(self, target_node_id: str, tag_id: str) -> None:
        q = (
            "MATCH (t {id: $tid}), (tag:Tag {id: $tgid}) "
            "MERGE (t)-[:TAGGED_AS]->(tag)"
        )
        self._cur.execute(q, {"tid": target_node_id, "tgid": tag_id})

    # ────────────────────────────────────────────────────────────────────
    #  VECTOR INDEX + SEARCH
    # ────────────────────────────────────────────────────────────────────
    def create_vector_index(
        self,
        index_name: str,
        label: NodeLabel,
        property_name: str,
        dimension: int,
        capacity: int = 4096,
        metric: str = "cos",
        resize_coefficient: int = 2,
    ) -> None:
        """
        CREATE VECTOR INDEX <index_name> ON :<Label>(<property>)
        WITH CONFIG {"dimension": <d>, "capacity": <c>, ...}
        """
        q = (
            f"CREATE VECTOR INDEX {index_name} "
            f"ON :`{label.value}`({property_name}) "
            f"WITH CONFIG {{"
            f' "dimension": {dimension}, '
            f' "capacity": {capacity}, '
            f' "metric": "{metric}", '
            f' "resize_coefficient": {resize_coefficient}'
            f" }};"
        )
        self._cur.execute(q)

    def list_vector_indices(self) -> List[Dict[str, Any]]:
        """
        Returns a list of dicts describing every vector index in the db.
        """
        q = "CALL vector_search.show_index_info() YIELD * RETURN *"
        self._cur.execute(q)
        return [dict(row) for row in self._cur.fetchall()]

    def vector_search(
        self,
        index_name: str,
        query_vector: Sequence[float],
        k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        RUN: CALL vector_search.search($index_name, $k, $query_vector) YIELD *
        RETURN node, distance, similarity
        """
        q = (
            "CALL vector_search.search($idx, $k, $vec) "
            "YIELD node, distance, similarity "
            "RETURN node, distance, similarity"
        )
        self._cur.execute(q, {"idx": index_name, "k": k, "vec": list(query_vector)})
        # Each row comes back as (node, distance, similarity)
        return [
            {
                "node": dict(row[0]),
                "distance": row[1],
                "similarity": row[2],
            }
            for row in self._cur.fetchall()
        ]

    # Convenience wrapper for the common case: similarity search on chunks
    def search_chunks(
        self,
        query_vector: Sequence[float],
        k: int = 5,
        index_name: str = "chunk_embedding_index",
    ) -> List[Dict[str, Any]]:
        return self.vector_search(index_name, query_vector, k)