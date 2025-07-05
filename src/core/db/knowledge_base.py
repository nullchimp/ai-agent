from typing import Any, Dict, List, Optional, Sequence

from core.db.schemas import EdgeType
from core.db.schemas.knowledge_base import (
    Node as BaseNode, 
    Document, 
    DocumentChunk, 
    Interaction,
    Source,
    VectorStore,
    Vector
)

from core.db.connection_pool import get_connection_pool

def create_document(doc: Document) -> str:
    pool = get_connection_pool()
    
    with pool.get_connection() as db:
        db._execute(*doc.create())
        
        # Link document to source if source_id is provided
        if doc.source_id:
            db._execute(*doc.link(
                EdgeType.SOURCED_FROM,
                Source,
                doc.source_id
            ))

        if doc._references and len(doc._references):
            for ref in doc._references:
                db._execute(*ref.create())
                db._execute(*doc.link(
                    EdgeType.REFERENCES,
                    ref,
                    ref.id
                ))

def create_chunk(chunk: DocumentChunk) -> str:
    pool = get_connection_pool()
    
    with pool.get_connection() as db:
        db._execute(*chunk.create())
        
        if not chunk.parent_id:
            raise ValueError("DocumentChunk must have a parent_id")
        
        db._execute(*chunk.link(
            EdgeType.CHUNK_OF,
            Document,
            chunk.parent_id,
        ))

def create_source(source: Source) -> str:
    pool = get_connection_pool()
    
    with pool.get_connection() as db:
        return db._execute(*source.create())

def create_vector(vector: Vector) -> str:
    if not vector.chunk_id:
        raise ValueError("Vector must have a chunk_id")
    
    if not vector.vector_store_id:
        raise ValueError("Vector must have a vector_store_id")

    pool = get_connection_pool()
    
    with pool.get_connection() as db:
        db._execute(*vector.create())

        db._execute(*vector.link(
            EdgeType.EMBEDDING_OF,
            DocumentChunk,
            vector.chunk_id,
        ))

        db._execute(*vector.link(
            EdgeType.STORED_IN,
            VectorStore,
            vector.vector_store_id,
        ))

def create_interaction(
    interaction: Interaction, prev_interaction_id: str | None = None
) -> str:
    pool = get_connection_pool()
    
    with pool.get_connection() as db:
        node_id = db._execute(*interaction.create())
        if prev_interaction_id:
            db._execute(*interaction.link(
                EdgeType.FOLLOWS,
                Interaction,
                interaction.id,
            ))
        return node_id
    
def update_chunk_embedding(
    chunk_id: str, 
    embedding: List[float], 
    vector_store_id: str
) -> str:
    pool = get_connection_pool()
    
    with pool.get_connection() as db:
        vector = Vector(
            chunk_id=chunk_id,
            vector_store_id=vector_store_id,
            embedding=embedding
        )
        
        return db.create_vector(vector)

# ────────────────────────────────────────────────────────────────────
#  VECTOR INDEX + SEARCH
# ────────────────────────────────────────────────────────────────────
def create_vector_store(
    **kwargs: Any
) -> VectorStore:
    pool = get_connection_pool()
    
    with pool.get_connection() as db:
        vector_store = VectorStore(
            model=kwargs["model"]
        )

        vector_store.add_metadata(**kwargs)
        
        # Store in the database
        print("Creating vector store...")
        try:
            db._execute(*vector_store.create())
            print(f"Vector store created with ID: {vector_store.id}")
            db._current_vector_store = vector_store
            
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
            db._execute(q)
            print(f"Vector index {kwargs['index_name']} created successfully")
            
            return vector_store
        except Exception as e:
            print(f"Error creating vector store: {str(e)}")
            raise e

def vector_search(
    query_vector: Sequence[float],
    index_name: str,
    k: int = 5,
) -> List[Dict[str, Any]]:
    pool = get_connection_pool()
    
    with pool.get_connection() as db:
        q = (
            "CALL vector_search.search($idx, $k, $vec) "
            "YIELD node, distance, similarity "
            "RETURN node, distance, similarity"
        )
        db._cur.execute(q, {"idx": index_name, "k": k, "vec": list(query_vector)})
        # Each row comes back as (node, distance, similarity)
        return [
            {
                "node": dict(row[0].properties),
                "distance": row[1],
                "similarity": row[2],
            }
            for row in db._cur.fetchall()
        ]
    
def get_vectors_for_chunk(
    chunk_id: str, 
    vector_store_id: Optional[str] = None,
    model: Optional[str] = None
) -> List[Dict[str, Any]]:
    pool = get_connection_pool()
    
    with pool.get_connection() as db:
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
        
        db._cur.execute(q, params)
        return [dict(row[0].properties) for row in db._cur.fetchall()]

# Convenience wrapper for the common case: similarity search on chunks
def search_chunks(
    query_vector: Sequence[float],
    index_name: str = "vector_embedding_index",
    k: int = 5
) -> List[Dict[str, Any]]:
    pool = get_connection_pool()
    
    with pool.get_connection() as db:
        vector_results = db.vector_search(query_vector, index_name, k)
        
        # For each vector result, fetch the associated chunk
        results = []
        for result in vector_results:
            vector_node = result["node"]
            chunk_id = vector_node.get("chunk_id")
            
            if chunk_id:
                chunk = db.get_by_id(DocumentChunk, chunk_id)
                if chunk:
                    results.append({
                        "chunk": chunk,
                        "vector": vector_node,
                        "distance": result["distance"],
                        "similarity": result["similarity"]
                    })
                    
        return results

def get_document_chunks(document_id: str) -> List[Dict[str, Any]]:
    pool = get_connection_pool()
    
    with pool.get_connection() as db:
        q = f"""
        MATCH (c:`{DocumentChunk.label()}`)-[:CHUNK_OF]->(d:`{Document.label()}` {{id: $doc_id}})
        RETURN c
        ORDER BY c.chunk_index
        """
        db._cur.execute(q, {"doc_id": document_id})
        return [dict(row[0].properties) for row in db._cur.fetchall()]

def get_references(
    document_id: str
) -> List[Dict[str, Any]]:
    pool = get_connection_pool()
    
    with pool.get_connection() as db:
        q = f"""
        MATCH (d:`{Document.label()}` {{id: $doc_id}})-[:REFERENCES]->(s:`{Source.label()}`)
        RETURN s
        """
        db._cur.execute(q, {"doc_id": document_id})
        return [dict(row[0].properties) for row in db._cur.fetchall()]

def get_sources(
    document_id: str
) -> List[Dict[str, Any]]:
    pool = get_connection_pool()
    
    with pool.get_connection() as db:
        q = f"""
        MATCH (d:`{Document.label()}` {{id: $doc_id}})-[:SOURCED_FROM]->(s:`{Source.label()}`)
        RETURN s
        """
        db._cur.execute(q, {"doc_id": document_id})
        return [dict(row[0].properties) for row in db._cur.fetchall()]

def get_by_id(
    label: BaseNode | str, 
    node_id: str
) -> Optional[Dict[str, Any]]:
    pool = get_connection_pool()
    
    with pool.get_connection() as db:
        return db.get_by_property(label, "id", node_id, fetch_one=True)

def get_by_property(
    label: BaseNode | str, 
    property_name: str,
    property_value: Any,
    fetch_one: bool = False
) -> Optional[Dict[str, Any]]:
    pool = get_connection_pool()
    
    with pool.get_connection() as db:
        if issubclass(label, BaseNode) or isinstance(label, BaseNode):
            label = label.label()

        q = f"MATCH (n:`{label}` {{{property_name}: $value}}) RETURN n"
        db._cur.execute(q, {"value": property_value})

        if fetch_one:
            result = db._cur.fetchone()
            if result:
                return dict(result[0].properties)
            return None
        
        return [dict(row[0].properties) for row in db._cur.fetchall()]

def get_source_by_chunk(
    chunk_id: str
) -> Optional[Dict[str, Any]]:
    pool = get_connection_pool()
    
    with pool.get_connection() as db:
        q = f"""
        MATCH (c:`{DocumentChunk.label()}` {{id: $chunk_id}})-[:CHUNK_OF]->(d:`{Document.label()}`) -[:SOURCED_FROM]->(s:`{Source.label()}`)
        RETURN s
        """
        db._cur.execute(q, {"chunk_id": chunk_id})
        result = db._cur.fetchone()
        if result:
            return dict(result[0].properties)
        return None

def load_vector_store(
    model: str = None,
    vector_store_id: str = None
) -> VectorStore:
    pool = get_connection_pool()
    
    with pool.get_connection() as db:
        if not (vector_store_id or model):
            raise ValueError("Either model or vector_store_id must be provided")
        
        prop = "id"
        value = vector_store_id
        if not vector_store_id:
            prop = "model"
            value = model

        vs_dict = db.get_by_property(
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