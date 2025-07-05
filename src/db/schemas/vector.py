import hashlib
from typing import List

from .base import Node, ProcessingStatus


class VectorStore(Node):
    def __init__(
        self,
        model: str,                           
        status: ProcessingStatus = ProcessingStatus.PENDING
    ):
        super().__init__()
        self.id = hashlib.sha256(model.encode()).hexdigest()[:32]
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