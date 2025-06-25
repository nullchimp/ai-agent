import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from core.debug_capture import (
    DebugCapture, DebugEvent, DebugEventType, 
    get_debug_capture_instance, delete_debug_capture_instance,
    get_all_debug_events, clear_all_debug_events, _debug_sessions
)

class TestDebugCapture:
    def setup_method(self):
        # Clear all debug sessions for each test
        _debug_sessions.clear()

    def test_debug_capture_per_session(self):
        capture1 = get_debug_capture_instance("session1")
        capture2 = get_debug_capture_instance("session1")
        capture3 = get_debug_capture_instance("session2")
        
        assert capture1 is capture2  # Same session should return same instance
        assert capture1 is not capture3  # Different sessions should be different instances
        assert capture1.session_id == "session1"
        assert capture3.session_id == "session2"

    def test_enable_disable_debug(self):
        capture = get_debug_capture_instance("test_session")
        assert not capture.is_enabled()
        
        capture.enable()
        assert capture.is_enabled()
        
        capture.disable()
        assert not capture.is_enabled()

    def test_capture_event_when_disabled(self):
        capture = get_debug_capture_instance("test_session")
        capture.disable()
        
        capture.capture_event(DebugEventType.TOOL_CALL, "test", {"key": "value"})
        
        events = capture.get_events()
        assert len(events) == 0

    def test_capture_event_when_enabled(self):
        capture = get_debug_capture_instance("test_session")
        capture.enable()
        
        capture.capture_event(DebugEventType.TOOL_CALL, "test", {"key": "value"})
        
        events = capture.get_events()
        assert len(events) == 1
        assert events[0]["event_type"] == DebugEventType.TOOL_CALL
        assert events[0]["message"] == "test"
        assert events[0]["data"]["key"] == "value"

    def test_session_id_tracking(self):
        capture1 = get_debug_capture_instance("session_1")
        capture2 = get_debug_capture_instance("session_2")
        
        capture1.enable()
        capture2.enable()
        
        capture1.capture_event(DebugEventType.TOOL_CALL, "test1", {})
        capture2.capture_event(DebugEventType.TOOL_RESULT, "test2", {})
        
        events1 = capture1.get_events()
        events2 = capture2.get_events()
        
        assert len(events1) == 1
        assert len(events2) == 1
        assert events1[0]["message"] == "test1"
        assert events1[0]["session_id"] == "session_1"
        assert events2[0]["message"] == "test2"
        assert events2[0]["session_id"] == "session_2"
        
        # Test global events gathering
        all_events = get_all_debug_events()
        assert len(all_events) == 2
        
        # Test filtering by session
        session1_events = get_all_debug_events("session_1")
        assert len(session1_events) == 1
        assert session1_events[0]["message"] == "test1"

    def test_clear_events(self):
        capture1 = get_debug_capture_instance("session_1")
        capture2 = get_debug_capture_instance("session_2")
        
        capture1.enable()
        capture2.enable()
        
        capture1.capture_event(DebugEventType.TOOL_CALL, "test1", {})
        capture2.capture_event(DebugEventType.TOOL_RESULT, "test2", {})
        
        # Clear specific session
        capture1.clear_events()
        events1 = capture1.get_events()
        events2 = capture2.get_events()
        assert len(events1) == 0
        assert len(events2) == 1
        assert events2[0]["message"] == "test2"
        
        # Test global clear
        capture1.capture_event(DebugEventType.TOOL_CALL, "test3", {})
        clear_all_debug_events()
        assert len(capture1.get_events()) == 0
        assert len(capture2.get_events()) == 0

    def test_max_events_limit(self):
        capture = get_debug_capture_instance("test_session")
        capture.enable()
        capture._max_events = 3  # Set low limit for testing
        
        for i in range(5):
            capture.capture_event(DebugEventType.TOOL_CALL, f"test{i}", {})
        
        events = capture.get_events()
        assert len(events) == 3
        # Should keep the latest events
        messages = [event["message"] for event in events]
        assert "test2" in messages
        assert "test3" in messages
        assert "test4" in messages
        assert "test0" not in messages
        assert "test1" not in messages

    def test_capture_llm_request(self):
        capture = get_debug_capture_instance("test_session")
        capture.enable()
        
        payload = {"messages": [{"role": "user", "content": "test"}]}
        capture.capture_llm_request(payload)
        
        events = capture.get_events()
        assert len(events) == 1
        assert events[0]["event_type"] == DebugEventType.AGENT_TO_MODEL
        assert events[0]["message"] == "LLM Request"
        
        # Check that the payload data is preserved (ignoring color metadata)
        captured_payload = events[0]["data"]["payload"]
        assert "messages" in captured_payload
        assert len(captured_payload["messages"]) == 1
        assert captured_payload["messages"][0]["role"] == "user"
        assert captured_payload["messages"][0]["content"] == "test"
        
        # Check that color metadata is present at the data root level with path-based keys
        captured_data = events[0]["data"]
        assert "_debug_colors" in captured_data
        assert "_payload_messages_color" in captured_data["_debug_colors"]
        assert "_payload_messages_role_color" in captured_data["_debug_colors"]
        assert "_payload_messages_content_color" in captured_data["_debug_colors"]

    def test_capture_tool_call(self):
        capture = get_debug_capture_instance("test_session")
        capture.enable()
        
        capture.capture_tool_call("google_search", {"query": "test"})
        
        events = capture.get_events()
        assert len(events) == 1
        assert events[0]["event_type"] == DebugEventType.TOOL_CALL
        assert events[0]["message"] == "Tool Call: google_search"
        assert events[0]["data"]["tool_name"] == "google_search"
        assert events[0]["data"]["arguments"]["query"] == "test"
        
        # Check that color metadata is present for tool_name
        assert "_debug_colors" in events[0]["data"]
        assert "_tool_name_color" in events[0]["data"]["_debug_colors"]

    def test_debug_event_to_dict(self):
        event = DebugEvent(
            DebugEventType.TOOL_RESULT,
            "Test message",
            "test_session",
            {"result": "success"},
            datetime(2023, 1, 1, 12, 0, 0)
        )
        
        event_dict = event.to_dict()
        assert event_dict["event_type"] == DebugEventType.TOOL_RESULT
        assert event_dict["message"] == "Test message"
        assert event_dict["data"]["result"] == "success"
        assert event_dict["timestamp"] == "2023-01-01T12:00:00"
        assert event_dict["session_id"] == "test_session"

    def test_delete_debug_capture_instance(self):
        capture = get_debug_capture_instance("test_session")
        capture.enable()
        capture.capture_event(DebugEventType.TOOL_CALL, "test", {})
        
        assert len(_debug_sessions) == 1
        assert delete_debug_capture_instance("test_session") == True
        assert len(_debug_sessions) == 0
        assert delete_debug_capture_instance("non_existent") == False
