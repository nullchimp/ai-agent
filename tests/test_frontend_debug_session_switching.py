import pytest
from unittest.mock import Mock, AsyncMock, patch, call
from core.debug_capture import get_debug_capture_instance, _debug_sessions
from api.routes import session_router, api_router
from fastapi.testclient import TestClient
from fastapi import FastAPI


class TestFrontendDebugSessionSwitching:
    """Test the frontend integration for debug session switching"""

    @pytest.fixture
    def app(self):
        app = FastAPI()
        app.include_router(session_router)
        app.include_router(api_router)
        return app

    @pytest.fixture
    def client(self, app):
        return TestClient(app)

    @pytest.fixture
    def mock_agent_deps(self):
        with patch("api.routes.get_agent_instance") as mock_get_agent, \
             patch("api.routes.get_debug_capture_instance") as mock_get_debug:
            mock_agent = Mock()
            mock_agent.get_tools.return_value = []
            mock_agent.process_query = AsyncMock(return_value=("Test response", set()))
            mock_agent.initialize_mcp_tools = AsyncMock()
            mock_get_agent.return_value = mock_agent
            
            mock_debug = Mock()
            mock_get_debug.return_value = mock_debug
            yield mock_agent

    @pytest.fixture
    def mock_session_manager(self):
        # No longer needed since route doesn't use MCPSessionManager
        yield None

    def test_debug_panel_shows_session_specific_events(self, client, mock_agent_deps, mock_session_manager):
        """Test that the debug panel shows only events for the current session"""
        
        # Create two sessions with different debug events
        response1 = client.get("/api/session/new")
        session1_id = response1.json()["session_id"]
        
        response2 = client.get("/api/session/new")
        session2_id = response2.json()["session_id"]
        
        # Add different events to each session
        debug1 = get_debug_capture_instance(session1_id)
        debug2 = get_debug_capture_instance(session2_id)
        
        # Enable debug for both sessions before adding events
        debug1.enable()
        debug2.enable()
        
        debug1.capture_event("user_message", "User asks about weather", {"query": "What's the weather?"})
        debug1.capture_event("llm_response", "AI responds about weather", {"response": "It's sunny today"})
        
        debug2.capture_event("user_message", "User asks about news", {"query": "Latest news?"})
        debug2.capture_event("tool_call", "News search initiated", {"tool": "google_search", "query": "latest news"})
        debug2.capture_event("tool_result", "News results retrieved", {"results": ["News item 1", "News item 2"]})
        
        # Test: Debug endpoint for session 1 should only show session 1 events
        debug_response1 = client.get(f"/api/{session1_id}/debug", headers={"X-API-Key": "test_12345"})
        events1 = debug_response1.json()["events"]
        
        assert len(events1) == 2
        assert all(event["session_id"] == session1_id for event in events1)
        assert events1[0]["event_type"] == "user_message"
        assert events1[1]["event_type"] == "llm_response"
        
        # Test: Debug endpoint for session 2 should only show session 2 events
        debug_response2 = client.get(f"/api/{session2_id}/debug", headers={"X-API-Key": "test_12345"})
        events2 = debug_response2.json()["events"]
        
        assert len(events2) == 3
        assert all(event["session_id"] == session2_id for event in events2)
        assert events2[0]["event_type"] == "user_message"
        assert events2[1]["event_type"] == "tool_call"
        assert events2[2]["event_type"] == "tool_result"

    def test_debug_state_persists_across_session_switches(self, client, mock_agent_deps, mock_session_manager):
        """Test that debug enabled/disabled state is maintained per session"""
        
        # Create two sessions
        response1 = client.get("/api/session/new")
        session1_id = response1.json()["session_id"]
        
        response2 = client.get("/api/session/new")
        session2_id = response2.json()["session_id"]
        
        # Both start disabled by default, enable them first
        debug1 = get_debug_capture_instance(session1_id)
        debug2 = get_debug_capture_instance(session2_id)
        
        debug1.enable()
        debug2.enable()
        
        debug_status1 = client.get(f"/api/{session1_id}/debug", headers={"X-API-Key": "test_12345"})
        debug_status2 = client.get(f"/api/{session2_id}/debug", headers={"X-API-Key": "test_12345"})
        
        assert debug_status1.json()["enabled"] is True
        assert debug_status2.json()["enabled"] is True
        
        # Disable debug for session 1
        toggle_response = client.post(
            f"/api/{session1_id}/debug/toggle", 
            json={"enabled": False},
            headers={"X-API-Key": "test_12345"}
        )
        assert toggle_response.json()["enabled"] is False
        
        # Verify session 1 is disabled, session 2 still enabled
        debug_status1_after = client.get(f"/api/{session1_id}/debug", headers={"X-API-Key": "test_12345"})
        debug_status2_after = client.get(f"/api/{session2_id}/debug", headers={"X-API-Key": "test_12345"})
        
        assert debug_status1_after.json()["enabled"] is False
        assert debug_status2_after.json()["enabled"] is True
        
        # Add events to both sessions
        debug1 = get_debug_capture_instance(session1_id)
        debug2 = get_debug_capture_instance(session2_id)
        
        debug1.capture_event("test_event", "Should not be captured", {"test": "data1"})
        debug2.capture_event("test_event", "Should be captured", {"test": "data2"})
        
        # Verify only session 2 captures events (since session 1 is disabled, session 2 still enabled)
        events1 = client.get(f"/api/{session1_id}/debug", headers={"X-API-Key": "test_12345"}).json()["events"]
        events2 = client.get(f"/api/{session2_id}/debug", headers={"X-API-Key": "test_12345"}).json()["events"]
        
        assert len(events1) == 0  # Session 1 debug is disabled
        assert len(events2) == 1  # Session 2 debug is enabled

    def test_empty_session_shows_empty_debug_panel(self, client, mock_agent_deps, mock_session_manager):
        """Test that a new session with no events shows an empty debug panel"""
        
        # Create a new session
        response = client.get("/api/session/new")
        session_id = response.json()["session_id"]
        
        # Debug endpoint should return enabled=False but no events by default
        debug_response = client.get(f"/api/{session_id}/debug", headers={"X-API-Key": "test_12345"})
        debug_data = debug_response.json()
        
        assert debug_data["enabled"] is False
        assert len(debug_data["events"]) == 0

    def test_debug_events_ordering_by_timestamp(self, client, mock_agent_deps, mock_session_manager):
        """Test that debug events are returned in chronological order"""
        
        # Create a session
        response = client.get("/api/session/new")
        session_id = response.json()["session_id"]
        
        debug_capture = get_debug_capture_instance(session_id)
        
        # Enable debug before adding events
        debug_capture.enable()
        
        # Add events in a specific order
        import time
        debug_capture.capture_event("event_1", "First event", {"order": 1})
        time.sleep(0.01)  # Small delay to ensure different timestamps
        debug_capture.capture_event("event_2", "Second event", {"order": 2})
        time.sleep(0.01)
        debug_capture.capture_event("event_3", "Third event", {"order": 3})
        
        # Get events from API
        debug_response = client.get(f"/api/{session_id}/debug", headers={"X-API-Key": "test_12345"})
        events = debug_response.json()["events"]
        
        assert len(events) == 3
        # Events should be in chronological order
        assert events[0]["event_type"] == "event_1"
        assert events[1]["event_type"] == "event_2"
        assert events[2]["event_type"] == "event_3"
        
        # Timestamps should be in ascending order
        timestamps = [event["timestamp"] for event in events]
        assert timestamps == sorted(timestamps)
