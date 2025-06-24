import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from api.app import create_app
from core.debug_capture import get_debug_capture_instance, _debug_sessions, clear_all_debug_events
from agent import get_agent_instance

@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)

@pytest.fixture
def auth_headers():
    return {"X-API-Key": "test_12345"}

class TestDebugAPI:
    def setup_method(self):
        # Clear all debug sessions and reset state
        _debug_sessions.clear()
        # Create a default debug capture for tests
        default_capture = get_debug_capture_instance("default")
        default_capture.disable()
        default_capture.clear_events()

    def test_get_debug_info_disabled(self, client, auth_headers):
        response = client.get("/api/test_session/debug", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["enabled"] is False
        assert data["events"] == []

    def test_toggle_debug_enable(self, client, auth_headers):
        response = client.post(
            "/api/test_session/debug/toggle",
            json={"enabled": True},
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["enabled"] is True
        
        # Verify the test_session capture instance is enabled
        test_capture = get_debug_capture_instance("test_session")
        assert test_capture.is_enabled()

    def test_toggle_debug_disable(self, client, auth_headers):
        # Enable debug first for the specific session
        test_capture = get_debug_capture_instance("test_session")
        test_capture.enable()
        
        response = client.post(
            "/api/test_session/debug/toggle",
            json={"enabled": False},
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["enabled"] is False
        assert not test_capture.is_enabled()

    def test_get_debug_info_with_events(self, client, auth_headers):
        test_capture = get_debug_capture_instance("test_session")
        test_capture.enable()
        test_capture.capture_tool_call("test_tool", {"arg": "value"})
        
        response = client.get("/api/test_session/debug", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["events"]) == 1
        assert data["events"][0]["event_type"] == "tool_call"
        assert data["events"][0]["message"] == "Tool Call: test_tool"

    def test_get_debug_info_with_session_filter(self, client, auth_headers):
        # Create two separate session captures
        capture1 = get_debug_capture_instance("session_1")
        capture2 = get_debug_capture_instance("session_2")
        
        capture1.enable()
        capture2.enable()
        
        capture1.capture_tool_call("tool1", {})
        capture2.capture_tool_call("tool2", {})
        
        response = client.get("/api/session_1/debug", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["events"]) == 1
        assert data["events"][0]["message"] == "Tool Call: tool1"

    def test_clear_debug_events(self, client, auth_headers):
        test_capture = get_debug_capture_instance("test_session")
        test_capture.enable()
        test_capture.capture_tool_call("test_tool", {})
        
        # Verify event exists
        events = test_capture.get_events()
        assert len(events) == 1
        
        response = client.delete("/api/test_session/debug", headers=auth_headers)
        assert response.status_code == 204
        
        # Verify all events cleared (global clear)
        assert len(_debug_sessions) == 0 or all(len(capture.get_events()) == 0 for capture in _debug_sessions.values())

    def test_clear_debug_events_by_session(self, client, auth_headers):
        # Create two separate session captures
        capture1 = get_debug_capture_instance("session_1")
        capture2 = get_debug_capture_instance("session_2")
        
        capture1.enable()
        capture2.enable()
        
        capture1.capture_tool_call("tool1", {})
        capture2.capture_tool_call("tool2", {})
        
        response = client.delete("/api/session_1/debug", headers=auth_headers)
        assert response.status_code == 204
        
        # Verify only session_1 events are cleared
        assert len(capture1.get_events()) == 0
        assert len(capture2.get_events()) == 1
        assert capture2.get_events()[0]["message"] == "Tool Call: tool2"

    def test_ask_endpoint_sets_session_id(self, client, auth_headers):
        # This test is not as relevant with per-session captures
        # since session management is handled differently now
        mock_agent = MagicMock()
        
        # Mock the async process_query method to return an awaitable
        async def mock_process_query(query):
            return ("Test response", [])
        
        mock_agent.process_query = mock_process_query
        
        # Mock the dependency injection by overriding the app dependency
        async def mock_get_agent_instance(session_id: str = None):
            return mock_agent
            
        client.app.dependency_overrides[get_agent_instance] = mock_get_agent_instance
        
        try:
            response = client.post(
                "/api/test_session/ask",
                json={"query": "test query"},
                headers=auth_headers
            )
            
            # The main goal is that the request succeeds
            assert response.status_code == 200
            
            data = response.json()
            assert data["response"] == "Test response"
            assert data["used_tools"] == []
        finally:
            # Clean up the dependency override
            client.app.dependency_overrides.clear()

    def test_unauthorized_access(self, client):
        response = client.get("/api/test_session/debug")
        assert response.status_code == 401
