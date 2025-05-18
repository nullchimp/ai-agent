from __future__ import annotations

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

from datetime import datetime, timezone
from enum import Enum
from typing import List, Dict, Any
import uuid


# ────────────────────────────────
#  Graph semantics (optional)
# ────────────────────────────────

class ProcessingStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class EdgeType(Enum):
    CHUNK_OF = "CHUNK_OF"          # DocumentChunk ➜ Document
    FOLLOWS = "FOLLOWS"            # Interaction ➜ Interaction
    SOURCED_FROM = "SOURCED_FROM"  # Document ➜ Source
    STORED_IN = "STORED_IN"        # Vector ➜ VectorStore
    EMBEDDING_OF = "EMBEDDING_OF"  # Vector ➜ DocumentChunk
    REFERENCES = "REFERENCES"      # Document ➜ Source

# ────────────────────────────────
#  Core nodes
# ────────────────────────────────

class Node:
    @classmethod
    def label(cls) -> str:
        return cls.__name__.upper()

    def __init__(self, *args, **kwargs):
        self.id = uuid.uuid4()
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        self.metadata = {}

    def fill(self, key: str, value: Any) -> None:
        self.__dict__[key] = value

    def create(self) -> str:
        label = self.__class__.__name__.upper()
        q = f"MERGE (n:`{label}` {{id: $id}}) SET n += $props RETURN n.id"
        return [q, {"id": str(self.id), "props": self.to_dict()}]

    def link(
        self,
        edge: EdgeType,
        nodeType: str,
        to_id: str,
    ) -> None:
        label = self.__class__.__name__.upper()
        q = (
            f"MATCH (a:`{label}` {{id: $lid}}), "
            f"(b:`{nodeType}` {{id: $rid}}) "
            f"MERGE (a)-[r:`{edge.value}`]->(b)"
        )
        return [q, {"lid": str(self.id), "rid": str(to_id)}]

    def to_dict(self) -> dict:
        def _value(v):
            if isinstance(v, datetime):
                return v.isoformat()
            elif isinstance(v, Enum):
                return v.value
            elif isinstance(v, uuid.UUID):
                return str(v)
            return v

        return {key: _value(value) for key, value in self.__dict__.items() if not (callable(value) or key.startswith('_'))}
    
    def add_metadata(self, *args, **kwargs):
        for key, value in kwargs.items():
            self.metadata[key] = value

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
        parent_document_id: str,
        chunk_index: int = 0,
        token_count: int = 0,
    ):
        super().__init__()
        self.path = path
        self.content = content
        self.content_hash =  hashlib.sha256(content.encode()).hexdigest()
        self.parent_id = parent_document_id
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
        model: str,                           
        status: ProcessingStatus = ProcessingStatus.PENDING
    ):
        super().__init__()
        self.status = status
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