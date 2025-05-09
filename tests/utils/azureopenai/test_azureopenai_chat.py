import pytest
from utils.azureopenai.chat import Chat
from utils.azureopenai.client import Client, Message, Response
from unittest.mock import MagicMock, patch
import os


def test_chat_create_env(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "key")
    chat = Chat.create()
    assert isinstance(chat, Chat)


def test_chat_create_no_env(monkeypatch):
    monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError):
        Chat.create()


def test_chat_send_prompt(monkeypatch):
    chat = Chat(MagicMock())
    chat.client.get_completion.return_value = "result"
    out = chat.send_prompt("sys", "user")
    assert out == "result"
    chat.client.get_completion.assert_called()


def test_chat_send_prompt_with_options(monkeypatch):
    chat = Chat(MagicMock())
    mock_resp = MagicMock()
    mock_resp.to_json.return_value = "json"
    chat.client.make_request.return_value = mock_resp
    out = chat.send_prompt_with_options("sys", "user", tools=[{"a": 1}])
    assert out == "json"
    chat.client.make_request.assert_called()


def test_chat_send_prompt_with_messages_and_options(monkeypatch):
    chat = Chat(MagicMock())
    mock_resp = MagicMock()
    mock_resp.to_dict.return_value = {"choices": [1]}
    chat.client.make_request.return_value = mock_resp
    out = chat.send_prompt_with_messages_and_options(
        [{"role": "user", "content": "hi"}]
    )
    assert out["choices"] == [1]
    chat.client.make_request.assert_called()


def test_chat_send_followup(monkeypatch):
    chat = Chat(MagicMock())
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock()]
    mock_resp.choices[0].message = {"content": "foo"}
    chat.client.make_request.return_value = mock_resp
    out = chat.send_followup([], "hi")
    assert out == "foo"


def test_chat_send_followup_empty(monkeypatch):
    chat = Chat(MagicMock())
    mock_resp = MagicMock()
    mock_resp.choices = []
    chat.client.make_request.return_value = mock_resp
    out = chat.send_followup([], "hi")
    assert out == ""


def test_placeholder():
    assert True
