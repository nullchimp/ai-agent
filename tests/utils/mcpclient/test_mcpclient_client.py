import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import sys
import os
import asyncio

# Ensure src/ is in sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))


def test_mcpclient_run(monkeypatch):
    import utils.mcpclient.client as mcp
    # Patch stdio_client and ClientSession context managers
    mock_read = MagicMock()
    mock_write = MagicMock()
    mock_session = MagicMock()
    mock_session.initialize = AsyncMock()
    mock_session.list_prompts = AsyncMock(return_value=["prompt1"])
    mock_session.get_prompt = AsyncMock(return_value="prompt")
    mock_session.list_resources = AsyncMock(return_value=["res"])
    mock_session.list_tools = AsyncMock(return_value=["tool"])
    mock_session.read_resource = AsyncMock(return_value=("content", "mime"))
    mock_session.call_tool = AsyncMock(return_value="result")
    mock_stdio_client = MagicMock()
    mock_stdio_client.__aenter__ = AsyncMock(return_value=(mock_read, mock_write))
    mock_client_session = MagicMock()
    mock_client_session.__aenter__ = AsyncMock(return_value=mock_session)
    monkeypatch.setattr(mcp, "stdio_client", lambda *a, **kw: mock_stdio_client)
    monkeypatch.setattr(mcp, "ClientSession", lambda *a, **kw: mock_client_session)
    asyncio.run(mcp.run())


def test_handle_sampling_message():
    import utils.mcpclient.client as mcp
    msg = MagicMock()
    result = asyncio.run(mcp.handle_sampling_message(msg))
    assert result.role == "assistant"
    assert result.content.text.startswith("Hello")
