import pytest
from unittest.mock import Mock, patch, AsyncMock
from core.debug_capture import DebugCapture, get_debug_capture_instance, _debug_sessions
from api.routes import session_router, api_router
from fastapi.testclient import TestClient
from fastapi import FastAPI


class TestDebugSessionIsolation:
    """Test that debug events are properly isolated per session in the frontend-backend integration"""

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
        with patch("api.routes.get_agent_instance") as mock_get_agent:
            mock_agent = Mock()
            mock_agent.get_tools.return_value = []
            mock_agent.process_query = AsyncMock(return_value=("Test response", set()))
            mock_get_agent.return_value = mock_agent
            yield mock_agent

    @pytest.fixture
    def mock_session_manager(self):
        with patch("api.routes.MCPSessionManager") as mock_mgr:
            mock_instance = Mock()
            mock_instance.discovery = AsyncMock()
            mock_instance.tools = []
            mock_mgr.return_value = mock_instance
            yield mock_instance

    def test_debug_events_isolated_per_session(self, client, mock_agent_deps, mock_session_manager):
        """Test that debug events are properly isolated between different sessions"""
        
        # Create two sessions
        response1 = client.post("/api/session/new")
        assert response1.status_code == 200
        session1_id = response1.json()["session_id"]
        
        response2 = client.post("/api/session/new")
        assert response2.status_code == 200
        session2_id = response2.json()["session_id"]
        
        # Get debug capture instances for both sessions
        debug1 = get_debug_capture_instance(session1_id)
        debug2 = get_debug_capture_instance(session2_id)
        
        # Both should be enabled after session creation
        assert debug1.is_enabled(), "Session 1 debug should be enabled after creation"
        assert debug2.is_enabled(), "Session 2 debug should be enabled after creation"
        
        # Add different debug events to each session
        debug1.capture_event("test_event_1", "Session 1 event", {"session": 1, "data": "session1_data"})
        debug2.capture_event("test_event_2", "Session 2 event", {"session": 2, "data": "session2_data"})
        
        # Verify session 1 debug endpoint only returns session 1 events
        debug_response1 = client.get(f"/api/{session1_id}/debug", headers={"X-API-Key": "test_12345"})
        assert debug_response1.status_code == 200
        events1 = debug_response1.json()["events"]
        
        # Should have exactly 1 event for session 1
        assert len(events1) == 1
        assert events1[0]["event_type"] == "test_event_1"
        assert events1[0]["message"] == "Session 1 event"
        assert events1[0]["data"]["session"] == 1
        assert events1[0]["session_id"] == session1_id
        
        # Verify session 2 debug endpoint only returns session 2 events
        debug_response2 = client.get(f"/api/{session2_id}/debug", headers={"X-API-Key": "test_12345"})
        assert debug_response2.status_code == 200
        events2 = debug_response2.json()["events"]
        
        # Should have exactly 1 event for session 2
        assert len(events2) == 1
        assert events2[0]["event_type"] == "test_event_2"
        assert events2[0]["message"] == "Session 2 event"
        assert events2[0]["data"]["session"] == 2
        assert events2[0]["session_id"] == session2_id

    def test_debug_events_cleared_per_session(self, client, mock_agent_deps, mock_session_manager):
        """Test that clearing debug events only affects the specific session"""
        
        # Create two sessions
        response1 = client.post("/api/session/new")
        session1_id = response1.json()["session_id"]
        
        response2 = client.post("/api/session/new")
        session2_id = response2.json()["session_id"]
        
        # Add events to both sessions
        debug1 = get_debug_capture_instance(session1_id)
        debug2 = get_debug_capture_instance(session2_id)
        
        # Both should be enabled by default from session creation
        assert debug1.is_enabled()
        assert debug2.is_enabled()
        
        debug1.capture_event("session1_event", "Session 1 test", {"test": "data1"})
        debug2.capture_event("session2_event", "Session 2 test", {"test": "data2"})
        
        # Verify both sessions have events
        debug_response1 = client.get(f"/api/{session1_id}/debug", headers={"X-API-Key": "test_12345"})
        debug_response2 = client.get(f"/api/{session2_id}/debug", headers={"X-API-Key": "test_12345"})
        
        assert len(debug_response1.json()["events"]) == 1
        assert len(debug_response2.json()["events"]) == 1
        
        # Clear events for session 1 only
        clear_response = client.delete(f"/api/{session1_id}/debug", headers={"X-API-Key": "test_12345"})
        assert clear_response.status_code == 204
        
        # Verify session 1 events are cleared but session 2 events remain
        debug_response1_after = client.get(f"/api/{session1_id}/debug", headers={"X-API-Key": "test_12345"})
        debug_response2_after = client.get(f"/api/{session2_id}/debug", headers={"X-API-Key": "test_12345"})
        
        assert len(debug_response1_after.json()["events"]) == 0
        assert len(debug_response2_after.json()["events"]) == 1
        assert debug_response2_after.json()["events"][0]["event_type"] == "session2_event"

    def test_debug_toggle_per_session(self, client, mock_agent_deps, mock_session_manager):
        """Test that debug enable/disable is session-specific"""
        
        # Create two sessions
        response1 = client.post("/api/session/new")
        session1_id = response1.json()["session_id"]
        
        response2 = client.post("/api/session/new")
        session2_id = response2.json()["session_id"]
        
        # Both should be enabled by default
        debug_status1 = client.get(f"/api/{session1_id}/debug", headers={"X-API-Key": "test_12345"})
        debug_status2 = client.get(f"/api/{session2_id}/debug", headers={"X-API-Key": "test_12345"})
        
        assert debug_status1.json()["enabled"] is True
        assert debug_status2.json()["enabled"] is True
        
        # Disable debug for session 1 only
        toggle_response = client.post(
            f"/api/{session1_id}/debug/toggle", 
            json={"enabled": False},
            headers={"X-API-Key": "test_12345"}
        )
        assert toggle_response.status_code == 200
        assert toggle_response.json()["enabled"] is False
        
        # Verify session 1 is disabled, session 2 is still enabled
        debug_status1_after = client.get(f"/api/{session1_id}/debug", headers={"X-API-Key": "test_12345"})
        debug_status2_after = client.get(f"/api/{session2_id}/debug", headers={"X-API-Key": "test_12345"})
        
        assert debug_status1_after.json()["enabled"] is False
        assert debug_status2_after.json()["enabled"] is True

    def test_session_deletion_cleans_debug_data(self, client, mock_agent_deps, mock_session_manager):
        """Test that deleting a session also cleans up its debug data"""
        
        # Create a session
        response = client.post("/api/session/new")
        session_id = response.json()["session_id"]
        
        # Add debug events
        debug_capture = get_debug_capture_instance(session_id)
        assert debug_capture.is_enabled()  # Should be enabled by default
        debug_capture.capture_event("test_event", "Test message", {"test": "data"})
        
        # Verify debug events exist
        debug_response = client.get(f"/api/{session_id}/debug", headers={"X-API-Key": "test_12345"})
        assert len(debug_response.json()["events"]) == 1
        
        # Mock the delete_agent_instance to return True
        with patch("api.routes.delete_agent_instance", return_value=True):
            # Delete the session
            delete_response = client.delete(f"/api/session/{session_id}")
            assert delete_response.status_code == 204
        
        # Verify debug events for this session are cleaned up by checking the _debug_sessions
        assert session_id not in _debug_sessions

    def test_empty_session_debug_state(self, client, mock_agent_deps, mock_session_manager):
        """Test that a new session starts with empty debug state"""
        
        # Create a new session
        response = client.post("/api/session/new")
        session_id = response.json()["session_id"]
        
        # Check debug state - should be enabled but with no events
        debug_response = client.get(f"/api/{session_id}/debug", headers={"X-API-Key": "test_12345"})
        debug_data = debug_response.json()
        
        assert debug_response.status_code == 200
        assert debug_data["enabled"] is True  # Should be enabled by default
        assert len(debug_data["events"]) == 0  # Should have no events initially
