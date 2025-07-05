import hashlib
from typing import List

from .base import Node


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
        self.content_hash = hashlib.sha256(content.encode()).hexdigest()
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
        self.content_hash = hashlib.sha256(content.encode()).hexdigest()
        self.parent_id = parent_id
        self.chunk_index = chunk_index
        self.token_count = token_count