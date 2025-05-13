import pytest
from core.azureopenai.client import Client
from unittest.mock import MagicMock, AsyncMock
from types import SimpleNamespace


@pytest.mark.asyncio
async def test_client_make_request_success(monkeypatch):
    client = Client(api_key="k", endpoint="http://x", timeout=1)
    mock_post = AsyncMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"choices": [{"message": {"content": "hi"}}]}
    mock_post.return_value = mock_resp
    monkeypatch.setattr(client.http_client, "post", mock_post)
    
    # Test with a regular dict instead of SimpleNamespace
    out = await client.make_request([{"role": "user", "content": "hi"}])
    assert out["choices"][0]["message"]["content"] == "hi"
    mock_post.assert_called()


@pytest.mark.asyncio
async def test_client_make_request_error(monkeypatch):
    client = Client(api_key="k", endpoint="http://x", timeout=1)
    mock_post = AsyncMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 400
    mock_resp.json.return_value = {"error": {"message": "fail"}}
    mock_post.return_value = mock_resp
    monkeypatch.setattr(client.http_client, "post", mock_post)
    
    # Test with a regular dict instead of SimpleNamespace
    with pytest.raises(Exception) as exc:
        await client.make_request([{"role": "user", "content": "hi"}])
    assert "API error" in str(exc.value)


@pytest.mark.asyncio
async def test_client_get_completion(monkeypatch):
    client = Client(api_key="k", endpoint="http://x", timeout=1)
    # Add the get_completion method implementation for testing
    async def mock_make_request(*args, **kwargs):
        return {"choices": [{"message": {"content": "hi"}}]}
    client.make_request = mock_make_request
    out = await client.get_completion([{"role": "user", "content": "hi"}])
    assert out == "hi"


@pytest.mark.asyncio
async def test_client_get_completion_no_choices(monkeypatch):
    client = Client(api_key="k", endpoint="http://x", timeout=1)
    # Add the get_completion method implementation for testing
    async def mock_make_request(*args, **kwargs):
        return {"choices": []}
    client.make_request = mock_make_request
    with pytest.raises(Exception):
        await client.get_completion([{"role": "user", "content": "hi"}])


@pytest.mark.asyncio
async def test_client_make_request_with_tools(monkeypatch):
    client = Client(api_key="k", endpoint="http://x", timeout=1)
    mock_post = AsyncMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"choices": [{"message": {"content": "hi"}}]}
    mock_post.return_value = mock_resp
    monkeypatch.setattr(client.http_client, "post", mock_post)
    
    out = await client.make_request([{"role": "user", "content": "hi"}], tools=[{"type": "tool"}])
    assert out["choices"][0]["message"]["content"] == "hi"
    mock_post.assert_called()


def test_client_init_defaults():
    client = Client(api_key="k")
    assert client.api_key == "k"
    assert client.endpoint is not None
    assert client.timeout is not None

def test_placeholder():
    assert True
