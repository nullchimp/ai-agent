import pytest
from unittest.mock import patch, Mock, AsyncMock, MagicMock
from fastapi.testclient import TestClient
import uuid
import json

from api.app import create_app
from agent import get_agent_instance


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


@pytest.fixture
def auth_headers():
    return {"X-API-Key": "test_12345"}


class TestFrontendSessionIntegration:
    """Test the updated frontend session handling with new GET endpoints"""
    
    def setup_method(self):
        # Clear any existing state between tests
        from core.debug_capture import _debug_sessions
        _debug_sessions.clear()
    
    @patch('uuid.uuid4')
    @patch('agent.Agent')  
    @patch('agent.MCPSessionManager')
    def test_frontend_new_session_flow(self, mock_mcp_manager, mock_agent_class, mock_uuid, client):
        """Test the flow when frontend creates a new session"""
        # Setup mocks
        test_session_id = "new-session-123"
        mock_uuid.return_value = test_session_id
        
        # Mock agent instance
        mock_agent = Mock()
        mock_agent.session_id = test_session_id
        mock_agent.initialize_mcp_tools = AsyncMock()
        mock_agent_class.return_value = mock_agent
        
        # Mock MCPSessionManager
        mock_mcp_instance = Mock()
        mock_mcp_instance.discovery = AsyncMock()
        mock_mcp_instance.tools = []
        mock_mcp_manager.return_value = mock_mcp_instance
        
        # Frontend calls GET /api/session/new
        response = client.get("/api/session/new")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == test_session_id
        assert data["message"] == "Session is active"
        
        # Verify backend calls
        mock_agent_class.assert_called_once_with(test_session_id)
        mock_agent.initialize_mcp_tools.assert_called_once()
        
    @patch('agent.Agent')
    @patch('agent.MCPSessionManager')
    def test_frontend_verify_existing_session(self, mock_mcp_manager, mock_agent_class, client):
        """Test the flow when frontend verifies an existing session"""
        # Setup mocks
        existing_session_id = "existing-session-456"
        
        # Mock agent instance
        mock_agent = Mock()
        mock_agent.session_id = existing_session_id
        mock_agent.initialize_mcp_tools = AsyncMock()
        mock_agent_class.return_value = mock_agent
        
        # Mock MCPSessionManager
        mock_mcp_instance = Mock()
        mock_mcp_instance.discovery = AsyncMock()
        mock_mcp_instance.tools = []
        mock_mcp_manager.return_value = mock_mcp_instance
        
        # Frontend calls GET /api/session/{sessionId}
        response = client.get(f"/api/session/{existing_session_id}")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == existing_session_id
        assert data["message"] == "Session is active"
        
        # Verify backend calls
        mock_agent_class.assert_called_once_with(existing_session_id)
        mock_agent.initialize_mcp_tools.assert_called_once()
        
    @patch('agent.Agent')
    @patch('agent.MCPSessionManager')
    def test_frontend_session_verification_failure(self, mock_mcp_manager, mock_agent_class, client):
        """Test when session verification fails (session doesn't exist in backend)"""
        # Setup mocks - simulate agent initialization failure
        mock_agent_class.side_effect = Exception("Session not found")
        
        # Frontend calls GET /api/session/{sessionId}
        response = client.get("/api/session/lost-session-789")
        
        # Verify error response
        assert response.status_code == 500
        data = response.json()
        assert "Error initializing agent" in data["detail"]
        
        # Frontend should handle this by clearing sessionId and creating new session when needed
        
    @patch('uuid.uuid4')
    @patch('agent.Agent')
    @patch('agent.MCPSessionManager')
    def test_full_frontend_session_lifecycle(self, mock_mcp_manager, mock_agent_class, mock_uuid, client, auth_headers):
        """Test complete session lifecycle: create -> verify -> use"""
        # Setup mocks
        test_session_id = "lifecycle-session-123"
        mock_uuid.return_value = test_session_id
        
        # Mock agent instance  
        mock_agent = Mock()
        mock_agent.session_id = test_session_id
        mock_agent.initialize_mcp_tools = AsyncMock()
        
        async def mock_process_query(query):
            return ("Test response", set())
        
        mock_agent.process_query = mock_process_query
        mock_agent.get_tools = MagicMock(return_value=[])
        mock_agent_class.return_value = mock_agent
        
        # Mock MCPSessionManager
        mock_mcp_instance = Mock()
        mock_mcp_instance.discovery = AsyncMock()
        mock_mcp_instance.tools = []
        mock_mcp_manager.return_value = mock_mcp_instance
        
        # Step 1: Frontend creates new session
        response = client.get("/api/session/new")
        assert response.status_code == 200
        session_data = response.json()
        session_id = session_data["session_id"]
        assert session_id == test_session_id
        
        # Step 2: Frontend verifies session (simulating browser refresh)
        response = client.get(f"/api/session/{session_id}")
        assert response.status_code == 200
        verify_data = response.json()
        assert verify_data["session_id"] == session_id
        
        # Step 3: Frontend uses session to send message
        response = client.post(f"/api/{session_id}/ask", 
                             headers=auth_headers,
                             json={"query": "Hello"})
        assert response.status_code == 200
        
        # Step 4: Frontend gets tools for session
        response = client.get(f"/api/{session_id}/tools", headers=auth_headers)
        assert response.status_code == 200
        
        # Verify agent was created once (subsequent calls use cached instance)
        assert mock_agent_class.call_count == 1  # Agent instance is cached
        
    def test_frontend_session_message_flow_documentation(self):
        """Document the expected frontend behavior for session handling"""
        expected_flow = {
            "app_initialization": {
                "step_1": "Load sessions from localStorage",
                "step_2": "If session has sessionId, call GET /api/session/{sessionId}",
                "step_3": "If backend returns error, clear sessionId but keep frontend session",
                "step_4": "If no sessions exist, call GET /api/session/new"
            },
            "message_sending": {
                "step_1": "Check if current session has sessionId",
                "step_2": "If no sessionId, call GET /api/session/new to create backend session",
                "step_3": "Use sessionId to call POST /api/{sessionId}/ask",
                "step_4": "Save sessionId to localStorage for future use"
            },
            "session_persistence": {
                "frontend": "Sessions persisted in localStorage with messages",
                "backend": "Sessions created on-demand, message history not persisted",
                "graceful_degradation": "Frontend works even if backend sessions are lost"
            }
        }
        
        # This test documents the expected behavior
        assert expected_flow["app_initialization"]["step_2"] == "If session has sessionId, call GET /api/session/{sessionId}"
        assert expected_flow["message_sending"]["step_2"] == "If no sessionId, call GET /api/session/new to create backend session"
        assert "graceful_degradation" in expected_flow["session_persistence"]
