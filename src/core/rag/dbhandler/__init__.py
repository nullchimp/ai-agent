# one-off: ensure an index exists (once per DB)
# mg.create_vector_index(
#     index_name="chunk_embedding_index",
#     label=NodeLabel.CHUNK,
#     property_name="embedding",
#     dimension=len(q_vec),
# )

from __future__ import annotations

import mgclient
from typing import Any, Dict, List, Optional, Sequence, Union

from db.schemas import (
    Node as BaseNode,
    EdgeType, 
    Document, 
    DocumentChunk, 
    Interaction,
    Source,
    VectorStore,
    Vector,
    ProcessingStatus
)

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

    # ───── CRUD helpers ─────
    def create_document(self, doc: Document) -> str:
        self._execute(*doc.create())
        
        # Link document to source if source_id is provided
        if doc.source_id:
            self._execute(*doc.link(
                EdgeType.SOURCED_FROM,
                Source.label(),
                doc.source_id
            ))

        if doc._references and len(doc._references):
            for ref in doc._references:
                self._execute(*ref.create())
                self._execute(*doc.link(
                    EdgeType.REFERENCES,
                    ref.label(),
                    ref.id
                ))

    def create_chunk(self, chunk: DocumentChunk) -> str:
        self._execute(*chunk.create())
        
        if not chunk.parent_id:
            raise ValueError("DocumentChunk must have a parent_id")
        
        self._execute(*chunk.link(
            EdgeType.CHUNK_OF,
            Document.label(),
            chunk.parent_id,
        ))

    def create_source(self, source: Source) -> str:
        return self._execute(*source.create())
    
    def create_vector(self, vector: Vector) -> str:
        if not vector.chunk_id:
            raise ValueError("Vector must have a chunk_id")
        
        if not vector.vector_store_id:
            raise ValueError("Vector must have a vector_store_id")

        self._execute(*vector.create())

        self._execute(*vector.link(
            EdgeType.EMBEDDING_OF,
            DocumentChunk.label(),
            vector.chunk_id,
        ))

        self._execute(*vector.link(
            EdgeType.STORED_IN,
            VectorStore.label(),
            vector.vector_store_id,
        ))

    def create_interaction(
        self, interaction: Interaction, prev_interaction_id: str | None = None
    ) -> str:
        node_id = self._execute(*interaction.create())
        if prev_interaction_id:
            self._execute(*interaction.link(
                EdgeType.FOLLOWS,
                Interaction.label(),
                interaction.id,
            ))
        return node_id
        
    def update_chunk_embedding(
        self, 
        chunk_id: str, 
        embedding: List[float], 
        vector_store_id: str
    ) -> str:
        vector = Vector(
            chunk_id=chunk_id,
            vector_store_id=vector_store_id,
            embedding=embedding
        )
        
        return self.create_vector(vector)

    # ────────────────────────────────────────────────────────────────────
    #  VECTOR INDEX + SEARCH
    # ────────────────────────────────────────────────────────────────────
    def create_vector_store(
        self,
        **kwargs: Any
    ) -> VectorStore:
        vector_store = VectorStore(
            model=kwargs["model"],
            status=ProcessingStatus.COMPLETED,
        )

        vector_store.add_metadata(**kwargs)
        
        # Store in the database
        print("Creating vector store...")
        try:
            self._execute(*vector_store.create())
            print(f"Vector store created with ID: {vector_store.id}")
            self._current_vector_store = vector_store
            
            # Create the actual vector index
            q = (
                f"CREATE VECTOR INDEX {str(kwargs['index_name'])} "
                f"ON :`{Vector.label()}`({kwargs['property_name']}) "
                f"WITH CONFIG {{"
                f' "dimension": {kwargs["dimension"]}, '
                f' "capacity": {kwargs["capacity"]}, '
                f' "metric": "{kwargs["metric"]}", '
                f' "resize_coefficient": {kwargs["resize_coefficient"]}'
                f" }};"
            )
            self._execute(q)
            print(f"Vector index {kwargs['index_name']} created successfully")
            
            return vector_store
        except Exception as e:
            print(f"Error creating vector store: {str(e)}")
            raise e

    def vector_search(
        self,
        query_vector: Sequence[float],
        index_name: str,
        k: int = 5,
    ) -> List[Dict[str, Any]]:
        q = (
            "CALL vector_search.search($idx, $k, $vec) "
            "YIELD node, distance, similarity "
            "RETURN node, distance, similarity"
        )
        self._cur.execute(q, {"idx": index_name, "k": k, "vec": list(query_vector)})
        # Each row comes back as (node, distance, similarity)
        return [
            {
                "node": dict(row[0].properties),
                "distance": row[1],
                "similarity": row[2],
            }
            for row in self._cur.fetchall()
        ]
        
    def get_vectors_for_chunk(
        self, 
        chunk_id: str, 
        vector_store_id: Optional[str] = None,
        model: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all Vector nodes associated with a specific chunk.
        Optional filters by vector store ID or model.
        """
        params = {"chunk_id": chunk_id}
        filter_conditions = []
        
        if vector_store_id:
            filter_conditions.append("v.vector_store_id = $vector_store_id")
            params["vector_store_id"] = vector_store_id
            
        if model:
            filter_conditions.append("v.model = $model")
            params["model"] = model
            
        filter_clause = " AND ".join(filter_conditions)
        if filter_clause:
            filter_clause = f"WHERE {filter_clause}"
            
        q = f"""
        MATCH (v:`{Vector.label()}`)-[:EMBEDDING_OF]->(c:`{DocumentChunk.label()}` {{id: $chunk_id}})
        {filter_clause}
        RETURN v
        ORDER BY v.created_at DESC
        """
        
        self._cur.execute(q, params)
        return [dict(row[0].properties) for row in self._cur.fetchall()]

    # Convenience wrapper for the common case: similarity search on chunks
    def search_chunks(
        self,
        query_vector: Sequence[float],
        index_name: str = "vector_embedding_index",
        k: int = 5
    ) -> List[Dict[str, Any]]:
        # First, search for matching vectors
        vector_results = self.vector_search(query_vector, index_name, k)
        
        # For each vector result, fetch the associated chunk
        results = []
        for result in vector_results:
            vector_node = result["node"]
            chunk_id = vector_node.get("chunk_id")
            
            if chunk_id:
                chunk = self.get_by_id(DocumentChunk, chunk_id)
                if chunk:
                    results.append({
                        "chunk": chunk,
                        "vector": vector_node,
                        "distance": result["distance"],
                        "similarity": result["similarity"]
                    })
                    
        return results

    def get_document_chunks(self, document_id: str) -> List[Dict[str, Any]]:
        q = f"""
        MATCH (c:`{DocumentChunk.label()}`)-[:CHUNK_OF]->(d:`{Document.label()}` {{id: $doc_id}})
        RETURN c
        ORDER BY c.chunk_index
        """
        self._cur.execute(q, {"doc_id": document_id})
        return [dict(row[0].properties) for row in self._cur.fetchall()]
    
    def get_references(
        self, 
        document_id: str
    ) -> List[Dict[str, Any]]:
        q = f"""
        MATCH (d:`{Document.label()}` {{id: $doc_id}})-[:REFERENCES]->(s:`{Source.label()}`)
        RETURN s
        """
        self._cur.execute(q, {"doc_id": document_id})
        return [dict(row[0].properties) for row in self._cur.fetchall()]
    
    def get_sources(
        self, 
        document_id: str
    ) -> List[Dict[str, Any]]:
        q = f"""
        MATCH (d:`{Document.label()}` {{id: $doc_id}})-[:SOURCED_FROM]->(s:`{Source.label()}`)
        RETURN s
        """
        self._cur.execute(q, {"doc_id": document_id})
        return [dict(row[0].properties) for row in self._cur.fetchall()]

    def get_by_id(
        self, 
        label: BaseNode | str, 
        node_id: str
    ) -> Optional[Dict[str, Any]]:
        return self.get_by_property(label, "id", node_id, fetch_one=True)
    
    def get_by_property(
        self, 
        label: BaseNode | str, 
        property_name: str,
        property_value: Any,
        fetch_one: bool = False
    ) -> Optional[Dict[str, Any]]:
        if issubclass(label, BaseNode) or isinstance(label, BaseNode):
            label = label.label()

        q = f"MATCH (n:`{label}` {{{property_name}: $value}}) RETURN n"
        self._cur.execute(q, {"value": property_value})

        if fetch_one:
            result = self._cur.fetchone()
            if result:
                return dict(result[0].properties)
            return None
        
        return [dict(row[0].properties) for row in self._cur.fetchall()]

    def get_source_by_chunk(
        self, 
        chunk_id: str
    ) -> Optional[Dict[str, Any]]:
        q = f"""
        MATCH (c:`{DocumentChunk.label()}` {{id: $chunk_id}})-[:CHUNK_OF]->(d:`{Document.label()}`) -[:SOURCED_FROM]->(s:`{Source.label()}`)
        RETURN s
        """
        self._cur.execute(q, {"chunk_id": chunk_id})
        result = self._cur.fetchone()
        if result:
            return dict(result[0].properties)
        return None

    def load_vector_store(
        self,
        model: str = None,
        vector_store_id: str = None
    ) -> VectorStore:
        if not (vector_store_id or model):
            raise ValueError("Either model or vector_store_id must be provided")
        
        prop = "id"
        value = vector_store_id
        if not vector_store_id:
            prop = "model"
            value = model

        vs_dict = self.get_by_property(
            VectorStore,
            prop,
            value,
            fetch_one=True
        )

        if not vs_dict:
            return None
        
        print(f"Loaded vector store: {vs_dict}")
        # Create a VectorStore object from the dictionary
        vector_store = VectorStore(
            model=vs_dict.get('model', '')
        )

        for key, value in vs_dict.items():
            if key not in ['model', 'id']:
                vector_store.fill(key, value)

        return vector_store