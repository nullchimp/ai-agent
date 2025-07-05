import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
import uuid

from api.routes import session_router
from api.models import CreateSessionRequest


@pytest.fixture
def client():
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(session_router)
    return TestClient(app)


class TestSessionAPI:
    @patch('api.routes.create_new_session')
    @patch('api.routes.get_agent_instance')
    @patch('api.routes.get_debug_capture_instance')
    def test_create_session_endpoint(self, mock_debug, mock_agent, mock_create, client):
        mock_session_id = str(uuid.uuid4())
        mock_create.return_value = mock_session_id
        mock_agent.return_value = Mock()
        mock_debug.return_value = Mock()
        
        response = client.post("/api/sessions", json={"title": "Test Session"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == mock_session_id
        assert data["message"] == "Session created successfully"

    @patch('api.routes.list_sessions')
    def test_list_sessions_endpoint(self, mock_list, client):
        mock_sessions = [
            {
                "id": str(uuid.uuid4()),
                "user_id": "default-user",
                "title": "Session 1",
                "is_active": True,
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z",
                "last_activity": "2025-01-01T00:00:00Z",
                "agent_config": {}
            }
        ]
        mock_list.return_value = mock_sessions
        
        response = client.get("/api/sessions")
        
        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data
        assert len(data["sessions"]) == 1
        assert data["sessions"][0]["title"] == "Session 1"

    @patch('api.routes.get_agent_instance')
    @patch('api.routes.get_debug_capture_instance')
    def test_get_session_endpoint(self, mock_debug, mock_agent, client):
        mock_agent.return_value = Mock()
        mock_debug.return_value = Mock()
        
        session_id = str(uuid.uuid4())
        response = client.get(f"/api/session/{session_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id
        assert data["message"] == "Session is active"

    @patch('api.routes.delete_agent_instance')
    @patch('api.routes.get_session_manager')
    @patch('api.routes.delete_debug_capture_instance')
    def test_delete_session_endpoint(self, mock_debug_delete, mock_get_manager, mock_delete, client):
        mock_delete.return_value = True
        mock_session_manager = Mock()
        mock_session_manager.delete_session = AsyncMock(return_value=True)
        mock_get_manager.return_value = mock_session_manager
        
        session_id = str(uuid.uuid4())
        response = client.delete(f"/api/session/{session_id}")
        
        assert response.status_code == 204

    @patch('api.routes.get_session_manager')
    def test_update_session_endpoint(self, mock_get_manager, client):
        mock_session_manager = Mock()
        mock_session_manager.update_session = AsyncMock(return_value=True)
        mock_get_manager.return_value = mock_session_manager
        
        session_id = str(uuid.uuid4())
        update_data = {"title": "Updated Session"}
        response = client.put(f"/api/session/{session_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Session updated successfully"

    def test_create_session_with_default_title(self, client):
        with patch('api.routes.create_new_session') as mock_create, \
             patch('api.routes.get_agent_instance') as mock_agent, \
             patch('api.routes.get_debug_capture_instance') as mock_debug:
            
            mock_session_id = str(uuid.uuid4())
            mock_create.return_value = mock_session_id
            mock_agent.return_value = Mock()
            mock_debug.return_value = Mock()
            
            response = client.post("/api/sessions", json={})
            
            assert response.status_code == 200
            # Verify create_new_session was called with default title
            mock_create.assert_called_once_with(title="New Session")