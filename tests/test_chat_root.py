import pytest
from unittest.mock import patch, MagicMock
import builtins
import sys
import os

# Ensure src/ is in sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))


def test_placeholder():
    assert True


def test_chat_run_conversation_exit(monkeypatch):
    import chat as chat_mod

    monkeypatch.setattr(builtins, "input", lambda _: "exit")
    monkeypatch.setattr(chat_mod, "chat", MagicMock())
    chat_mod.run_conversation()


def test_chat_run_conversation_flow(monkeypatch):
    import chat as chat_mod

    inputs = iter(["question", "exit"])
    monkeypatch.setattr(builtins, "input", lambda _: next(inputs))
    monkeypatch.setattr(chat_mod, "chat", MagicMock())
    chat_mod.chat.send_prompt.return_value = "response"
    chat_mod.run_conversation()
