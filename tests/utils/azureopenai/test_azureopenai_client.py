import pytest
from utils.azureopenai.client import Client, Message, Response, ResponseChoice, ErrorResponse
from unittest.mock import patch, MagicMock


def test_message_and_responsechoice():
    m = Message(role="user", content="hi")
    rc = ResponseChoice(message={"content": "hi"})
    assert m.role == "user"
    assert rc.message["content"] == "hi"


def test_error_response():
    err = ErrorResponse({"message": "fail"})
    assert err.message == "fail"
    err2 = ErrorResponse({})
    assert err2.message == ""


def test_response_to_json_and_dict():
    data = {"choices": [{"message": {"content": "hi"}}]}
    resp = Response(data)
    assert resp.to_json().startswith("{")
    assert resp.to_dict() == data


def test_response_with_error():
    data = {"choices": [], "error": {"message": "fail"}}
    resp = Response(data)
    assert resp.error.message == "fail"
    assert "fail" in resp.to_json()


def test_client_make_request(monkeypatch):
    client = Client(api_key="k", endpoint="http://x", timeout=1)
    mock_post = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"choices": [{"message": {"content": "hi"}}]}
    mock_post.return_value = mock_resp
    monkeypatch.setattr(client.http_client, "post", mock_post)
    out = client.make_request([Message(role="user", content="hi")])
    assert isinstance(out, Response)
    mock_post.assert_called()


def test_client_make_request_error(monkeypatch):
    client = Client(api_key="k", endpoint="http://x", timeout=1)
    mock_post = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 400
    mock_resp.json.return_value = {"error": {"message": "fail"}}
    mock_post.return_value = mock_resp
    monkeypatch.setattr(client.http_client, "post", mock_post)
    with pytest.raises(Exception):
        client.make_request([Message(role="user", content="hi")])


def test_client_get_completion(monkeypatch):
    client = Client(api_key="k", endpoint="http://x", timeout=1)
    mock_make = MagicMock()
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock()]
    mock_resp.choices[0].message = {"content": "hi"}
    mock_make.return_value = mock_resp
    client.make_request = mock_make
    out = client.get_completion([Message(role="user", content="hi")])
    assert out == "hi"


def test_client_get_completion_no_choices(monkeypatch):
    client = Client(api_key="k", endpoint="http://x", timeout=1)
    mock_make = MagicMock()
    mock_resp = MagicMock()
    mock_resp.choices = []
    mock_make.return_value = mock_resp
    client.make_request = mock_make
    with pytest.raises(Exception):
        client.get_completion([Message(role="user", content="hi")])
