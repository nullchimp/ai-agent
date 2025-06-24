import pytest
from src.core.debug_capture import get_debug_capture_instance, _debug_sessions


class TestDebugCaptureBasic:
    """Basic tests to understand debug capture behavior"""

    def test_debug_capture_instance_reuse(self):
        """Test that get_debug_capture_instance returns the same instance for same session_id"""
        
        # Clear any existing sessions
        _debug_sessions.clear()
        
        session_id = "test_session_123"
        
        # First call creates instance
        instance1 = get_debug_capture_instance(session_id)
        assert not instance1.is_enabled()  # Should start disabled
        
        # Enable it
        instance1.enable()
        assert instance1.is_enabled()
        
        # Second call should return same instance
        instance2 = get_debug_capture_instance(session_id)
        assert instance1 is instance2  # Same object reference
        assert instance2.is_enabled()  # Should still be enabled

    def test_debug_capture_events_persistence(self):
        """Test that events persist in the same instance"""
        
        # Clear any existing sessions
        _debug_sessions.clear()
        
        session_id = "test_session_456"
        
        # Get instance and enable
        instance = get_debug_capture_instance(session_id)
        instance.enable()
        
        # Add event
        instance.capture_event("test_event", "Test message", {"test": "data"})
        events = instance.get_events()
        assert len(events) == 1
        
        # Get instance again - should have same events
        instance2 = get_debug_capture_instance(session_id)
        events2 = instance2.get_events()
        assert len(events2) == 1
        assert events2[0]["event_type"] == "test_event"

    def test_different_sessions_isolated(self):
        """Test that different session IDs have isolated debug captures"""
        
        # Clear any existing sessions
        _debug_sessions.clear()
        
        session1 = "session_1"
        session2 = "session_2"
        
        # Get instances
        instance1 = get_debug_capture_instance(session1)
        instance2 = get_debug_capture_instance(session2)
        
        # Enable both
        instance1.enable()
        instance2.enable()
        
        # Add different events
        instance1.capture_event("event_1", "Message 1", {"data": 1})
        instance2.capture_event("event_2", "Message 2", {"data": 2})
        
        # Verify isolation
        events1 = instance1.get_events()
        events2 = instance2.get_events()
        
        assert len(events1) == 1
        assert len(events2) == 1
        assert events1[0]["event_type"] == "event_1"
        assert events2[0]["event_type"] == "event_2"
