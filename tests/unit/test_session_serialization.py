"""
Unit tests for session JSON serialization and deserialization (T085).
Tests conversation_history and agent_config JSON handling.
"""

import pytest
import json
from datetime import datetime, timezone
from src.core.db.schemas.session import Session


def test_session_basic_serialization():
    """Test that a session serializes to valid JSON."""
    session = Session(
        session_id="test-session-123",
        user_id="user-456",
        title="Test Session",
        conversation_count=5,
        last_activity=datetime.now(timezone.utc),
        is_active=True,
        conversation_history=[],
        agent_config={}
    )
    
    # Serialize to JSON
    session_dict = session.to_dict()
    json_str = json.dumps(session_dict)
    
    # Should be valid JSON
    assert json_str is not None
    assert isinstance(json_str, str)
    
    # Deserialize back
    parsed = json.loads(json_str)
    assert parsed["session_id"] == "test-session-123"
    assert parsed["user_id"] == "user-456"


def test_conversation_history_serialization():
    """Test that conversation_history with complex messages serializes correctly."""
    conversation_history = [
        {
            "role": "user",
            "content": "Hello, how are you?",
            "timestamp": "2024-01-15T10:30:00Z"
        },
        {
            "role": "assistant",
            "content": "I'm doing well, thank you!",
            "timestamp": "2024-01-15T10:30:05Z",
            "metadata": {
                "model": "gpt-4",
                "tokens": 15
            }
        },
        {
            "role": "user",
            "content": "Can you help me with Python?",
            "timestamp": "2024-01-15T10:31:00Z"
        }
    ]
    
    session = Session(
        session_id="test-conv-session",
        user_id="user-789",
        title="Python Help",
        conversation_count=3,
        last_activity=datetime.now(timezone.utc),
        is_active=True,
        conversation_history=conversation_history,
        agent_config={}
    )
    
    # Serialize
    session_dict = session.to_dict()
    json_str = json.dumps(session_dict)
    
    # Deserialize
    parsed = json.loads(json_str)
    
    # Verify conversation history preserved
    assert len(parsed["conversation_history"]) == 3
    assert parsed["conversation_history"][0]["role"] == "user"
    assert parsed["conversation_history"][1]["role"] == "assistant"
    assert parsed["conversation_history"][1]["metadata"]["model"] == "gpt-4"
    assert parsed["conversation_history"][1]["metadata"]["tokens"] == 15


def test_agent_config_serialization():
    """Test that agent_config with nested objects serializes correctly."""
    agent_config = {
        "model": "gpt-4-turbo",
        "temperature": 0.7,
        "max_tokens": 2000,
        "tools": [
            {"name": "web_search", "enabled": True},
            {"name": "file_read", "enabled": False}
        ],
        "system_prompt": "You are a helpful assistant.",
        "preferences": {
            "language": "en",
            "verbosity": "detailed",
            "code_style": {
                "indent": 4,
                "quotes": "double"
            }
        }
    }
    
    session = Session(
        session_id="test-config-session",
        user_id="user-999",
        title="Config Test",
        conversation_count=0,
        last_activity=datetime.now(timezone.utc),
        is_active=True,
        conversation_history=[],
        agent_config=agent_config
    )
    
    # Serialize
    session_dict = session.to_dict()
    json_str = json.dumps(session_dict)
    
    # Deserialize
    parsed = json.loads(json_str)
    
    # Verify agent_config preserved
    assert parsed["agent_config"]["model"] == "gpt-4-turbo"
    assert parsed["agent_config"]["temperature"] == 0.7
    assert parsed["agent_config"]["max_tokens"] == 2000
    assert len(parsed["agent_config"]["tools"]) == 2
    assert parsed["agent_config"]["tools"][0]["name"] == "web_search"
    assert parsed["agent_config"]["tools"][0]["enabled"] is True
    assert parsed["agent_config"]["preferences"]["code_style"]["indent"] == 4
    assert parsed["agent_config"]["preferences"]["code_style"]["quotes"] == "double"


def test_empty_fields_serialization():
    """Test that empty conversation_history and agent_config serialize correctly."""
    session = Session(
        session_id="test-empty-session",
        user_id="user-empty",
        title="Empty Session",
        conversation_count=0,
        last_activity=datetime.now(timezone.utc),
        is_active=True,
        conversation_history=[],
        agent_config={}
    )
    
    session_dict = session.to_dict()
    json_str = json.dumps(session_dict)
    parsed = json.loads(json_str)
    
    # Verify empty fields are valid
    assert parsed["conversation_history"] == []
    assert parsed["agent_config"] == {}


def test_special_characters_in_content():
    """Test that special characters in messages are properly escaped."""
    conversation_history = [
        {
            "role": "user",
            "content": 'String with "quotes" and \'apostrophes\' and\nnewlines\tand\ttabs',
            "timestamp": "2024-01-15T10:30:00Z"
        },
        {
            "role": "assistant",
            "content": "Here's some JSON: {\"key\": \"value\", \"nested\": {\"array\": [1, 2, 3]}}",
            "timestamp": "2024-01-15T10:30:05Z"
        }
    ]
    
    session = Session(
        session_id="test-special-chars",
        user_id="user-special",
        title="Special Characters",
        conversation_count=2,
        last_activity=datetime.now(timezone.utc),
        is_active=True,
        conversation_history=conversation_history,
        agent_config={}
    )
    
    # Serialize and deserialize
    session_dict = session.to_dict()
    json_str = json.dumps(session_dict)
    parsed = json.loads(json_str)
    
    # Verify special characters preserved
    assert "\"quotes\"" in parsed["conversation_history"][0]["content"]
    assert "newlines" in parsed["conversation_history"][0]["content"]
    assert "{\"key\":" in parsed["conversation_history"][1]["content"]


def test_large_conversation_serialization():
    """Test serialization of a session with many messages."""
    conversation_history = [
        {
            "role": "user" if i % 2 == 0 else "assistant",
            "content": f"Message number {i} with some content",
            "timestamp": f"2024-01-15T10:{i:02d}:00Z"
        }
        for i in range(100)
    ]
    
    session = Session(
        session_id="test-large-session",
        user_id="user-large",
        title="Large Conversation",
        conversation_count=100,
        last_activity=datetime.now(timezone.utc),
        is_active=True,
        conversation_history=conversation_history,
        agent_config={}
    )
    
    # Serialize
    session_dict = session.to_dict()
    json_str = json.dumps(session_dict)
    
    # Should not raise any errors
    assert json_str is not None
    
    # Deserialize and verify
    parsed = json.loads(json_str)
    assert len(parsed["conversation_history"]) == 100
    assert parsed["conversation_history"][0]["content"] == "Message number 0 with some content"
    assert parsed["conversation_history"][99]["content"] == "Message number 99 with some content"


def test_unicode_characters_serialization():
    """Test that Unicode characters (emojis, non-ASCII) serialize correctly."""
    conversation_history = [
        {
            "role": "user",
            "content": "Hello! 👋 こんにちは 你好 مرحبا",
            "timestamp": "2024-01-15T10:30:00Z"
        },
        {
            "role": "assistant",
            "content": "I can help with multiple languages! 🌍✨",
            "timestamp": "2024-01-15T10:30:05Z"
        }
    ]
    
    session = Session(
        session_id="test-unicode-session",
        user_id="user-unicode",
        title="Unicode Test 🔥",
        conversation_count=2,
        last_activity=datetime.now(timezone.utc),
        is_active=True,
        conversation_history=conversation_history,
        agent_config={"language": "multi"}
    )
    
    # Serialize
    session_dict = session.to_dict()
    json_str = json.dumps(session_dict, ensure_ascii=False)
    
    # Deserialize
    parsed = json.loads(json_str)
    
    # Verify Unicode preserved
    assert "👋" in parsed["conversation_history"][0]["content"]
    assert "こんにちは" in parsed["conversation_history"][0]["content"]
    assert "🌍" in parsed["conversation_history"][1]["content"]
    assert "🔥" in parsed["title"]


def test_null_values_handling():
    """Test that None/null values in optional fields are handled correctly."""
    conversation_history = [
        {
            "role": "user",
            "content": "Test message",
            "timestamp": "2024-01-15T10:30:00Z",
            "metadata": None  # Explicitly None
        }
    ]
    
    session = Session(
        session_id="test-null-session",
        user_id="user-null",
        title="Null Test",
        conversation_count=1,
        last_activity=datetime.now(timezone.utc),
        is_active=True,
        conversation_history=conversation_history,
        agent_config={}
    )
    
    # Serialize
    session_dict = session.to_dict()
    json_str = json.dumps(session_dict)
    
    # Deserialize
    parsed = json.loads(json_str)
    
    # Verify null handling
    assert parsed["conversation_history"][0]["metadata"] is None
