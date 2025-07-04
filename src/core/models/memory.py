from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class MemoryType(str, Enum):
    WORKING = "working"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"


class MemoryImportance(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MemoryEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    session_id: str
    memory_type: MemoryType
    content: str
    importance: MemoryImportance = MemoryImportance.MEDIUM
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_accessed: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    access_count: int = 0
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    related_messages: List[str] = Field(default_factory=list)
    
    def access(self) -> None:
        self.last_accessed = datetime.now(timezone.utc)
        self.access_count += 1
    
    def add_tag(self, tag: str) -> None:
        if tag not in self.tags:
            self.tags.append(tag)
    
    def update_importance(self, importance: MemoryImportance) -> None:
        self.importance = importance