from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Type, TypeVar

T = TypeVar('T', bound='Node')


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
    BELONGS_TO = "BELONGS_TO"      # Session ➜ User


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

    def create(self) -> List[Any]:
        label = self.__class__.__name__.upper()
        q = f"MERGE (n:`{label}` {{id: $id}}) SET n += $props RETURN n.id"
        return [q, {"id": str(self.id), "props": self.to_dict()}]

    def link(
        self,
        edge: EdgeType,
        nodeType: str,
        to_id: str,
    ) -> List[Any]:
        label = self.__class__.__name__.upper()
        q = (
            f"MATCH (a:`{label}` {{id: $lid}}), "
            f"(b:`{nodeType}` {{id: $rid}}) "
            f"MERGE (a)-[r:`{edge.value}`]->(b)"
        )
        return [q, {"lid": str(self.id), "rid": str(to_id)}]

    def to_dict(self) -> Dict[str, Any]:
        def _value(v):
            if isinstance(v, datetime):
                return v.isoformat()
            elif isinstance(v, Enum):
                return v.value
            elif isinstance(v, uuid.UUID):
                return str(v)
            return v

        return {key: _value(value) for key, value in self.__dict__.items() if not (callable(value) or key.startswith('_'))}

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)
    
    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        instance = cls.__new__(cls)
        
        for key, value in data.items():
            if key == 'id' and isinstance(value, str):
                try:
                    instance.id = uuid.UUID(value)
                except ValueError:
                    instance.id = value
            elif key in ['created_at', 'updated_at'] and isinstance(value, str):
                try:
                    setattr(instance, key, datetime.fromisoformat(value.replace('Z', '+00:00')))
                except ValueError:
                    setattr(instance, key, value)
            else:
                setattr(instance, key, value)
        
        if not hasattr(instance, 'metadata'):
            instance.metadata = {}
            
        return instance
    
    @classmethod  
    def from_json(cls: Type[T], json_str: str) -> T:
        data = json.loads(json_str)
        return cls.from_dict(data)

    def add_metadata(self, *args, **kwargs):
        for key, value in kwargs.items():
            self.metadata[key] = value