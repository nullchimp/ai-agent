import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

from core.db.schemas.session_objects import Session
from core.db.session import (
    create_session,
    get_session_by_id,
    save_session_state,
    restore_session_state,
    update_session
)

class TestSessionSchema:
    def test_session_initialization(self):
        session = Session(
            title="Test Session",
            session_id="test-123"
        )
        
        assert session.title == "Test Session"
        assert session.session_id == "test-123"
        assert session.is_active is True
        assert session.conversation_history == []
        assert session.enabled_tools == []
        assert session.disabled_tools == []
        assert session.mcp_initialized is False
        assert session.agent_config == {}
    
    def test_session_update_conversation_history(self):
        session = Session(session_id="test-123")
        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
        
        session.update_conversation_history(history)
        
        assert session.conversation_history == history
        assert session.updated_at is not None
    
    def test_session_update_tool_states(self):
        session = Session(session_id="test-123")
        enabled = ["tool1", "tool2"]
        disabled = ["tool3"]
        
        session.update_tool_states(enabled, disabled)
        
        assert session.enabled_tools == enabled
        assert session.disabled_tools == disabled
    
    def test_session_set_mcp_initialized(self):
        session = Session(session_id="test-123")
        
        session.set_mcp_initialized(True)
        
        assert session.mcp_initialized is True
    
    def test_session_update_agent_config(self):
        session = Session(session_id="test-123")
        config = {"model": "gpt-4", "temperature": 0.7}
        
        session.update_agent_config(config)
        
        assert session.agent_config == config


class TestSessionRepository:
    @patch('core.db.session.get_connection_pool')
    def test_create_session(self, mock_pool):
        mock_db = MagicMock()
        mock_pool.return_value.get_connection.return_value.__enter__.return_value = mock_db
        
        session = create_session(session_id="test-456", title="New Session")
        
        assert session.session_id == "test-456"
        assert session.title == "New Session"
        mock_db._execute.assert_called_once()
    
    @patch('core.db.session.get_by_property')
    def test_get_session_by_id_found(self, mock_get):
        mock_get.return_value = {
            "session_id": "test-789",
            "title": "Existing Session",
            "is_active": True,
            "conversation_history": [],
            "enabled_tools": ["tool1"],
            "disabled_tools": [],
            "mcp_initialized": False,
            "agent_config": {},
            "conversation_count": 0,
            "last_activity": datetime.now(timezone.utc).isoformat(),
            "id": "uuid-123",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "metadata": {}
        }
        
        session = get_session_by_id("test-789")
        
        assert session is not None
        assert session.session_id == "test-789"
        assert session.title == "Existing Session"
    
    @patch('core.db.session.get_by_property')
    def test_get_session_by_id_not_found(self, mock_get):
        mock_get.return_value = None
        
        session = get_session_by_id("nonexistent")
        
        assert session is None
    
    @patch('core.db.session.get_connection_pool')
    @patch('core.db.session.get_session_by_id')
    def test_save_session_state_new(self, mock_get, mock_pool):
        mock_get.return_value = None
        mock_db = MagicMock()
        mock_pool.return_value.get_connection.return_value.__enter__.return_value = mock_db
        
        save_session_state(
            session_id="new-session",
            conversation_history=[{"role": "user", "content": "test"}],
            enabled_tools=["tool1"],
            disabled_tools=["tool2"],
            mcp_initialized=True,
            agent_config={"test": "config"}
        )
        
        assert mock_db._execute.call_count >= 1
    
    @patch('core.db.session.get_session_by_id')
    @patch('core.db.session.update_session')
    def test_restore_session_state(self, mock_update, mock_get):
        mock_session = Session(
            session_id="test-restore",
            title="Restore Test",
            conversation_history=[{"role": "user", "content": "test"}],
            enabled_tools=["tool1"],
            disabled_tools=[],
            mcp_initialized=True,
            agent_config={"key": "value"}
        )
        mock_get.return_value = mock_session
        
        state = restore_session_state("test-restore")
        
        assert state is not None
        assert state["session_id"] == "test-restore"
        assert state["title"] == "Restore Test"
        assert len(state["conversation_history"]) == 1
        assert state["enabled_tools"] == ["tool1"]
        assert state["mcp_initialized"] is True


class TestSessionIntegration:
    @patch('core.db.session.get_connection_pool')
    @patch('core.db.session.get_session_by_id')
    def test_full_session_lifecycle(self, mock_get, mock_pool):
        mock_db = MagicMock()
        mock_pool.return_value.get_connection.return_value.__enter__.return_value = mock_db
        mock_get.return_value = None
        
        session_id = "lifecycle-test"
        
        save_session_state(
            session_id=session_id,
            conversation_history=[
                {"role": "user", "content": "Question 1"},
                {"role": "assistant", "content": "Answer 1"}
            ],
            enabled_tools=["GoogleSearch", "WebScraper"],
            disabled_tools=["ReadFile"],
            mcp_initialized=True,
            agent_config={"model": "gpt-4"}
        )
        
        mock_session = Session(
            session_id=session_id,
            conversation_history=[
                {"role": "user", "content": "Question 1"},
                {"role": "assistant", "content": "Answer 1"}
            ],
            enabled_tools=["GoogleSearch", "WebScraper"],
            disabled_tools=["ReadFile"],
            mcp_initialized=True,
            agent_config={"model": "gpt-4"}
        )
        mock_get.return_value = mock_session
        
        restored = restore_session_state(session_id)
        
        assert restored is not None
        assert len(restored["conversation_history"]) == 2
        assert "GoogleSearch" in restored["enabled_tools"]
        assert "ReadFile" in restored["disabled_tools"]
        assert restored["mcp_initialized"] is True
