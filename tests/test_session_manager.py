import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from core.models import AgentSession, SessionStatus
from core.storage.session_manager import PersistentSessionManager


class TestPersistentSessionManager:
    @pytest.fixture
    def mock_storage_manager(self):
        storage_manager = AsyncMock()
        storage_manager.initialize = AsyncMock()
        storage_manager.session_repo = AsyncMock()
        storage_manager.memory_repo = AsyncMock()
        storage_manager.health_check = AsyncMock(return_value=True)
        storage_manager.close = AsyncMock()
        return storage_manager
    
    @pytest.fixture
    def session_manager(self, mock_storage_manager):
        return PersistentSessionManager(storage_manager=mock_storage_manager)
    
    @pytest.fixture
    def sample_session(self):
        return AgentSession(
            session_id="test-session-123",
            user_id="user-456",
            title="Test Session",
            status=SessionStatus.ACTIVE
        )
    
    async def test_create_session(self, session_manager, mock_storage_manager, sample_session):
        mock_storage_manager.session_repo.create_session.return_value = sample_session
        
        result = await session_manager.create_session(
            user_id="user-456",
            title="Test Session"
        )
        
        assert result.user_id == "user-456"
        assert result.title == "Test Session"
        assert result.status == SessionStatus.ACTIVE
        
        mock_storage_manager.initialize.assert_called_once()
        mock_storage_manager.session_repo.create_session.assert_called_once()
    
    async def test_get_session(self, session_manager, mock_storage_manager, sample_session):
        mock_storage_manager.session_repo.get_session.return_value = sample_session
        
        result = await session_manager.get_session("test-session-123")
        
        assert result == sample_session
        mock_storage_manager.session_repo.get_session.assert_called_once_with("test-session-123")
    
    async def test_get_session_not_found(self, session_manager, mock_storage_manager):
        mock_storage_manager.session_repo.get_session.return_value = None
        
        result = await session_manager.get_session("nonexistent")
        
        assert result is None
    
    async def test_add_message_user(self, session_manager, mock_storage_manager, sample_session):
        mock_storage_manager.session_repo.get_session.return_value = sample_session
        mock_storage_manager.session_repo.update_session.return_value = sample_session
        
        result = await session_manager.add_message(
            session_id="test-session-123",
            role="user",
            content="Hello, how are you?"
        )
        
        assert len(result.conversation_history) == 1
        assert result.conversation_history[0].role == "user"
        assert result.conversation_history[0].content == "Hello, how are you?"
        
        mock_storage_manager.session_repo.update_session.assert_called_once()
    
    async def test_add_message_assistant_triggers_memory(self, session_manager, mock_storage_manager, sample_session):
        # Add a user message first
        sample_session.add_message("user", "What is Python?")
        
        mock_storage_manager.session_repo.get_session.return_value = sample_session
        mock_storage_manager.session_repo.update_session.return_value = sample_session
        
        with patch.object(session_manager.memory_coordinator, 'process_interaction') as mock_process:
            result = await session_manager.add_message(
                session_id="test-session-123",
                role="assistant",
                content="Python is a programming language.",
                used_tools=["web_search"]
            )
            
            assert len(result.conversation_history) == 2
            mock_process.assert_called_once_with(
                session_id="test-session-123",
                user_input="What is Python?",
                agent_response="Python is a programming language.",
                tools_used=["web_search"]
            )
    
    async def test_add_message_session_not_found(self, session_manager, mock_storage_manager):
        mock_storage_manager.session_repo.get_session.return_value = None
        
        with pytest.raises(ValueError, match="Session test-session-123 not found"):
            await session_manager.add_message(
                session_id="test-session-123",
                role="user",
                content="Hello"
            )
    
    async def test_get_context_for_response(self, session_manager, mock_storage_manager, sample_session):
        # Add some messages to the session
        sample_session.add_message("user", "What is Python?")
        sample_session.add_message("assistant", "Python is a programming language.")
        
        mock_storage_manager.session_repo.get_session.return_value = sample_session
        
        mock_memory_context = {
            "working_memory": ["Recent context"],
            "episodic_memory": ["Past conversation"],
            "semantic_memory": ["Python facts"]
        }
        
        with patch.object(session_manager.memory_coordinator, 'get_context_for_response') as mock_get_context:
            mock_get_context.return_value = mock_memory_context
            
            result = await session_manager.get_context_for_response(
                "test-session-123",
                "Tell me more about Python"
            )
            
            assert "memory_context" in result
            assert "recent_messages" in result
            assert result["memory_context"] == mock_memory_context
            assert len(result["recent_messages"]) == 2
            
            mock_get_context.assert_called_once_with("test-session-123", "Tell me more about Python")
    
    async def test_archive_session(self, session_manager, mock_storage_manager, sample_session):
        mock_storage_manager.session_repo.get_session.return_value = sample_session
        mock_storage_manager.session_repo.update_session.return_value = sample_session
        
        result = await session_manager.archive_session("test-session-123")
        
        assert result is True
        mock_storage_manager.session_repo.update_session.assert_called_once()
        # Check that the session status was changed to ARCHIVED
        updated_session = mock_storage_manager.session_repo.update_session.call_args[0][0]
        assert updated_session.status == SessionStatus.ARCHIVED
    
    async def test_archive_session_not_found(self, session_manager, mock_storage_manager):
        mock_storage_manager.session_repo.get_session.return_value = None
        
        result = await session_manager.archive_session("nonexistent")
        
        assert result is False
    
    async def test_health_check(self, session_manager, mock_storage_manager):
        result = await session_manager.health_check()
        
        assert result is True
        mock_storage_manager.health_check.assert_called_once()
    
    async def test_close(self, session_manager, mock_storage_manager):
        # Initialize first
        await session_manager.initialize()
        assert session_manager._initialized is True
        
        await session_manager.close()
        
        assert session_manager._initialized is False
        mock_storage_manager.close.assert_called_once()
    
    async def test_cleanup_old_sessions(self, session_manager, mock_storage_manager):
        from datetime import datetime, timedelta
        
        # Create mock sessions with different last activity times
        old_session = AgentSession(
            session_id="old-session",
            title="Old Session",
            status=SessionStatus.ACTIVE
        )
        old_session.last_activity = datetime.utcnow() - timedelta(days=35)
        
        recent_session = AgentSession(
            session_id="recent-session",
            title="Recent Session", 
            status=SessionStatus.ACTIVE
        )
        recent_session.last_activity = datetime.utcnow() - timedelta(days=5)
        
        mock_storage_manager.session_repo.list_sessions.return_value = [old_session, recent_session]
        mock_storage_manager.session_repo.update_session.return_value = old_session
        
        result = await session_manager.cleanup_old_sessions(days_inactive=30)
        
        assert result == 1  # Only one session should be archived
        mock_storage_manager.session_repo.update_session.assert_called_once()
        
        # Check that the old session was archived
        updated_session = mock_storage_manager.session_repo.update_session.call_args[0][0]
        assert updated_session.session_id == "old-session"
        assert updated_session.status == SessionStatus.ARCHIVED


class TestSessionManagerSingleton:
    def test_get_session_manager(self):
        from core.storage.session_manager import get_session_manager
        
        manager1 = get_session_manager()
        manager2 = get_session_manager()
        
        assert manager1 is manager2  # Should be the same instance
        assert isinstance(manager1, PersistentSessionManager)
    
    async def test_cleanup_session_manager(self):
        from core.storage.session_manager import get_session_manager, cleanup_session_manager
        
        manager = get_session_manager()
        with patch.object(manager, 'close') as mock_close:
            await cleanup_session_manager()
            mock_close.assert_called_once()
        
        # Getting manager again should create a new instance
        new_manager = get_session_manager()
        assert new_manager is not manager