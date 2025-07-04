from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from core.models import AgentSession, MemoryEntry, MemoryType


class SessionRepository(ABC):
    @abstractmethod
    async def create_session(self, session: AgentSession) -> AgentSession:
        pass
    
    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[AgentSession]:
        pass
    
    @abstractmethod
    async def update_session(self, session: AgentSession) -> AgentSession:
        pass
    
    @abstractmethod
    async def delete_session(self, session_id: str) -> bool:
        pass
    
    @abstractmethod
    async def list_sessions(self, user_id: Optional[str] = None, limit: int = 100) -> List[AgentSession]:
        pass
    
    @abstractmethod
    async def get_active_sessions(self) -> List[AgentSession]:
        pass


class MemoryRepository(ABC):
    @abstractmethod
    async def store_memory(self, memory: MemoryEntry) -> MemoryEntry:
        pass
    
    @abstractmethod
    async def get_memory(self, memory_id: str) -> Optional[MemoryEntry]:
        pass
    
    @abstractmethod
    async def update_memory(self, memory: MemoryEntry) -> MemoryEntry:
        pass
    
    @abstractmethod
    async def delete_memory(self, memory_id: str) -> bool:
        pass
    
    @abstractmethod
    async def get_session_memories(
        self, 
        session_id: str, 
        memory_type: Optional[MemoryType] = None,
        limit: int = 100
    ) -> List[MemoryEntry]:
        pass
    
    @abstractmethod
    async def search_memories(
        self,
        query: str,
        session_id: Optional[str] = None,
        memory_type: Optional[MemoryType] = None,
        limit: int = 10
    ) -> List[MemoryEntry]:
        pass


class StorageManager(ABC):
    @abstractmethod
    async def initialize(self) -> None:
        pass
    
    @abstractmethod
    async def close(self) -> None:
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        pass