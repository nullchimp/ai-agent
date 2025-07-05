import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Self

class EdgeType(Enum):
    CHUNK_OF = "CHUNK_OF"          # DocumentChunk ➜ Document
    FOLLOWS = "FOLLOWS"            # Interaction ➜ Interaction
    SOURCED_FROM = "SOURCED_FROM"  # Document ➜ Source
    STORED_IN = "STORED_IN"        # Vector ➜ VectorStore
    EMBEDDING_OF = "EMBEDDING_OF"  # Vector ➜ DocumentChunk
    REFERENCES = "REFERENCES"      # Document ➜ Source

registry = {}

class Node:
    @classmethod
    def label(cls) -> str:
        return cls.__name__.upper()

    def __init_subclass__(cls):
        super().__init_subclass__()
        registry[cls.__name__] = cls

    def __init__(self, *args, **kwargs):
        self.id = uuid.uuid4()
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        self.metadata = {}

    def fill(self, key: str, value: Any) -> None:
        self.__dict__[key] = value

    def create(self) -> str:
        q = f"MERGE (n:`{self.label()}` {{id: $id}}) SET n += $props RETURN n.id"
        return [q, {"id": str(self.id), "props": self.to_dict()}]

    def link(
        self,
        edge: EdgeType,
        nodeType: type["Node"],
        to_id: str,
    ) -> None:
        q = (
            f"MATCH (a:`{self.label()}` {{id: $lid}}), "
            f"(b:`{nodeType.label()}` {{id: $rid}}) "
            f"MERGE (a)-[r:`{edge.value}`]->(b)"
        )
        return [q, {"lid": str(self.id), "rid": str(to_id)}]

    def to_dict(self) -> dict:
        def _value(v):
            if isinstance(v, datetime):
                return v.isoformat()
            if isinstance(v, Enum):
                return v.value
            if isinstance(v, uuid.UUID):
                return str(v)
            if isinstance(v, Node):
                result = v.to_dict()
                result["__class__"] = v.__class__.__name__
                return result
            if isinstance(v, list) or isinstance(v, set):
                return [_value(item) for item in v]
            if isinstance(v, dict):
                return {k: _value(val) for k, val in v.items()}
            if isinstance(v, tuple):
                return tuple(_value(item) for item in v)
            return v

        return {key: _value(value) for key, value in self.__dict__.items() if not (callable(value) or key.startswith('_'))}
    
    @classmethod
    def from_dict(cls, data: dict) -> "Node":
        def _from_value(v):
            if isinstance(v, dict) and "__class__" in v:
                class_name = v.pop("__class__")
                if class_name not in registry:
                    raise ValueError(f"Class {class_name} not found in registry")
                return registry[class_name].from_dict(v)
            if isinstance(v, dict):
                return {k: _from_value(val) for k, val in v.items()}
            if isinstance(v, list):
                return [_from_value(item) for item in v]
            if isinstance(v, tuple):
                return tuple(_from_value(item) for item in v)
            if isinstance(v, str):
                try:
                    return uuid.UUID(v)
                except ValueError:
                    try:
                        return datetime.fromisoformat(v)
                    except ValueError:
                        return v
            return v

        data_copy = data.copy()
        if "__class__" in data_copy:
            class_name = data_copy.pop("__class__")
            if class_name in registry and cls != registry[class_name]:
                return registry[class_name].from_dict(data_copy)
        
        instance = cls.__new__(cls)
        for key, value in data_copy.items():
            setattr(instance, key, _from_value(value))
        
        return instance

        
    def add_metadata(self, *args, **kwargs):
        for key, value in kwargs.items():
            self.metadata[key] = value

# Import all schemas
from core.db.schemas.knowledge_base import *
from core.db.schemas.session import *
from core.db.schemas.user import *