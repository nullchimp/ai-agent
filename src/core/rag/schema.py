from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
import uuid


# ────────────────────────────────
#  Graph semantics (optional)
# ────────────────────────────────

class NodeLabel(Enum):
    DOCUMENT = "Document"
    CHUNK = "DocumentChunk"
    TAG = "Tag"
    INTERACTION = "Interaction"


class EdgeType(Enum):
    CHUNK_OF = "CHUNK_OF"          # DocumentChunk ➜ Document
    TAGGED_AS = "TAGGED_AS"        # {Document, Chunk} ➜ Tag
    FOLLOWS = "FOLLOWS"            # Interaction ➜ Interaction (chronology)

# ────────────────────────────────
#  Core nodes
# ────────────────────────────────

@dataclass
class Document:
    id: str
    path: str
    content: str
    title: str = ""
    source_uri: str = ""
    content_hash: str = ""
    embedding_version: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class DocumentChunk:
    id: str
    path: str
    content: str
    parent_document_id: str
    chunk_index: int = 0
    token_count: int = 0
    embedding: Optional[List[float]] = None
    content_hash: str = ""
    embedding_version: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Tag:
    id: str
    name: str
    embedding: Optional[List[float]] = None

@dataclass
class Interaction:
    id: str
    session_id: str
    content: str
    role: str                   # "user", "assistant", "system", …
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    embedding: Optional[List[float]] = None