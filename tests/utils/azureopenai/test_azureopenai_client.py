import pytest
from utils.azureopenai.client import Client
from unittest.mock import MagicMock
from types import SimpleNamespace


def test_client_make_request_success(monkeypatch):
    client = Client(api_key="k", endpoint="http://x", timeout=1)
    mock_post = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"choices": [{"message": {"content": "hi"}}]}
    mock_post.return_value = mock_resp
    monkeypatch.setattr(client.http_client, "post", mock_post)
    # Use a message with raw_messages attribute to avoid AttributeError
    msg = SimpleNamespace(role="user", content="hi", raw_messages=[{"role": "user", "content": "hi"}])
    out = client.make_request([msg])
    assert out["choices"][0]["message"]["content"] == "hi"
    mock_post.assert_called()


def test_client_make_request_error(monkeypatch):
    client = Client(api_key="k", endpoint="http://x", timeout=1)
    mock_post = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 400
    mock_resp.json.return_value = {"error": {"message": "fail"}}
    mock_post.return_value = mock_resp
    monkeypatch.setattr(client.http_client, "post", mock_post)
    # Use a message with raw_messages attribute to avoid AttributeError
    msg = SimpleNamespace(role="user", content="hi", raw_messages=[{"role": "user", "content": "hi"}])
    with pytest.raises(Exception) as exc:
        client.make_request([msg])
    assert "API error" in str(exc.value)


def test_client_get_completion(monkeypatch):
    client = Client(api_key="k", endpoint="http://x", timeout=1)
    mock_make = MagicMock()
    mock_make.return_value = {"choices": [{"message": {"content": "hi"}}]}
    client.make_request = mock_make
    out = client.get_completion([{"role": "user", "content": "hi"}])
    assert out == "hi"


def test_client_get_completion_no_choices(monkeypatch):
    client = Client(api_key="k", endpoint="http://x", timeout=1)
    mock_make = MagicMock()
    mock_make.return_value = {"choices": []}
    client.make_request = mock_make
    with pytest.raises(Exception):
        client.get_completion([{"role": "user", "content": "hi"}])


def test_client_make_request_with_tools(monkeypatch):
    client = Client(api_key="k", endpoint="http://x", timeout=1)
    mock_post = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"choices": [{"message": {"content": "hi"}}]}
    mock_post.return_value = mock_resp
    monkeypatch.setattr(client.http_client, "post", mock_post)
    # Use a message with raw_messages attribute to avoid AttributeError
    msg = SimpleNamespace(role="user", content="hi", raw_messages=[{"role": "user", "content": "hi"}])
    out = client.make_request([msg], tools=[{"type": "tool"}])
    assert out["choices"][0]["message"]["content"] == "hi"
    mock_post.assert_called()


def test_client_init_defaults():
    client = Client(api_key="k")
    assert client.api_key == "k"
    assert client.endpoint is not None
    assert client.timeout is not None

def test_placeholder():
    assert True
