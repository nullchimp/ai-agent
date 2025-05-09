import pytest
from unittest.mock import patch, MagicMock
import builtins
import sys
import os

# Ensure src/ is in sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))


def test_agent_process_tool_calls_executes_tool(monkeypatch):
    import agent
    tool_call = {
        "function": {"name": "read_file", "arguments": '{"base_dir": "/tmp", "filename": "foo.txt"}'},
        "id": "abc"
    }
    agent.tool_map = {"read_file": MagicMock(run=MagicMock(return_value={"ok": True}))}
    response = {"tool_calls": [tool_call]}
    results = agent.process_tool_calls(response)
    assert results[0]["tool_call_id"] == "abc"
    assert "output" in results[0]


def test_agent_process_tool_calls_tool_not_found(monkeypatch):
    import agent
    tool_call = {
        "function": {"name": "not_a_tool", "arguments": '{}'},
        "id": "id1"
    }
    agent.tool_map = {}
    response = {"tool_calls": [tool_call]}
    results = agent.process_tool_calls(response)
    assert "error" in results[0]["output"]


def test_agent_run_conversation_exit(monkeypatch):
    import agent
    # Patch input to exit immediately
    monkeypatch.setattr(builtins, "input", lambda _: "exit")
    monkeypatch.setattr(agent, "chat", MagicMock())
    agent.run_conversation()


def test_agent_run_conversation_tool_flow(monkeypatch):
    import agent
    # Simulate a conversation with a tool call and follow-up
    inputs = iter(["question", "exit"])
    monkeypatch.setattr(builtins, "input", lambda _: next(inputs))
    fake_response = {"choices": [{"message": {"content": "answer", "tool_calls": [{"function": {"name": "read_file", "arguments": '{}'}, "id": "id1"}]}}]}
    fake_followup = {"choices": [{"message": {"content": "final"}}]}
    monkeypatch.setattr(agent, "chat", MagicMock())
    agent.chat.send_prompt_with_messages_and_options.side_effect = [fake_response, fake_followup]
    agent.tool_map = {"read_file": MagicMock(run=MagicMock(return_value={"ok": True}))}
    agent.run_conversation()


def test_placeholder():
    assert True
