import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from core.debug_capture import DebugCapture, DebugEvent, DebugEventType

class TestDebugCapture:
    def setup_method(self):
        # Reset the singleton instance for each test
        DebugCapture._instance = None
        DebugCapture._session_id = None

    def test_debug_capture_singleton(self):
        capture1 = DebugCapture()
        capture2 = DebugCapture()
        assert capture1 is capture2

    def test_enable_disable_debug(self):
        capture = DebugCapture()
        assert not capture.is_enabled()
        
        capture.enable()
        assert capture.is_enabled()
        
        capture.disable()
        assert not capture.is_enabled()

    def test_capture_event_when_disabled(self):
        capture = DebugCapture()
        capture.disable()
        
        capture.capture_event(DebugEventType.TOOL_CALL, "test", {"key": "value"})
        
        events = capture.get_events()
        assert len(events) == 0

    def test_capture_event_when_enabled(self):
        capture = DebugCapture()
        capture.enable()
        
        capture.capture_event(DebugEventType.TOOL_CALL, "test", {"key": "value"})
        
        events = capture.get_events()
        assert len(events) == 1
        assert events[0]["event_type"] == DebugEventType.TOOL_CALL
        assert events[0]["message"] == "test"
        assert events[0]["data"]["key"] == "value"

    def test_session_id_tracking(self):
        capture = DebugCapture()
        capture.enable()
        
        capture.set_session_id("session_1")
        capture.capture_event(DebugEventType.TOOL_CALL, "test1", {})
        
        capture.set_session_id("session_2")
        capture.capture_event(DebugEventType.TOOL_RESULT, "test2", {})
        
        all_events = capture.get_events()
        assert len(all_events) == 2
        
        session1_events = capture.get_events("session_1")
        assert len(session1_events) == 1
        assert session1_events[0]["message"] == "test1"
        
        session2_events = capture.get_events("session_2")
        assert len(session2_events) == 1
        assert session2_events[0]["message"] == "test2"

    def test_clear_events(self):
        capture = DebugCapture()
        capture.enable()
        
        capture.set_session_id("session_1")
        capture.capture_event(DebugEventType.TOOL_CALL, "test1", {})
        
        capture.set_session_id("session_2")
        capture.capture_event(DebugEventType.TOOL_RESULT, "test2", {})
        
        # Clear specific session
        capture.clear_events("session_1")
        events = capture.get_events()
        assert len(events) == 1
        assert events[0]["message"] == "test2"
        
        # Clear all events
        capture.clear_events()
        events = capture.get_events()
        assert len(events) == 0

    def test_max_events_limit(self):
        capture = DebugCapture()
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
        capture = DebugCapture()
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
        
        # Check that color metadata is present
        assert "_debug_colors" in captured_payload
        assert "_messages_color" in captured_payload["_debug_colors"]

    def test_capture_tool_call(self):
        capture = DebugCapture()
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
        with patch('core.debug_capture.DebugCapture.get_current_session_id', return_value="test_session"):
            event = DebugEvent(
                DebugEventType.TOOL_RESULT,
                "Test message",
                {"result": "success"},
                datetime(2023, 1, 1, 12, 0, 0)
            )
            
            event_dict = event.to_dict()
            assert event_dict["event_type"] == DebugEventType.TOOL_RESULT
            assert event_dict["message"] == "Test message"
            assert event_dict["data"]["result"] == "success"
            assert event_dict["timestamp"] == "2023-01-01T12:00:00"
            assert event_dict["session_id"] == "test_session"
