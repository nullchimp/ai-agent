"""
Unit tests for session database operations.
Tests save_session_state() and restore_session_state() functions.
"""

import pytest
from datetime import datetime, timezone
from typing import Dict, Any, List

from core.db.session import (
    create_db_session,
    get_session_by_id,
    save_session_state,
    restore_session_state,
    delete_session,
)


class TestSessionDBOperations:
    """Test suite for session database CRUD operations"""
    
    def test_save_session_state_creates_new_session(self):
        """Test that save_session_state creates a new session if it doesn't exist"""
        session_id = f"test-session-{datetime.now().timestamp()}"
        
        # Save state for non-existent session
        save_session_state(
            session_id=session_id,
            conversation_history=[
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi!"}
            ],
            enabled_tools=["google_search", "read_file"],
            disabled_tools=["write_file"],
            mcp_initialized=False,
            agent_config={"model": "gpt-4"}
        )
        
        # Verify session was created
        session = get_session_by_id(session_id)
        assert session is not None
        assert session.session_id == session_id
        assert len(session.conversation_history) == 2
        assert "google_search" in session.enabled_tools
        
        # Cleanup
        delete_session(session_id)
    
    def test_save_session_state_updates_existing_session(self):
        """Test that save_session_state updates an existing session"""
        session_id = f"test-session-{datetime.now().timestamp()}"
        
        # Create initial session
        create_db_session(
            session_id=session_id,
            conversation_history=[{"role": "user", "content": "First message"}],
            enabled_tools=["google_search"],
            disabled_tools=[],
            mcp_initialized=False
        )
        
        # Update session state
        save_session_state(
            session_id=session_id,
            conversation_history=[
                {"role": "user", "content": "First message"},
                {"role": "assistant", "content": "Response"},
                {"role": "user", "content": "Second message"}
            ],
            enabled_tools=["google_search", "read_file"],
            disabled_tools=["write_file"],
            mcp_initialized=True,
            agent_config={"model": "gpt-4-turbo"}
        )
        
        # Verify updates
        session = get_session_by_id(session_id)
        assert len(session.conversation_history) == 3
        assert session.mcp_initialized is True
        assert "read_file" in session.enabled_tools
        assert "write_file" in session.disabled_tools
        
        # Cleanup
        delete_session(session_id)
    
    def test_restore_session_state_returns_none_for_missing_session(self):
        """Test that restore_session_state returns None for non-existent session"""
        result = restore_session_state("non-existent-session-id")
        assert result is None
    
    def test_restore_session_state_returns_full_state(self):
        """Test that restore_session_state returns complete session state"""
        session_id = f"test-session-{datetime.now().timestamp()}"
        
        # Create session with full state
        conversation = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"}
        ]
        enabled = ["google_search", "read_file", "web_scraper"]
        disabled = ["write_file", "github_search"]
        config = {"model": "gpt-4", "temperature": 0.7}
        
        create_db_session(
            session_id=session_id,
            title="Test Session",
            conversation_history=conversation,
            enabled_tools=enabled,
            disabled_tools=disabled,
            mcp_initialized=True,
            agent_config=config
        )
        
        # Restore state
        restored = restore_session_state(session_id)
        
        assert restored is not None
        assert restored["session_id"] == session_id
        assert restored["title"] == "Test Session"
        assert len(restored["conversation_history"]) == 3
        assert restored["conversation_history"][0]["role"] == "user"
        assert restored["enabled_tools"] == enabled
        assert restored["disabled_tools"] == disabled
        assert restored["mcp_initialized"] is True
        assert restored["agent_config"]["model"] == "gpt-4"
        assert "last_activity" in restored
        assert "conversation_count" in restored
        
        # Cleanup
        delete_session(session_id)
    
    def test_session_state_persistence_across_updates(self):
        """Test that session state persists correctly across multiple updates"""
        session_id = f"test-session-{datetime.now().timestamp()}"
        
        # Initial state
        save_session_state(
            session_id=session_id,
            conversation_history=[{"role": "user", "content": "Message 1"}],
            enabled_tools=["tool1"],
            disabled_tools=[],
            mcp_initialized=False,
            agent_config={}
        )
        
        # Update 1
        save_session_state(
            session_id=session_id,
            conversation_history=[
                {"role": "user", "content": "Message 1"},
                {"role": "assistant", "content": "Response 1"}
            ],
            enabled_tools=["tool1", "tool2"],
            disabled_tools=[],
            mcp_initialized=False,
            agent_config={}
        )
        
        # Update 2
        save_session_state(
            session_id=session_id,
            conversation_history=[
                {"role": "user", "content": "Message 1"},
                {"role": "assistant", "content": "Response 1"},
                {"role": "user", "content": "Message 2"}
            ],
            enabled_tools=["tool1", "tool2"],
            disabled_tools=["tool3"],
            mcp_initialized=True,
            agent_config={"key": "value"}
        )
        
        # Verify final state
        restored = restore_session_state(session_id)
        assert len(restored["conversation_history"]) == 3
        assert restored["mcp_initialized"] is True
        assert "tool3" in restored["disabled_tools"]
        assert restored["agent_config"]["key"] == "value"
        
        # Cleanup
        delete_session(session_id)
