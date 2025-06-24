import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
import uuid

from api.app import create_app


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
    @patch('api.routes.MCPSessionManager')
    @patch('uuid.uuid4')
    def test_create_new_session_success(self, mock_uuid, mock_mcp_manager, mock_get_agent, client):
        """Test successful session creation"""
        # Setup mocks
        test_session_id = "test-session-123"
        mock_uuid.return_value = test_session_id
        
        mock_agent = MagicMock()
        mock_get_agent.return_value = mock_agent
        
        mock_session_manager = AsyncMock()
        mock_session_manager.tools = []
        mock_mcp_manager.return_value = mock_session_manager
        
        # Make request
        response = client.post("/api/session/new")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == test_session_id
        assert data["message"] == "Session created successfully"
        
        # Verify agent was retrieved
        mock_get_agent.assert_called_once_with(test_session_id)
        
    @patch('api.routes.get_agent_instance')
    @patch('api.routes.MCPSessionManager')
    @patch('uuid.uuid4')
    def test_create_new_session_with_tools(self, mock_uuid, mock_mcp_manager, mock_get_agent, client):
        """Test session creation with tool initialization"""
        # Setup mocks
        test_session_id = "test-session-123"
        mock_uuid.return_value = test_session_id
        
        mock_agent = MagicMock()
        mock_get_agent.return_value = mock_agent
        
        mock_tool = MagicMock()
        mock_session_manager = AsyncMock()
        mock_session_manager.tools = [mock_tool]
        mock_mcp_manager.return_value = mock_session_manager
        
        # Make request
        response = client.post("/api/session/new")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == test_session_id
        
        # Verify tool was added to agent
        mock_agent.add_tool.assert_called_once_with(mock_tool)
        
    @patch('api.routes.get_agent_instance')
    @patch('api.routes.MCPSessionManager')
    @patch('uuid.uuid4')
    def test_create_new_session_initialization_error(self, mock_uuid, mock_mcp_manager, mock_get_agent, client):
        """Test session creation with initialization error"""
        # Setup mocks
        test_session_id = "test-session-123"
        mock_uuid.return_value = test_session_id
        
        mock_get_agent.return_value = MagicMock()
        
        # Make session manager throw an error
        mock_mcp_manager.side_effect = Exception("MCP initialization failed")
        
        # Make request
        response = client.post("/api/session/new")
        
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
    
    @patch('agent.get_agent_instance')
    @patch('api.routes.debug_capture')
    def test_ask_with_session_id(self, mock_debug_capture, mock_get_agent, client, auth_headers):
        """Test the ask endpoint with session ID"""
        # Setup mock
        mock_agent = AsyncMock()
        mock_agent.process_query.return_value = ("Test response", ["tool1"])
        mock_get_agent.return_value = mock_agent
        
        # Mock debug capture
        mock_debug_capture.set_session_id = MagicMock()
        
        # Make request
        response = client.post(
            "/api/test-session-123/ask",
            json={"query": "Test question"},
            headers=auth_headers
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["response"] == "Test response"
        assert data["used_tools"] == ["tool1"]
        
        # Verify agent was retrieved with correct session ID
        mock_get_agent.assert_called_once_with("test-session-123")
        
        # Verify query was processed
        mock_agent.process_query.assert_called_once_with("Test question")
        
        # Verify debug session was set
        mock_debug_capture.set_session_id.assert_called_once_with("test-session-123")
        
    @patch('agent.get_agent_instance')
    def test_tools_list_with_session_id(self, mock_get_agent, client, auth_headers):
        """Test the tools list endpoint with session ID"""
        # Setup mock
        mock_tool_info = MagicMock()
        mock_tool_info.name = "test_tool"
        mock_tool_info.description = "Test tool description"
        mock_tool_info.enabled = True
        mock_tool_info.parameters = {"param1": "value1"}
        
        mock_agent = MagicMock()
        mock_agent.get_tools.return_value = [mock_tool_info]
        mock_get_agent.return_value = mock_agent
        
        # Make request
        response = client.get(
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
        assert tool["parameters"] == {"param1": "value1"}
        
        # Verify agent was retrieved with correct session ID
        mock_get_agent.assert_called_once_with("test-session-123")
        
    @patch('agent.get_agent_instance')
    def test_tools_toggle_with_session_id(self, mock_get_agent, client, auth_headers):
        """Test the tools toggle endpoint with session ID"""
        # Setup mock
        mock_agent = MagicMock()
        mock_agent.enable_tool.return_value = True
        mock_get_agent.return_value = mock_agent
        
        # Make request
        response = client.post(
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
        
        # Verify agent was retrieved with correct session ID
        mock_get_agent.assert_called_once_with("test-session-123")
        
        # Verify tool was enabled
        mock_agent.enable_tool.assert_called_once_with("test_tool")


if __name__ == "__main__":
    pytest.main([__file__])
