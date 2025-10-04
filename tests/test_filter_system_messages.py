import pytest
from api.routes.session import filter_system_messages


class TestFilterSystemMessages:
    def test_filter_removes_system_messages(self):
        conversation_history = [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"},
            {"role": "assistant", "content": "I'm doing well!"}
        ]
        
        filtered = filter_system_messages(conversation_history)
        
        assert len(filtered) == 4
        assert all(msg.get("role") != "system" for msg in filtered)
        assert filtered[0]["role"] == "user"
        assert filtered[0]["content"] == "Hello"

    def test_filter_with_no_system_messages(self):
        conversation_history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
        
        filtered = filter_system_messages(conversation_history)
        
        assert len(filtered) == 2
        assert filtered == conversation_history

    def test_filter_with_only_system_messages(self):
        conversation_history = [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "system", "content": "Additional instructions"}
        ]
        
        filtered = filter_system_messages(conversation_history)
        
        assert len(filtered) == 0

    def test_filter_with_empty_history(self):
        conversation_history = []
        
        filtered = filter_system_messages(conversation_history)
        
        assert len(filtered) == 0
        assert filtered == []

    def test_filter_preserves_order(self):
        conversation_history = [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "First user message"},
            {"role": "assistant", "content": "First assistant response"},
            {"role": "user", "content": "Second user message"},
            {"role": "assistant", "content": "Second assistant response"}
        ]
        
        filtered = filter_system_messages(conversation_history)
        
        assert len(filtered) == 4
        assert filtered[0]["content"] == "First user message"
        assert filtered[1]["content"] == "First assistant response"
        assert filtered[2]["content"] == "Second user message"
        assert filtered[3]["content"] == "Second assistant response"
