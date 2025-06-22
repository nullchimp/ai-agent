import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from src.api.app import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_ask_endpoint_with_valid_api_key(client):
    with patch.dict(os.environ, {"API_KEY": "test-key"}):
        response = client.post(
            "/api/ask",
            json={"query": "What is the weather?"},
            headers={"X-API-Key": "test-key"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "Mock response for query: What is the weather?" in data["response"]


def test_ask_endpoint_without_api_key(client):
    response = client.post(
        "/api/ask",
        json={"query": "What is the weather?"}
    )
    
    assert response.status_code == 401
    assert "API key is required" in response.json()["detail"]


def test_ask_endpoint_with_invalid_api_key(client):
    with patch.dict(os.environ, {"API_KEY": "correct-key"}):
        response = client.post(
            "/api/ask",
            json={"query": "What is the weather?"},
            headers={"X-API-Key": "wrong-key"}
        )
        
        assert response.status_code == 401
        assert "Invalid API key" in response.json()["detail"]


def test_ask_endpoint_invalid_request_body(client):
    with patch.dict(os.environ, {"API_KEY": "test-key"}):
        response = client.post(
            "/api/ask",
            json={"invalid": "field"},
            headers={"X-API-Key": "test-key"}
        )
        
        assert response.status_code == 422  # Validation error


def test_ask_endpoint_missing_request_body(client):
    with patch.dict(os.environ, {"API_KEY": "test-key"}):
        response = client.post(
            "/api/ask",
            headers={"X-API-Key": "test-key"}
        )
        
        assert response.status_code == 422  # Validation error
