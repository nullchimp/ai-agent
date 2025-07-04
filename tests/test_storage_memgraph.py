import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from core.models import AgentSession, ConversationMessage, SessionStatus, MemoryEntry, MemoryType, MemoryImportance
from core.storage.memgraph_storage import MemgraphSessionRepository, MemgraphMemoryRepository


class TestMemgraphSessionRepository:
    @pytest.fixture
    def mock_client(self):
        client = MagicMock()
        client._execute = MagicMock()
        client._cur = MagicMock()
        return client
    
    @pytest.fixture
    def session_repo(self, mock_client):
        return MemgraphSessionRepository(mock_client)
    
    @pytest.fixture
    def sample_session(self):
        return AgentSession(
            session_id="test-session-123",
            user_id="user-456",
            title="Test Session",
            status=SessionStatus.ACTIVE
        )
    
    async def test_create_session(self, session_repo, mock_client, sample_session):
        result = await session_repo.create_session(sample_session)
        
        assert result == sample_session
        mock_client._execute.assert_called_once()
        call_args = mock_client._execute.call_args
        assert "CREATE (s:AgentSession" in call_args[0][0]
        assert call_args[0][1]["session_id"] == "test-session-123"
    
    async def test_get_session_found(self, session_repo, mock_client):
        mock_node = MagicMock()
        mock_node.properties = {
            "session_id": "test-session-123",
            "user_id": "user-456",
            "title": "Test Session",
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat(),
            "metadata": "{}",
            "conversation_history": "[]"
        }
        mock_client._cur.fetchone.return_value = [mock_node]
        
        result = await session_repo.get_session("test-session-123")
        
        assert result is not None
        assert result.session_id == "test-session-123"
        assert result.user_id == "user-456"
        assert result.status == SessionStatus.ACTIVE
    
    async def test_get_session_not_found(self, session_repo, mock_client):
        mock_client._cur.fetchone.return_value = None
        
        result = await session_repo.get_session("nonexistent")
        
        assert result is None
    
    async def test_update_session(self, session_repo, mock_client, sample_session):
        sample_session.title = "Updated Title"
        
        result = await session_repo.update_session(sample_session)
        
        assert result == sample_session
        mock_client._execute.assert_called_once()
        call_args = mock_client._execute.call_args
        assert "SET s.title = $title" in call_args[0][0]
        assert call_args[0][1]["title"] == "Updated Title"
    
    async def test_delete_session(self, session_repo, mock_client):
        result = await session_repo.delete_session("test-session-123")
        
        assert result is True
        mock_client._execute.assert_called_once()
        call_args = mock_client._execute.call_args
        assert "DELETE s" in call_args[0][0]
    
    async def test_list_sessions_with_user_id(self, session_repo, mock_client):
        mock_client._cur.fetchall.return_value = []
        
        result = await session_repo.list_sessions(user_id="user-456", limit=10)
        
        assert result == []
        mock_client._execute.assert_called_once()
        call_args = mock_client._execute.call_args
        assert "user_id: $user_id" in call_args[0][0]
        assert call_args[0][1]["user_id"] == "user-456"
    
    async def test_get_active_sessions(self, session_repo, mock_client):
        mock_client._cur.fetchall.return_value = []
        
        result = await session_repo.get_active_sessions()
        
        assert result == []
        mock_client._execute.assert_called_once()
        call_args = mock_client._execute.call_args
        assert "status: 'active'" in call_args[0][0]


class TestMemgraphMemoryRepository:
    @pytest.fixture
    def mock_client(self):
        client = MagicMock()
        client._execute = MagicMock()
        client._cur = MagicMock()
        return client
    
    @pytest.fixture
    def memory_repo(self, mock_client):
        return MemgraphMemoryRepository(mock_client)
    
    @pytest.fixture
    def sample_memory(self):
        return MemoryEntry(
            session_id="test-session-123",
            memory_type=MemoryType.WORKING,
            content="Test memory content",
            importance=MemoryImportance.MEDIUM
        )
    
    async def test_store_memory(self, memory_repo, mock_client, sample_memory):
        result = await memory_repo.store_memory(sample_memory)
        
        assert result == sample_memory
        mock_client._execute.assert_called_once()
        call_args = mock_client._execute.call_args
        assert "CREATE (m:MemoryEntry" in call_args[0][0]
        assert call_args[0][1]["session_id"] == "test-session-123"
        assert call_args[0][1]["memory_type"] == "working"
    
    async def test_get_memory_found(self, memory_repo, mock_client):
        mock_node = MagicMock()
        mock_node.properties = {
            "id": "memory-123",
            "session_id": "test-session-123",
            "memory_type": "working",
            "content": "Test memory content",
            "importance": "medium",
            "created_at": datetime.utcnow().isoformat(),
            "last_accessed": datetime.utcnow().isoformat(),
            "access_count": 0,
            "tags": "[]",
            "metadata": "{}",
            "related_messages": "[]"
        }
        mock_client._cur.fetchone.return_value = [mock_node]
        
        result = await memory_repo.get_memory("memory-123")
        
        assert result is not None
        assert result.id == "memory-123"
        assert result.memory_type == MemoryType.WORKING
        assert result.content == "Test memory content"
    
    async def test_get_memory_not_found(self, memory_repo, mock_client):
        mock_client._cur.fetchone.return_value = None
        
        result = await memory_repo.get_memory("nonexistent")
        
        assert result is None
    
    async def test_get_session_memories_with_type_filter(self, memory_repo, mock_client):
        mock_client._cur.fetchall.return_value = []
        
        result = await memory_repo.get_session_memories(
            "test-session-123", 
            memory_type=MemoryType.EPISODIC,
            limit=50
        )
        
        assert result == []
        mock_client._execute.assert_called_once()
        call_args = mock_client._execute.call_args
        assert "memory_type: $memory_type" in call_args[0][0]
        assert call_args[0][1]["memory_type"] == "episodic"
    
    async def test_search_memories(self, memory_repo, mock_client):
        mock_client._cur.fetchall.return_value = []
        
        result = await memory_repo.search_memories(
            query="test query",
            session_id="test-session-123",
            memory_type=MemoryType.SEMANTIC,
            limit=10
        )
        
        assert result == []
        mock_client._execute.assert_called_once()
        call_args = mock_client._execute.call_args
        assert "CONTAINS $query" in call_args[0][0]
        assert call_args[0][1]["query"] == "test query"
        assert call_args[0][1]["session_id"] == "test-session-123"
        assert call_args[0][1]["memory_type"] == "semantic"