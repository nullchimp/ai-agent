import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
import uuid

from api.app import create_app
from agent import get_agent_instance


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


@pytest.fixture
def auth_headers():
    return {"X-API-Key": "test_12345"}


class TestSessionRoutes:
    """Test session creation and deletion routes"""
    
    @patch('api.routes.get_agent_instance')
    @patch('api.routes.get_debug_capture_instance')
    @patch('uuid.uuid4')
    def test_get_session_new_success(self, mock_uuid, mock_get_debug, mock_get_agent, client):
        """Test successful creation of new session"""
        # Setup mocks
        test_session_id = "test-session-123"
        mock_uuid.return_value = test_session_id
        
        mock_agent = AsyncMock()
        mock_get_agent.return_value = mock_agent
        mock_get_debug.return_value = MagicMock()
        
        # Make request
        response = client.get("/api/session/new")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == test_session_id
        assert data["message"] == "Session is active"
        
        # Verify agent and debug instances were retrieved
        mock_get_agent.assert_called_once_with(test_session_id)
        mock_get_debug.assert_called_once_with(test_session_id)
        
    @patch('api.routes.get_agent_instance')
    @patch('api.routes.get_debug_capture_instance')
    def test_get_session_existing_success(self, mock_get_debug, mock_get_agent, client):
        """Test getting existing session"""
        # Setup mocks
        test_session_id = "existing-session-456"
        
        mock_agent = AsyncMock()
        mock_get_agent.return_value = mock_agent
        mock_get_debug.return_value = MagicMock()
        
        # Make request
        response = client.get(f"/api/session/{test_session_id}")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == test_session_id
        assert data["message"] == "Session is active"
        
        # Verify agent and debug instances were retrieved
        mock_get_agent.assert_called_once_with(test_session_id)
        mock_get_debug.assert_called_once_with(test_session_id)
        
    @patch('api.routes.get_agent_instance')
    @patch('api.routes.get_debug_capture_instance')
    def test_get_session_initialization_error(self, mock_get_debug, mock_get_agent, client):
        """Test session get with initialization error"""
        # Setup mocks
        test_session_id = "error-session-789"
        
        mock_get_debug.return_value = MagicMock()
        
        # Make agent initialization fail
        mock_get_agent.side_effect = Exception("MCP initialization failed")
        
        # Make request
        response = client.get(f"/api/session/{test_session_id}")
        
        # Verify error response
        assert response.status_code == 500
        data = response.json()
        assert "Error initializing agent" in data["detail"]
        assert "MCP initialization failed" in data["detail"]
        
    @patch('api.routes.delete_agent_instance')
    def test_delete_session_success(self, mock_delete_agent, client):
        """Test successful session deletion"""
        # Setup mock
        mock_delete_agent.return_value = True
        
        # Make request
        response = client.delete("/api/session/test-session-123")
        
        # Verify response
        assert response.status_code == 204
        assert response.content == b""
        
        # Verify agent deletion was called
        mock_delete_agent.assert_called_once_with("test-session-123")
        
    @patch('api.routes.delete_agent_instance')
    def test_delete_session_not_found(self, mock_delete_agent, client):
        """Test deletion of non-existent session"""
        # Setup mock
        mock_delete_agent.return_value = False
        
        # Make request
        response = client.delete("/api/session/non-existent-session")
        
        # Verify error response
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Session not found"
        
        # Verify agent deletion was attempted
        mock_delete_agent.assert_called_once_with("non-existent-session")


class TestSessionBasedRoutes:
    """Test that existing routes work with session IDs"""
    
    def test_ask_with_session_id(self, client, auth_headers):
        """Test the ask endpoint with session ID"""
        # Setup mock agent
        mock_agent = AsyncMock()
        mock_agent.process_query.return_value = ("Test response", ["tool1"])
        
        def mock_get_agent_instance(session_id: str):
            return mock_agent
        
        # Override the dependency
        app = create_app()
        app.dependency_overrides[get_agent_instance] = mock_get_agent_instance
        test_client = TestClient(app)
        
        # Make request
        response = test_client.post(
            "/api/test-session-123/ask",
            json={"query": "Test question"},
            headers=auth_headers
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["response"] == "Test response"
        assert data["used_tools"] == ["tool1"]
        
        # Verify query was processed
        mock_agent.process_query.assert_called_once_with("Test question")
        
        # Clean up
        app.dependency_overrides.clear()
        
    def test_tools_list_with_session_id(self, client, auth_headers):
        """Test the tools list endpoint with session ID"""
        # Setup mock
        mock_tool_info = MagicMock()
        mock_tool_info.name = "test_tool"
        mock_tool_info.description = "Test tool description"
        mock_tool_info.enabled = True
        mock_tool_info.source = "test_source"
        
        mock_agent = MagicMock()
        mock_agent.get_tools.return_value = [mock_tool_info]
        
        def mock_get_agent_instance(session_id: str):
            return mock_agent
        
        # Override the dependency
        app = create_app()
        app.dependency_overrides[get_agent_instance] = mock_get_agent_instance
        test_client = TestClient(app)
        
        # Make request
        response = test_client.get(
            "/api/test-session-123/tools",
            headers=auth_headers
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert len(data["tools"]) == 1
        tool = data["tools"][0]
        assert tool["name"] == "test_tool"
        assert tool["description"] == "Test tool description"
        assert tool["enabled"] is True
        
        # Clean up
        app.dependency_overrides.clear()
        
    def test_tools_toggle_with_session_id(self, client, auth_headers):
        """Test the tools toggle endpoint with session ID"""
        # Setup mock
        mock_agent = MagicMock()
        mock_agent.enable_tool.return_value = True
        
        def mock_get_agent_instance(session_id: str):
            return mock_agent
        
        # Override the dependency
        app = create_app()
        app.dependency_overrides[get_agent_instance] = mock_get_agent_instance
        test_client = TestClient(app)
        
        # Make request
        response = test_client.post(
            "/api/test-session-123/tools/toggle",
            json={"tool_name": "test_tool", "enabled": True},
            headers=auth_headers
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["tool_name"] == "test_tool"
        assert data["enabled"] is True
        assert "enabled" in data["message"]
        
        # Verify tool was enabled
        mock_agent.enable_tool.assert_called_once_with("test_tool")
        
        # Clean up
        app.dependency_overrides.clear()


if __name__ == "__main__":
    pytest.main([__file__])
