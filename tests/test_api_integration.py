import os
import sys
from unittest.mock import patch, AsyncMock
import importlib

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.api import routes, app as app_module


@pytest.mark.asyncio
async def test_ask_endpoint_with_real_agent_integration():
    with patch.object(
        routes.agent, "process_query", new_callable=AsyncMock
    ) as mock_process_query:
        mock_process_query.return_value = "Artificial intelligence (AI) is a branch of computer science focused on creating systems or machines that can perform tasks that typically require human intelligence. These tasks include learning, reasoning, problem-solving, perception, language understanding, and decision-making. AI technologies use algorithms and large datasets to mimic human cognitive processes and automate complex or repetitive tasks.\n\nThere are two main types of AI:\n\n- Narrow AI: Designed for specific tasks (e.g., voice assistants, image recognition).\n- General AI: Hypothetical systems with human-level intelligence across a wide range of tasks.\n\nAI is used in various industries, including healthcare, finance, transportation, and more, to improve efficiency, accuracy, and decision-making."

        importlib.reload(app_module)
        reloaded_app = app_module.create_app()
        client = TestClient(reloaded_app)

        with patch("src.api.routes.session_manager") as mock_session_manager:
            mock_session_manager.discovery = AsyncMock()
            mock_session_manager.tools = []

            with patch.dict(os.environ, {"API_KEY": "test-key"}):
                response = client.post(
                    "/api/ask",
                    json={"query": "What is artificial intelligence?"},
                    headers={"X-API-Key": "test-key"},
                )

                assert response.status_code == 200
                data = response.json()
                assert "Artificial intelligence (AI)" in data["response"]


@pytest.mark.asyncio
async def test_ask_endpoint_agent_error_handling():
    with patch.object(
        routes.agent, "process_query", new_callable=AsyncMock
    ) as mock_process_query:
        mock_process_query.side_effect = Exception("Event loop is closed")

        importlib.reload(app_module)
        reloaded_app = app_module.create_app()
        client = TestClient(reloaded_app)

        with patch("src.api.routes.session_manager") as mock_session_manager:
            mock_session_manager.discovery = AsyncMock()
            mock_session_manager.tools = []

            with patch.dict(os.environ, {"API_KEY": "test-key"}):
                response = client.post(
                    "/api/ask",
                    json={"query": "What is artificial intelligence?"},
                    headers={"X-API-Key": "test-key"},
                )

                assert response.status_code == 200
                data = response.json()
                assert "Sorry, I encountered an error: Event loop is closed" in data["response"]
