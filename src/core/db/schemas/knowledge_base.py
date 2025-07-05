from __future__ import annotations

from core.db.schemas import Node

# Graph Schema Relationships:
#
# Node Types:
# - Document: Represents a full document with content and metadata
# - DocumentChunk: Represents a portion of a document used for embeddings
#   (content stored both in graph and vector store for flexibility)
# - Interaction: Represents a chat message or system interaction
# - Source: Represents the origin of documents
# - VectorStore: Represents an embedding storage system
# - Vector: Represents embedding vectors for document chunks
#
# Relationships:
# 1. DocumentChunk →(CHUNK_OF)→ Document
#    Documents are split into chunks for embedding and retrieval
#
# 2. Interaction →(FOLLOWS)→ Interaction
#    Interactions are linked chronologically
#
# 3. Document →(SOURCED_FROM)→ Source
#    Documents are linked to their origin source
#
# 4. Vector →(STORED_IN)→ VectorStore
#    Vectors are stored in specific vector stores
#
# 5. Vector →(EMBEDDING_OF)→ DocumentChunk
#    Vectors are embeddings of document chunks
#
# 6. Document →(REFERENCES)→ Source
#    Documents can reference other sources

import hashlib
from typing import List

class Source(Node):
    def __init__(
        self,
        name: str,
        type: str,                     # e.g., "website", "file", "api"
        uri: str = "",             # Base location/URL
    ):
        super().__init__()
        self.name = name
        self.type = type
        self.uri = uri

class Document(Node):
    def __init__(
        self,
        path: str,
        content: str,
        title: str = "",
        source_id: str = "",            # Reference to Source node
        references: List[str] = None,       # List of source IDs
    ):
        super().__init__()
        self.path = path
        self.content = content
        self.content_hash =  hashlib.sha256(content.encode()).hexdigest()
        self.title = title
        self.source_id = source_id

        # Will not be stored in the graph
        self._references = references or []

class DocumentChunk(Node):
    def __init__(
        self,
        path: str,
        content: str,                   # Keep content in the graph for direct access
        parent_id: str,
        chunk_index: int = 0,
        token_count: int = 0,
    ):
        super().__init__()
        self.path = path
        self.content = content
        self.content_hash =  hashlib.sha256(content.encode()).hexdigest()
        self.parent_id = parent_id
        self.chunk_index = chunk_index
        self.token_count = token_count

class Interaction(Node):
    def __init__(
        self,
        session_id: str,
        content: str,
        role: str,                   # "user", "assistant", "system", …
    ):
        super().__init__()
        self.session_id = session_id
        self.content = content
        self.content_hash =  hashlib.sha256(content.encode()).hexdigest()
        self.role = role

class VectorStore(Node):
    def __init__(
        self,
        model: str
    ):
        super().__init__()
        self.id = hashlib.sha256(model.encode()).hexdigest()[:32]
        self.model = model

class Vector(Node):
    def __init__(
        self,                           
        chunk_id: str,
        vector_store_id: str,           # Reference to VectorStore node
        embedding: List[float],         # The actual embedding vector
    ):
        super().__init__()
        self.chunk_id = chunk_id
        self.vector_store_id = vector_store_id
        self.embedding = embedding