from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from core.models import MemoryEntry, MemoryType, MemoryImportance
from core.storage.interfaces import MemoryRepository


class WorkingMemory:
    def __init__(self, memory_repo: MemoryRepository, max_size: int = 20):
        self.memory_repo = memory_repo
        self.max_size = max_size
        self._buffer: List[MemoryEntry] = []
    
    async def add_memory(self, session_id: str, content: str, importance: MemoryImportance = MemoryImportance.MEDIUM) -> MemoryEntry:
        memory = MemoryEntry(
            session_id=session_id,
            memory_type=MemoryType.WORKING,
            content=content,
            importance=importance
        )
        
        # Store in repository
        await self.memory_repo.store_memory(memory)
        
        # Add to buffer
        self._buffer.append(memory)
        
        # Maintain buffer size
        if len(self._buffer) > self.max_size:
            # Remove oldest low-importance memories first
            self._buffer.sort(key=lambda m: (m.importance.value, m.created_at))
            self._buffer = self._buffer[-self.max_size:]
        
        return memory
    
    async def get_context(self, session_id: str, limit: int = 10) -> List[MemoryEntry]:
        # Get recent working memories from repository
        memories = await self.memory_repo.get_session_memories(
            session_id=session_id,
            memory_type=MemoryType.WORKING,
            limit=limit
        )
        
        # Sort by importance and recency
        # Map importance to numeric values for proper sorting
        importance_order = {
            MemoryImportance.CRITICAL: 4,
            MemoryImportance.HIGH: 3,
            MemoryImportance.MEDIUM: 2,
            MemoryImportance.LOW: 1
        }
        memories.sort(key=lambda m: (importance_order.get(m.importance, 0), m.created_at), reverse=True)
        return memories[:limit]
    
    async def clear_old_memories(self, session_id: str, older_than_hours: int = 24) -> None:
        cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)
        memories = await self.memory_repo.get_session_memories(
            session_id=session_id,
            memory_type=MemoryType.WORKING,
            limit=1000
        )
        
        for memory in memories:
            if memory.created_at < cutoff_time and memory.importance != MemoryImportance.CRITICAL:
                await self.memory_repo.delete_memory(memory.id)


class EpisodicMemory:
    def __init__(self, memory_repo: MemoryRepository):
        self.memory_repo = memory_repo
    
    async def store_conversation_memory(
        self, 
        session_id: str, 
        content: str, 
        importance: MemoryImportance = MemoryImportance.MEDIUM,
        tags: List[str] = None,
        related_messages: List[str] = None
    ) -> MemoryEntry:
        memory = MemoryEntry(
            session_id=session_id,
            memory_type=MemoryType.EPISODIC,
            content=content,
            importance=importance,
            tags=tags or [],
            related_messages=related_messages or []
        )
        
        return await self.memory_repo.store_memory(memory)
    
    async def get_conversation_history(self, session_id: str, limit: int = 50) -> List[MemoryEntry]:
        return await self.memory_repo.get_session_memories(
            session_id=session_id,
            memory_type=MemoryType.EPISODIC,
            limit=limit
        )
    
    async def search_episodes(self, query: str, session_id: str, limit: int = 10) -> List[MemoryEntry]:
        return await self.memory_repo.search_memories(
            query=query,
            session_id=session_id,
            memory_type=MemoryType.EPISODIC,
            limit=limit
        )


class SemanticMemory:
    def __init__(self, memory_repo: MemoryRepository):
        self.memory_repo = memory_repo
    
    async def store_knowledge(
        self, 
        session_id: str, 
        content: str, 
        importance: MemoryImportance = MemoryImportance.MEDIUM,
        tags: List[str] = None
    ) -> MemoryEntry:
        memory = MemoryEntry(
            session_id=session_id,
            memory_type=MemoryType.SEMANTIC,
            content=content,
            importance=importance,
            tags=tags or []
        )
        
        return await self.memory_repo.store_memory(memory)
    
    async def get_knowledge_base(self, session_id: str, limit: int = 100) -> List[MemoryEntry]:
        return await self.memory_repo.get_session_memories(
            session_id=session_id,
            memory_type=MemoryType.SEMANTIC,
            limit=limit
        )
    
    async def search_knowledge(self, query: str, session_id: str, limit: int = 10) -> List[MemoryEntry]:
        return await self.memory_repo.search_memories(
            query=query,
            session_id=session_id,
            memory_type=MemoryType.SEMANTIC,
            limit=limit
        )


class MemoryCoordinator:
    def __init__(self, memory_repo: MemoryRepository):
        self.memory_repo = memory_repo
        self.working_memory = WorkingMemory(memory_repo)
        self.episodic_memory = EpisodicMemory(memory_repo)
        self.semantic_memory = SemanticMemory(memory_repo)
    
    async def process_interaction(
        self, 
        session_id: str, 
        user_input: str, 
        agent_response: str,
        tools_used: List[str] = None
    ) -> None:
        # Store in working memory for immediate context
        await self.working_memory.add_memory(
            session_id=session_id,
            content=f"User: {user_input}",
            importance=MemoryImportance.MEDIUM
        )
        
        await self.working_memory.add_memory(
            session_id=session_id,
            content=f"Agent: {agent_response}",
            importance=MemoryImportance.MEDIUM
        )
        
        # Store in episodic memory for conversation history
        interaction_content = f"User: {user_input}\nAgent: {agent_response}"
        if tools_used:
            interaction_content += f"\nTools used: {', '.join(tools_used)}"
        
        await self.episodic_memory.store_conversation_memory(
            session_id=session_id,
            content=interaction_content,
            importance=MemoryImportance.MEDIUM,
            tags=tools_used or []
        )
        
        # Extract and store important information in semantic memory
        await self._extract_semantic_knowledge(session_id, user_input, agent_response)
    
    async def get_context_for_response(self, session_id: str, query: str) -> Dict[str, Any]:
        # Get working memory context
        working_context = await self.working_memory.get_context(session_id, limit=5)
        
        # Search episodic memory for relevant past interactions
        episodic_context = await self.episodic_memory.search_episodes(query, session_id, limit=3)
        
        # Search semantic memory for relevant knowledge
        semantic_context = await self.semantic_memory.search_knowledge(query, session_id, limit=3)
        
        return {
            "working_memory": [m.content for m in working_context],
            "episodic_memory": [m.content for m in episodic_context],
            "semantic_memory": [m.content for m in semantic_context]
        }
    
    async def _extract_semantic_knowledge(self, session_id: str, user_input: str, agent_response: str) -> None:
        # Simple knowledge extraction logic
        # In a real implementation, this would use NLP/LLM techniques
        
        # Look for facts, definitions, or important insights
        knowledge_indicators = [
            "is defined as", "means", "refers to", "fact:", "remember that",
            "important:", "key point:", "definition:", "note that"
        ]
        
        text_to_analyze = f"{user_input} {agent_response}".lower()
        
        for indicator in knowledge_indicators:
            if indicator in text_to_analyze:
                # Extract the sentence containing the knowledge
                sentences = agent_response.split(".")
                for sentence in sentences:
                    if indicator in sentence.lower():
                        await self.semantic_memory.store_knowledge(
                            session_id=session_id,
                            content=sentence.strip(),
                            importance=MemoryImportance.HIGH,
                            tags=["extracted_knowledge"]
                        )
                        break