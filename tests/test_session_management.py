import pytest
from unittest.mock import Mock, AsyncMock, patch
import uuid
from datetime import datetime, timezone

from db.schemas import User, Session
from db.session_manager import SessionManager


class TestSessionManager:
    def setup_method(self):
        self.mock_db_client = Mock()
        self.mock_db_client.connect = Mock()
        self.mock_db_client.close = Mock()
        self.mock_db_client._execute = Mock()
        
        self.session_manager = SessionManager(self.mock_db_client)

    def test_session_manager_initialization(self):
        assert self.session_manager.database == self.mock_db_client
        assert isinstance(self.session_manager._hardcoded_user, User)
        assert self.session_manager._hardcoded_user.username == "default_user"

    @pytest.mark.asyncio
    async def test_initialize_default_user(self):
        self.mock_db_client._cur = Mock()
        
        user_id = await self.session_manager.initialize_default_user()
        
        assert user_id == str(self.session_manager._hardcoded_user.id)
        self.mock_db_client.connect.assert_called_once()
        self.mock_db_client._execute.assert_called_once()
        self.mock_db_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_user_session(self):
        self.mock_db_client._cur = Mock()
        
        session = await self.session_manager.create_user_session(
            title="Test Session",
            agent_config={"test": "config"}
        )
        
        assert isinstance(session, Session)
        assert session.title == "Test Session"
        assert session.agent_config == {"test": "config"}
        assert session.is_active is True
        
        # Should connect, execute create, execute link, then close
        self.mock_db_client.connect.assert_called_once()
        assert self.mock_db_client._execute.call_count == 2  # create + link
        self.mock_db_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_session_found(self):
        mock_session_data = {
            "id": str(uuid.uuid4()),
            "user_id": str(self.session_manager._hardcoded_user.id),
            "title": "Test Session",
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "last_activity": datetime.now(timezone.utc).isoformat(),
            "agent_config": {},
            "metadata": {}
        }
        
        mock_result = Mock()
        mock_result.properties = mock_session_data
        
        self.mock_db_client._cur = Mock()
        self.mock_db_client._cur.fetchone.return_value = [mock_result]
        
        session = await self.session_manager.get_session(mock_session_data["id"])
        
        assert isinstance(session, Session)
        assert str(session.id) == mock_session_data["id"]
        assert session.title == "Test Session"

    @pytest.mark.asyncio
    async def test_get_session_not_found(self):
        self.mock_db_client._cur = Mock()
        self.mock_db_client._cur.fetchone.return_value = None
        
        session = await self.session_manager.get_session("nonexistent-id")
        
        assert session is None

    @pytest.mark.asyncio
    async def test_delete_session_success(self):
        self.mock_db_client._cur = Mock()
        self.mock_db_client._cur.fetchone.return_value = [1]  # deleted_count = 1
        
        result = await self.session_manager.delete_session("test-session-id")
        
        assert result is True
        self.mock_db_client.connect.assert_called_once()
        self.mock_db_client._execute.assert_called_once()
        self.mock_db_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_session_not_found(self):
        self.mock_db_client._cur = Mock()
        self.mock_db_client._cur.fetchone.return_value = [0]  # deleted_count = 0
        
        result = await self.session_manager.delete_session("nonexistent-id")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_update_session_activity(self):
        self.mock_db_client._cur = Mock()
        self.mock_db_client._cur.fetchone.return_value = [Mock()]  # session found
        
        result = await self.session_manager.update_session_activity("test-session-id")
        
        assert result is True
        self.mock_db_client.connect.assert_called_once()
        self.mock_db_client._execute.assert_called_once()
        self.mock_db_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_user_sessions(self):
        mock_session_data = [
            {
                "id": str(uuid.uuid4()),
                "user_id": str(self.session_manager._hardcoded_user.id),
                "title": "Session 1",
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "last_activity": datetime.now(timezone.utc).isoformat(),
                "agent_config": {},
                "metadata": {}
            },
            {
                "id": str(uuid.uuid4()),
                "user_id": str(self.session_manager._hardcoded_user.id),
                "title": "Session 2",
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "last_activity": datetime.now(timezone.utc).isoformat(),
                "agent_config": {},
                "metadata": {}
            }
        ]
        
        mock_results = []
        for data in mock_session_data:
            mock_result = Mock()
            mock_result.properties = data
            mock_results.append([mock_result])
        
        self.mock_db_client._cur = Mock()
        self.mock_db_client._cur.fetchall.return_value = mock_results
        
        sessions = await self.session_manager.list_user_sessions()
        
        assert len(sessions) == 2
        assert all(isinstance(session, Session) for session in sessions)
        assert sessions[0].title == "Session 1"
        assert sessions[1].title == "Session 2"


class TestSessionIntegration:
    @pytest.mark.asyncio
    async def test_session_json_serialization(self):
        user = User("test_user", "test@example.com")
        session = Session(
            user_id=str(user.id),
            title="Test Session",
            agent_config={"tool1": {"enabled": True}},
            is_active=True
        )
        
        # Test serialization
        json_data = session.to_json()
        assert isinstance(json_data, str)
        
        # Test deserialization
        session2 = Session.from_json(json_data)
        assert str(session2.id) == str(session.id)
        assert session2.title == session.title
        assert session2.agent_config == session.agent_config
        assert session2.is_active == session.is_active

    def test_user_creation(self):
        user = User("testuser", "test@example.com", "Test User")
        
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.display_name == "Test User"
        assert isinstance(user.id, uuid.UUID)
        assert user.created_at is not None
        assert user.updated_at is not None