import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from core.models import MemoryEntry, MemoryType, MemoryImportance
from core.memory import MemoryCoordinator, WorkingMemory, EpisodicMemory, SemanticMemory


class TestWorkingMemory:
    @pytest.fixture
    def mock_memory_repo(self):
        repo = AsyncMock()
        repo.store_memory = AsyncMock()
        repo.get_session_memories = AsyncMock(return_value=[])
        repo.delete_memory = AsyncMock(return_value=True)
        return repo
    
    @pytest.fixture
    def working_memory(self, mock_memory_repo):
        return WorkingMemory(mock_memory_repo, max_size=5)
    
    async def test_add_memory(self, working_memory, mock_memory_repo):
        result = await working_memory.add_memory(
            session_id="test-session-123",
            content="Test working memory",
            importance=MemoryImportance.HIGH
        )
        
        assert result.session_id == "test-session-123"
        assert result.memory_type == MemoryType.WORKING
        assert result.content == "Test working memory"
        assert result.importance == MemoryImportance.HIGH
        
        mock_memory_repo.store_memory.assert_called_once_with(result)
    
    async def test_get_context(self, working_memory, mock_memory_repo):
        # Mock repository response
        mock_memories = [
            MemoryEntry(
                session_id="test-session-123",
                memory_type=MemoryType.WORKING,
                content="Memory 1",
                importance=MemoryImportance.HIGH
            ),
            MemoryEntry(
                session_id="test-session-123",
                memory_type=MemoryType.WORKING,
                content="Memory 2",
                importance=MemoryImportance.MEDIUM
            )
        ]
        mock_memory_repo.get_session_memories.return_value = mock_memories
        
        result = await working_memory.get_context("test-session-123", limit=5)
        
        assert len(result) == 2
        # Check that memories are sorted by importance (high before medium)
        assert result[0].content == "Memory 1"  # HIGH importance should be first
        assert result[1].content == "Memory 2"  # MEDIUM importance should be second
        mock_memory_repo.get_session_memories.assert_called_once_with(
            session_id="test-session-123",
            memory_type=MemoryType.WORKING,
            limit=5
        )


class TestEpisodicMemory:
    @pytest.fixture
    def mock_memory_repo(self):
        repo = AsyncMock()
        repo.store_memory = AsyncMock()
        repo.get_session_memories = AsyncMock(return_value=[])
        repo.search_memories = AsyncMock(return_value=[])
        return repo
    
    @pytest.fixture
    def episodic_memory(self, mock_memory_repo):
        return EpisodicMemory(mock_memory_repo)
    
    async def test_store_conversation_memory(self, episodic_memory, mock_memory_repo):
        # Mock the store_memory to return the memory object instead of AsyncMock
        async def mock_store(memory):
            return memory
        mock_memory_repo.store_memory.side_effect = mock_store
        
        result = await episodic_memory.store_conversation_memory(
            session_id="test-session-123",
            content="User: Hello\nAgent: Hi there!",
            importance=MemoryImportance.MEDIUM,
            tags=["greeting"],
            related_messages=["msg-1", "msg-2"]
        )
        
        assert result.session_id == "test-session-123"
        assert result.memory_type == MemoryType.EPISODIC
        assert result.content == "User: Hello\nAgent: Hi there!"
        assert result.tags == ["greeting"]
        assert result.related_messages == ["msg-1", "msg-2"]
        
        mock_memory_repo.store_memory.assert_called_once()
    
    async def test_get_conversation_history(self, episodic_memory, mock_memory_repo):
        await episodic_memory.get_conversation_history("test-session-123", limit=20)
        
        mock_memory_repo.get_session_memories.assert_called_once_with(
            session_id="test-session-123",
            memory_type=MemoryType.EPISODIC,
            limit=20
        )
    
    async def test_search_episodes(self, episodic_memory, mock_memory_repo):
        await episodic_memory.search_episodes("greeting", "test-session-123", limit=5)
        
        mock_memory_repo.search_memories.assert_called_once_with(
            query="greeting",
            session_id="test-session-123",
            memory_type=MemoryType.EPISODIC,
            limit=5
        )


class TestSemanticMemory:
    @pytest.fixture
    def mock_memory_repo(self):
        repo = AsyncMock()
        repo.store_memory = AsyncMock()
        repo.get_session_memories = AsyncMock(return_value=[])
        repo.search_memories = AsyncMock(return_value=[])
        return repo
    
    @pytest.fixture
    def semantic_memory(self, mock_memory_repo):
        return SemanticMemory(mock_memory_repo)
    
    async def test_store_knowledge(self, semantic_memory, mock_memory_repo):
        # Mock the store_memory to return the memory object instead of AsyncMock
        async def mock_store(memory):
            return memory
        mock_memory_repo.store_memory.side_effect = mock_store
        
        result = await semantic_memory.store_knowledge(
            session_id="test-session-123",
            content="Python is a programming language",
            importance=MemoryImportance.HIGH,
            tags=["programming", "python"]
        )
        
        assert result.session_id == "test-session-123"
        assert result.memory_type == MemoryType.SEMANTIC
        assert result.content == "Python is a programming language"
        assert result.importance == MemoryImportance.HIGH
        assert result.tags == ["programming", "python"]
        
        mock_memory_repo.store_memory.assert_called_once()
    
    async def test_search_knowledge(self, semantic_memory, mock_memory_repo):
        await semantic_memory.search_knowledge("python", "test-session-123", limit=10)
        
        mock_memory_repo.search_memories.assert_called_once_with(
            query="python",
            session_id="test-session-123",
            memory_type=MemoryType.SEMANTIC,
            limit=10
        )


class TestMemoryCoordinator:
    @pytest.fixture
    def mock_memory_repo(self):
        repo = AsyncMock()
        repo.store_memory = AsyncMock()
        repo.get_session_memories = AsyncMock(return_value=[])
        repo.search_memories = AsyncMock(return_value=[])
        return repo
    
    @pytest.fixture
    def memory_coordinator(self, mock_memory_repo):
        return MemoryCoordinator(mock_memory_repo)
    
    async def test_process_interaction(self, memory_coordinator, mock_memory_repo):
        await memory_coordinator.process_interaction(
            session_id="test-session-123",
            user_input="What is Python?",
            agent_response="Python is a programming language known for its simplicity.",
            tools_used=["web_search"]
        )
        
        # Should store memories in working and episodic memory
        assert mock_memory_repo.store_memory.call_count >= 3  # 2 working + 1 episodic + possible semantic
    
    async def test_get_context_for_response(self, memory_coordinator, mock_memory_repo):
        # Mock different types of memories
        working_memories = [
            MemoryEntry(
                session_id="test-session-123",
                memory_type=MemoryType.WORKING,
                content="Recent context"
            )
        ]
        episodic_memories = [
            MemoryEntry(
                session_id="test-session-123",
                memory_type=MemoryType.EPISODIC,
                content="Past conversation"
            )
        ]
        semantic_memories = [
            MemoryEntry(
                session_id="test-session-123",
                memory_type=MemoryType.SEMANTIC,
                content="Factual knowledge"
            )
        ]
        
        # Configure mock to return different memories based on memory type
        def mock_get_memories(session_id, memory_type=None, limit=None):
            if memory_type == MemoryType.WORKING:
                return working_memories
            return []
        
        def mock_search_memories(query, session_id=None, memory_type=None, limit=None):
            if memory_type == MemoryType.EPISODIC:
                return episodic_memories
            elif memory_type == MemoryType.SEMANTIC:
                return semantic_memories
            return []
        
        mock_memory_repo.get_session_memories.side_effect = mock_get_memories
        mock_memory_repo.search_memories.side_effect = mock_search_memories
        
        result = await memory_coordinator.get_context_for_response(
            "test-session-123",
            "What about Python?"
        )
        
        assert "working_memory" in result
        assert "episodic_memory" in result
        assert "semantic_memory" in result
        assert len(result["working_memory"]) == 1
        assert len(result["episodic_memory"]) == 1
        assert len(result["semantic_memory"]) == 1
    
    async def test_extract_semantic_knowledge(self, memory_coordinator, mock_memory_repo):
        # Test knowledge extraction with indicator phrases
        await memory_coordinator.process_interaction(
            session_id="test-session-123",
            user_input="What is machine learning?",
            agent_response="Machine learning is defined as a method of data analysis that automates analytical model building.",
            tools_used=[]
        )
        
        # Should have stored semantic knowledge due to "is defined as" indicator
        stored_calls = mock_memory_repo.store_memory.call_args_list
        semantic_calls = [call for call in stored_calls 
                         if call[0][0].memory_type == MemoryType.SEMANTIC]
        
        assert len(semantic_calls) > 0  # Should have stored at least one semantic memory