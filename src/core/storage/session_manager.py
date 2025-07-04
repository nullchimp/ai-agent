from typing import Optional, Dict, Any
import os

from core.models import AgentSession, SessionStatus
from core.storage import MemgraphStorageManager
from core.memory import MemoryCoordinator


class PersistentSessionManager:
    def __init__(self, storage_manager: MemgraphStorageManager = None):
        if storage_manager is None:
            # Use environment variables or defaults
            host = os.getenv("MEMGRAPH_HOST", "127.0.0.1")
            port = int(os.getenv("MEMGRAPH_PORT", "7687"))
            username = os.getenv("MEMGRAPH_USERNAME")
            password = os.getenv("MEMGRAPH_PASSWORD")
            
            self.storage_manager = MemgraphStorageManager(
                host=host, 
                port=port, 
                username=username, 
                password=password
            )
        else:
            self.storage_manager = storage_manager
        
        self.memory_coordinator = MemoryCoordinator(self.storage_manager.memory_repo)
        self._initialized = False
    
    async def initialize(self) -> None:
        if not self._initialized:
            await self.storage_manager.initialize()
            self._initialized = True
    
    async def create_session(self, user_id: Optional[str] = None, title: str = "New Session") -> AgentSession:
        await self.initialize()
        
        session = AgentSession(
            user_id=user_id,
            title=title,
            status=SessionStatus.ACTIVE
        )
        
        return await self.storage_manager.session_repo.create_session(session)
    
    async def get_session(self, session_id: str) -> Optional[AgentSession]:
        await self.initialize()
        return await self.storage_manager.session_repo.get_session(session_id)
    
    async def update_session(self, session: AgentSession) -> AgentSession:
        await self.initialize()
        return await self.storage_manager.session_repo.update_session(session)
    
    async def delete_session(self, session_id: str) -> bool:
        await self.initialize()
        return await self.storage_manager.session_repo.delete_session(session_id)
    
    async def add_message(self, session_id: str, role: str, content: str, used_tools: list = None) -> AgentSession:
        await self.initialize()
        
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Add message to session
        session.add_message(role, content, used_tools)
        
        # Update session in storage
        await self.update_session(session)
        
        # Process through memory system if it's a complete interaction
        if role == "assistant":
            # Find the last user message
            user_messages = [msg for msg in session.conversation_history if msg.role == "user"]
            if user_messages:
                last_user_message = user_messages[-1]
                await self.memory_coordinator.process_interaction(
                    session_id=session_id,
                    user_input=last_user_message.content,
                    agent_response=content,
                    tools_used=used_tools or []
                )
        
        return session
    
    async def get_context_for_response(self, session_id: str, query: str) -> Dict[str, Any]:
        await self.initialize()
        
        # Get memory context
        memory_context = await self.memory_coordinator.get_context_for_response(session_id, query)
        
        # Get recent conversation history
        session = await self.get_session(session_id)
        recent_messages = session.get_recent_messages(10) if session else []
        
        return {
            "memory_context": memory_context,
            "recent_messages": [{"role": msg.role, "content": msg.content} for msg in recent_messages]
        }
    
    async def get_active_sessions(self) -> list:
        await self.initialize()
        return await self.storage_manager.session_repo.get_active_sessions()
    
    async def archive_session(self, session_id: str) -> bool:
        await self.initialize()
        
        session = await self.get_session(session_id)
        if not session:
            return False
        
        session.status = SessionStatus.ARCHIVED
        await self.update_session(session)
        return True
    
    async def cleanup_old_sessions(self, days_inactive: int = 30) -> int:
        await self.initialize()
        
        from datetime import datetime, timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days_inactive)
        
        sessions = await self.storage_manager.session_repo.list_sessions(limit=1000)
        archived_count = 0
        
        for session in sessions:
            if session.last_activity < cutoff_date and session.status == SessionStatus.ACTIVE:
                session.status = SessionStatus.ARCHIVED
                await self.update_session(session)
                archived_count += 1
        
        return archived_count
    
    async def health_check(self) -> bool:
        await self.initialize()
        return await self.storage_manager.health_check()
    
    async def close(self) -> None:
        if self._initialized:
            await self.storage_manager.close()
            self._initialized = False


# Global session manager instance
_session_manager: Optional[PersistentSessionManager] = None


def get_session_manager() -> PersistentSessionManager:
    global _session_manager
    if _session_manager is None:
        _session_manager = PersistentSessionManager()
    return _session_manager


async def cleanup_session_manager() -> None:
    global _session_manager
    if _session_manager is not None:
        await _session_manager.close()
        _session_manager = None