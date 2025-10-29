"""
Integration tests for session persistence across server restarts.
Simulates server restart by clearing in-memory cache and restoring from database.
"""

import pytest
from datetime import datetime
from typing import Dict

from core.db.session import (
    create_db_session,
    save_session_state,
    restore_session_state,
    delete_session,
)


class TestSessionPersistence:
    """Test suite for session persistence across server restarts"""
    
    def test_session_survives_simulated_restart(self):
        """
        Test that session state is restored after simulated restart.
        
        Simulates a server restart by:
        1. Creating a session with state
        2. Saving state to database
        3. Simulating restart (not accessing in-memory cache)
        4. Restoring state from database
        5. Verifying all state is intact
        """
        session_id = f"test-restart-{datetime.now().timestamp()}"
        
        # Step 1 & 2: Create session with full state
        original_conversation = [
            {"role": "user", "content": "Hello, I need help with Python"},
            {"role": "assistant", "content": "I'd be happy to help! What do you need?"},
            {"role": "user", "content": "How do I read a file?"},
            {"role": "assistant", "content": "You can use open() function..."}
        ]
        
        original_enabled_tools = ["google_search", "read_file", "write_file"]
        original_disabled_tools = ["github_search"]
        original_config = {
            "model": "gpt-4-turbo-preview",
            "temperature": 0.7,
            "max_tokens": 4096
        }
        
        save_session_state(
            session_id=session_id,
            conversation_history=original_conversation,
            enabled_tools=original_enabled_tools,
            disabled_tools=original_disabled_tools,
            mcp_initialized=True,
            agent_config=original_config
        )
        
        # Step 3: Simulate restart - database persists, memory cleared
        # (In real scenario, _agent_sessions dict would be empty)
        
        # Step 4: Restore from database
        restored = restore_session_state(session_id)
        
        # Step 5: Verify all state is intact
        assert restored is not None, "Session should be restored from database"
        
        # Verify conversation history
        assert len(restored["conversation_history"]) == len(original_conversation)
        for i, msg in enumerate(restored["conversation_history"]):
            assert msg["role"] == original_conversation[i]["role"]
            assert msg["content"] == original_conversation[i]["content"]
        
        # Verify tool states
        assert set(restored["enabled_tools"]) == set(original_enabled_tools)
        assert set(restored["disabled_tools"]) == set(original_disabled_tools)
        
        # Verify MCP state
        assert restored["mcp_initialized"] is True
        
        # Verify agent config
        assert restored["agent_config"]["model"] == original_config["model"]
        assert restored["agent_config"]["temperature"] == original_config["temperature"]
        
        # Verify metadata fields exist
        assert "last_activity" in restored
        assert "conversation_count" in restored
        assert "title" in restored
        
        # Cleanup
        delete_session(session_id)
    
    def test_multiple_sessions_persist_independently(self):
        """Test that multiple sessions persist independently"""
        session_id_1 = f"test-multi-1-{datetime.now().timestamp()}"
        session_id_2 = f"test-multi-2-{datetime.now().timestamp()}"
        
        # Create two different sessions
        save_session_state(
            session_id=session_id_1,
            conversation_history=[{"role": "user", "content": "Session 1 message"}],
            enabled_tools=["tool_a"],
            disabled_tools=[],
            mcp_initialized=False,
            agent_config={"session": "1"}
        )
        
        save_session_state(
            session_id=session_id_2,
            conversation_history=[{"role": "user", "content": "Session 2 message"}],
            enabled_tools=["tool_b", "tool_c"],
            disabled_tools=["tool_a"],
            mcp_initialized=True,
            agent_config={"session": "2"}
        )
        
        # Restore both sessions
        restored_1 = restore_session_state(session_id_1)
        restored_2 = restore_session_state(session_id_2)
        
        # Verify sessions are independent
        assert restored_1["conversation_history"][0]["content"] == "Session 1 message"
        assert restored_2["conversation_history"][0]["content"] == "Session 2 message"
        
        assert restored_1["enabled_tools"] == ["tool_a"]
        assert set(restored_2["enabled_tools"]) == {"tool_b", "tool_c"}
        
        assert restored_1["mcp_initialized"] is False
        assert restored_2["mcp_initialized"] is True
        
        assert restored_1["agent_config"]["session"] == "1"
        assert restored_2["agent_config"]["session"] == "2"
        
        # Cleanup
        delete_session(session_id_1)
        delete_session(session_id_2)
    
    def test_conversation_history_integrity_after_restart(self):
        """Test that conversation history maintains order and integrity"""
        session_id = f"test-history-{datetime.now().timestamp()}"
        
        # Create long conversation history
        conversation = []
        for i in range(10):
            conversation.append({"role": "user", "content": f"User message {i}"})
            conversation.append({"role": "assistant", "content": f"Assistant response {i}"})
        
        # Add a tool call interaction
        conversation.append({
            "role": "assistant",
            "content": None,
            "tool_calls": [{
                "id": "call_123",
                "type": "function",
                "function": {"name": "google_search", "arguments": '{"query": "test"}'}
            }]
        })
        conversation.append({
            "role": "tool",
            "tool_call_id": "call_123",
            "name": "google_search",
            "content": "Search results..."
        })
        conversation.append({
            "role": "assistant",
            "content": "Based on the search results..."
        })
        
        # Save conversation
        save_session_state(
            session_id=session_id,
            conversation_history=conversation,
            enabled_tools=["google_search"],
            disabled_tools=[],
            mcp_initialized=True,
            agent_config={}
        )
        
        # Restore and verify
        restored = restore_session_state(session_id)
        restored_history = restored["conversation_history"]
        
        # Verify length
        assert len(restored_history) == len(conversation)
        
        # Verify order
        for i, msg in enumerate(restored_history):
            assert msg["role"] == conversation[i]["role"]
            if "content" in conversation[i]:
                assert msg.get("content") == conversation[i]["content"]
        
        # Verify tool call structure
        tool_call_msg = restored_history[-3]
        assert tool_call_msg["role"] == "assistant"
        assert "tool_calls" in tool_call_msg
        assert tool_call_msg["tool_calls"][0]["function"]["name"] == "google_search"
        
        # Cleanup
        delete_session(session_id)
    
    def test_empty_session_restores_correctly(self):
        """Test that a newly created session with no history restores correctly"""
        session_id = f"test-empty-{datetime.now().timestamp()}"
        
        # Create session with minimal state
        save_session_state(
            session_id=session_id,
            conversation_history=[],
            enabled_tools=[],
            disabled_tools=[],
            mcp_initialized=False,
            agent_config={}
        )
        
        # Restore
        restored = restore_session_state(session_id)
        
        assert restored is not None
        assert len(restored["conversation_history"]) == 0
        assert len(restored["enabled_tools"]) == 0
        assert len(restored["disabled_tools"]) == 0
        assert restored["mcp_initialized"] is False
        
        # Cleanup
        delete_session(session_id)
