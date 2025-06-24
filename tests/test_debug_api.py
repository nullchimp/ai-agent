import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from api.app import create_app
from core.debug_capture import debug_capture

@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)

@pytest.fixture
def auth_headers():
    return {"X-API-Key": "test_12345"}

class TestDebugAPI:
    def setup_method(self):
        # Reset debug capture state
        debug_capture.disable()
        debug_capture.clear_events()

    def test_get_debug_info_disabled(self, client, auth_headers):
        response = client.get("/api/debug", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["enabled"] is False
        assert data["events"] == []

    def test_toggle_debug_enable(self, client, auth_headers):
        response = client.post(
            "/api/debug/toggle",
            json={"enabled": True},
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["enabled"] is True
        assert debug_capture.is_enabled()

    def test_toggle_debug_disable(self, client, auth_headers):
        debug_capture.enable()
        
        response = client.post(
            "/api/debug/toggle",
            json={"enabled": False},
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["enabled"] is False
        assert not debug_capture.is_enabled()

    def test_get_debug_info_with_events(self, client, auth_headers):
        debug_capture.enable()
        debug_capture.capture_tool_call("test_tool", {"arg": "value"})
        
        response = client.get("/api/debug", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["enabled"] is True
        assert len(data["events"]) == 1
        assert data["events"][0]["event_type"] == "tool_call"
        assert data["events"][0]["message"] == "Tool Call: test_tool"

    def test_get_debug_info_with_session_filter(self, client, auth_headers):
        debug_capture.enable()
        debug_capture.set_session_id("session_1")
        debug_capture.capture_tool_call("tool1", {})
        
        debug_capture.set_session_id("session_2")
        debug_capture.capture_tool_call("tool2", {})
        
        response = client.get("/api/debug?session_id=session_1", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["events"]) == 1
        assert data["events"][0]["message"] == "Tool Call: tool1"

    def test_clear_debug_events(self, client, auth_headers):
        debug_capture.enable()
        debug_capture.capture_tool_call("test_tool", {})
        
        # Verify event exists
        events = debug_capture.get_events()
        assert len(events) == 1
        
        response = client.delete("/api/debug", headers=auth_headers)
        assert response.status_code == 200
        
        # Verify events cleared
        events = debug_capture.get_events()
        assert len(events) == 0

    def test_clear_debug_events_by_session(self, client, auth_headers):
        debug_capture.enable()
        debug_capture.set_session_id("session_1")
        debug_capture.capture_tool_call("tool1", {})
        
        debug_capture.set_session_id("session_2")
        debug_capture.capture_tool_call("tool2", {})
        
        response = client.delete("/api/debug?session_id=session_1", headers=auth_headers)
        assert response.status_code == 200
        
        events = debug_capture.get_events()
        assert len(events) == 1
        assert events[0]["message"] == "Tool Call: tool2"

    @patch('agent.agent_instance.process_query')
    def test_ask_endpoint_sets_session_id(self, mock_process, client, auth_headers):
        mock_process.return_value = ("Test response", [])
        
        response = client.post(
            "/api/ask",
            json={"query": "test query"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        # Session ID should be set during the request
        current_session = debug_capture.get_current_session_id()
        assert current_session is not None

    def test_unauthorized_access(self, client):
        response = client.get("/api/debug")
        assert response.status_code == 401
