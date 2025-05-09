import pytest
from utils.azureopenai.chat import Chat
from unittest.mock import MagicMock
import os


def test_chat_create_env(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "key")
    chat = Chat.create()
    assert isinstance(chat, Chat)


def test_chat_create_no_env(monkeypatch):
    monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError):
        Chat.create()


def test_chat_send_messages(monkeypatch):
    chat = Chat(MagicMock())
    chat.client.make_request.return_value = {"choices": [{"message": {"content": "result"}}]}
    out = chat.send_messages([{"role": "user", "content": "hi"}])
    assert out["choices"][0]["message"]["content"] == "result"
    chat.client.make_request.assert_called()


def test_chat_tools_property():
    chat = Chat(MagicMock(), tool_map={})
    assert isinstance(chat.tools, list)


def test_placeholder():
    assert True
