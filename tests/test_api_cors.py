import pytest
from fastapi.testclient import TestClient
from api.app import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_cors_headers_present(client):
    """Test that CORS headers are correctly set for localhost:8080"""
    response = client.options(
        "/api/ask",
        headers={
            "Origin": "http://localhost:8080",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "X-API-Key,Content-Type"
        }
    )
    
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:8080"
    assert "POST" in response.headers.get("access-control-allow-methods", "")
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_cors_blocked_for_other_origins(client):
    """Test that CORS is blocked for origins other than localhost:8080"""
    response = client.options(
        "/api/ask",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "X-API-Key,Content-Type"
        }
    )
    
    # Should not have the origin in the response headers
    assert response.headers.get("access-control-allow-origin") != "http://localhost:3000"


def test_cors_actual_request(client):
    """Test that actual requests from localhost:8080 include CORS headers"""
    response = client.get(
        "/",
        headers={"Origin": "http://localhost:8080"}
    )
    
    assert response.headers.get("access-control-allow-origin") == "http://localhost:8080"
