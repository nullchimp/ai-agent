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

from core.rag.schema import (
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
        # Remove bolt:// prefix if present in host
        if host.startswith("bolt://"):
            host = host.replace("bolt://", "")
            
        # Handle localhost -> 127.0.0.1 conversion (more reliable)
        if host == "localhost":
            host = "127.0.0.1"
            
        try:
            print(f"Connecting to Memgraph at {host}:{port}")
            self._conn = mgclient.connect(
                host=host,
                port=port,
                username=username,
                password=password,
                **kwargs,
            )
            self._conn.autocommit = True
            self._cur = self._conn.cursor()
            print(f"Connected successfully to Memgraph")
        except Exception as e:
            print(f"Connection error: {str(e)}")
            raise ConnectionError(f"Failed to connect to Memgraph at {host}:{port}: {str(e)}") from e

    def close(self) -> None:
        self._cur.close()
        self._conn.close()

    # Context-manager support
    def __enter__(self) -> "MemGraphClient":
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

    def create_chunk(self, chunk: DocumentChunk) -> str:
        self._execute(*chunk.create())
        
        if not chunk.parent_document_id:
            raise ValueError("DocumentChunk must have a parent_document_id")
        
        self._execute(*chunk.link(
            EdgeType.CHUNK_OF,
            DocumentChunk.label(),
            chunk.parent_document_id,
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
            raise

    def list_vector_indices(self) -> List[Dict[str, Any]]:
        q = "CALL vector_search.show_index_info() YIELD * RETURN *"
        self._cur.execute(q)
        return [dict(row) for row in self._cur.fetchall()]

    def vector_search(
        self,
        index_name: str,
        query_vector: Sequence[float],
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
        k: int = 5,
        index_name: str = "vector_embedding_index"
    ) -> List[Dict[str, Any]]:
        # First, search for matching vectors
        vector_results = self.vector_search(index_name, query_vector, k)
        
        # For each vector result, fetch the associated chunk
        results = []
        for result in vector_results:
            vector_node = result["node"]
            chunk_id = vector_node.get("chunk_id")
            
            if chunk_id:
                chunk = self.get_chunk_by_id(chunk_id)
                if chunk:
                    results.append({
                        "chunk": chunk,
                        "vector": vector_node,
                        "distance": result["distance"],
                        "similarity": result["similarity"]
                    })
                    
        return results
        
    def get_chunk_by_id(self, chunk_id: str) -> Dict[str, Any]:
        q = f"MATCH (c:`{DocumentChunk.label()}` {{id: $id}}) RETURN c"
        self._cur.execute(q, {"id": chunk_id})
        result = self._cur.fetchone()
        if result:
            return dict(result[0].properties)
        return None
    
    def get_document_chunks(self, document_id: str) -> List[Dict[str, Any]]:
        q = f"""
        MATCH (c:`{DocumentChunk.label()}`)-[:CHUNK_OF]->(d:`{Document.label()}` {{id: $doc_id}})
        RETURN c
        ORDER BY c.chunk_index
        """
        self._cur.execute(q, {"doc_id": document_id})
        return [dict(row[0].properties) for row in self._cur.fetchall()]
        
    def get_document_by_id(self, document_id: str) -> Dict[str, Any]:
        q = "MATCH (d:Document {id: $id}) RETURN d"
        self._cur.execute(q, {"id": document_id})
        result = self._cur.fetchone()
        if result:
            return dict(result[0].properties)
        return None
    
    def load_vector_store(
        self,
        model: str = None,
        vector_store_id: str = None
    ) -> VectorStore:
        if vector_store_id:
            # Find vector store by ID
            q = f"MATCH (vs:`{VectorStore.label()}` {{id: $id}}) RETURN vs"
            self._cur.execute(q, {"id": vector_store_id})
        elif model:
            # Find vector store by model name
            q = f"MATCH (vs:`{VectorStore.label()}` {{model: $model}}) RETURN vs"
            self._cur.execute(q, {"model": model})
        else:
            raise ValueError("Either model or vector_store_id must be provided")
        
        result = self._cur.fetchone()
        if not result:
            return None
        
        print(f"Found vector store: {result}")
        vs_dict = dict(result[0].properties)
        print(f"Loaded vector store: {vs_dict}")
        # Create a VectorStore object from the dictionary
        vector_store = VectorStore(
            model=vs_dict.get('model', '')
        )

        for key, value in vs_dict.items():
            if key not in ['model', 'id']:
                vector_store.fill(key, value)

        vector_store.id = vs_dict.get('id')
        return vector_store
    
    def get_vector_by_id(self, vector_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a Vector node by its ID.
        """
        q = f"MATCH (v:`{Vector.label()}` {{id: $id}}) RETURN v"
        self._cur.execute(q, {"id": vector_id})
        result = self._cur.fetchone()
        return dict(result[0].properties) if result else None