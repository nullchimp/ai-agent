import os
from unittest.mock import patch, AsyncMock

import pytest
from fastapi.testclient import TestClient

from src.api.app import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


@pytest.mark.asyncio
async def test_ask_endpoint_with_real_agent_integration(client):
    # Mock the agent's process_query method to avoid actual LLM calls
    with patch('src.api.routes.agent') as mock_agent:
        mock_agent.process_query = AsyncMock(return_value="This is a test response from the agent")
        mock_agent.add_tool = AsyncMock()
        
        # Mock the MCP session manager
        with patch('src.api.routes.session_manager') as mock_session_manager:
            mock_session_manager.discovery = AsyncMock()
            mock_session_manager.tools = []
            
            with patch.dict(os.environ, {"API_KEY": "test-key"}):
                response = client.post(
                    "/api/ask",
                    json={"query": "What is artificial intelligence?"},
                    headers={"X-API-Key": "test-key"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert "response" in data
                assert data["response"] == "This is a test response from the agent"
                
                # Verify the agent was called
                mock_agent.process_query.assert_called_once_with("What is artificial intelligence?")


@pytest.mark.asyncio
async def test_ask_endpoint_agent_error_handling(client):
    # Mock the agent to raise an exception
    with patch('src.api.routes.agent') as mock_agent:
        mock_agent.process_query = AsyncMock(side_effect=Exception("Test error"))
        mock_agent.add_tool = AsyncMock()
        
        with patch('src.api.routes.session_manager') as mock_session_manager:
            mock_session_manager.discovery = AsyncMock()
            mock_session_manager.tools = []
            
            with patch.dict(os.environ, {"API_KEY": "test-key"}):
                response = client.post(
                    "/api/ask",
                    json={"query": "What is artificial intelligence?"},
                    headers={"X-API-Key": "test-key"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert "response" in data
                assert "Sorry, I encountered an error: Test error" in data["response"]
