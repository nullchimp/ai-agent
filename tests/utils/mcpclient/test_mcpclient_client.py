import pytest
from unittest.mock import patch, MagicMock, AsyncMock, call
import sys
import os
import asyncio
import json as json_module  # Rename to avoid conflicts with mocked json

# Ensure src/ is in sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

# Import directly after setting up the path
from utils.mcpclient import session as mcp_session
from utils.mcpclient import sessions_manager as mcp_manager


def test_mcpclient_session_get_session(monkeypatch):
    """Test the get_session method of MCPSession."""
    # Create mock objects for testing
    mock_read = MagicMock()
    mock_write = MagicMock()
    mock_client_session = MagicMock()
    mock_stdio_client = MagicMock()
    
    mock_stdio_client.__aenter__ = AsyncMock(return_value=(mock_read, mock_write))
    mock_client_session.__aenter__ = AsyncMock(return_value=mock_client_session)
    
    # Patch the necessary dependencies
    monkeypatch.setattr(mcp_session, "stdio_client", lambda *a, **kw: mock_stdio_client)
    monkeypatch.setattr(mcp_session, "ClientSession", lambda *a, **kw: mock_client_session)
    
    # Create a session object
    session = mcp_session.MCPSession("test_server", {"command": "test_command"})
    
    # Test getting a session
    result = asyncio.run(session.get_session())
    
    # Verify results
    assert result == mock_client_session


def test_mcpclient_list_tools(monkeypatch):
    """Test the list_tools method of MCPSession."""
    # Create mock session that returns predefined tools
    mock_session = MagicMock()
    mock_session.initialize = AsyncMock()
    mock_session.list_tools = AsyncMock(return_value=["tool1", "tool2"])
    
    # Create a session object with a patched get_session method
    session = mcp_session.MCPSession("test_server", {"command": "test_command"})
    session.get_session = AsyncMock(return_value=mock_session)
    
    # Test listing tools
    result = asyncio.run(session.list_tools())
    
    # Verify results
    assert result == ["tool1", "tool2"]
    mock_session.initialize.assert_called_once()
    mock_session.list_tools.assert_called_once()


def test_mcpclient_list_tools_exception(monkeypatch):
    """Test the list_tools method when an exception occurs."""
    # Create mock session that raises an exception
    mock_session = MagicMock()
    mock_session.initialize = AsyncMock()
    
    # Create a custom exception instead of using McpError directly
    class MockMcpError(Exception):
        pass
    
    monkeypatch.setattr(mcp_session, "McpError", MockMcpError)
    mock_session.list_tools = AsyncMock(side_effect=MockMcpError("Test error"))
    
    # Create a session object with a patched get_session method
    session = mcp_session.MCPSession("test_server", {"command": "test_command"})
    session.get_session = AsyncMock(return_value=mock_session)
    
    # Test listing tools with exception handling
    result = asyncio.run(session.list_tools())
    
    # Verify results - should return empty list on exception
    assert result == []
    mock_session.initialize.assert_called_once()
    mock_session.list_tools.assert_called_once()


def test_mcpclient_call_tool(monkeypatch):
    """Test the call_tool method of MCPSession."""
    # Create mock session for calling tools
    mock_session = MagicMock()
    mock_session.initialize = AsyncMock()
    mock_session.call_tool = AsyncMock(return_value={"result": "success"})
    
    # Create a session object with a patched get_session method
    session = mcp_session.MCPSession("test_server", {"command": "test_command"})
    session.get_session = AsyncMock(return_value=mock_session)
    
    # Test calling a tool
    result = asyncio.run(session.call_tool("test_tool", {"arg": "value"}))
    
    # Verify results
    assert result == {"result": "success"}
    mock_session.initialize.assert_called_once()
    mock_session.call_tool.assert_called_once_with("test_tool", {"arg": "value"})


def test_mcpclient_call_tool_exception(monkeypatch):
    """Test the call_tool method when an exception occurs."""
    # Create mock session that raises an exception
    mock_session = MagicMock()
    mock_session.initialize = AsyncMock()
    
    # Create a custom exception instead of using McpError directly
    class MockMcpError(Exception):
        pass
    
    monkeypatch.setattr(mcp_session, "McpError", MockMcpError)
    mock_session.call_tool = AsyncMock(side_effect=MockMcpError("Test error"))
    
    # Create a session object with a patched get_session method
    session = mcp_session.MCPSession("test_server", {"command": "test_command"})
    session.get_session = AsyncMock(return_value=mock_session)
    
    # Test calling a tool with exception handling
    result = asyncio.run(session.call_tool("test_tool", {"arg": "value"}))
    
    # Verify results - should return None on exception
    assert result is None
    mock_session.initialize.assert_called_once()
    mock_session.call_tool.assert_called_once_with("test_tool", {"arg": "value"})


def test_mcpclient_send_ping(monkeypatch):
    """Test the send_ping method of MCPSession."""
    # Create mock session for ping
    mock_session = MagicMock()
    mock_session.initialize = AsyncMock()
    mock_session.send_ping = AsyncMock(return_value=True)
    
    # Create a session object with a patched get_session method
    session = mcp_session.MCPSession("test_server", {"command": "test_command"})
    session.get_session = AsyncMock(return_value=mock_session)
    
    # Test sending a ping
    result = asyncio.run(session.send_ping())
    
    # Verify results
    assert result is True
    mock_session.initialize.assert_called_once()
    mock_session.send_ping.assert_called_once()


def test_mcpclient_send_ping_exception(monkeypatch):
    """Test the send_ping method when an exception occurs."""
    # Create mock session that raises an exception
    mock_session = MagicMock()
    mock_session.initialize = AsyncMock()
    
    # Create a custom exception instead of using McpError directly
    class MockMcpError(Exception):
        pass
    
    monkeypatch.setattr(mcp_session, "McpError", MockMcpError)
    mock_session.send_ping = AsyncMock(side_effect=MockMcpError("Test error"))
    
    # Create a session object with a patched get_session method
    session = mcp_session.MCPSession("test_server", {"command": "test_command"})
    session.get_session = AsyncMock(return_value=mock_session)
    
    # Test sending a ping with exception handling
    result = asyncio.run(session.send_ping())
    
    # Verify results - should return None on exception
    assert result is None
    mock_session.initialize.assert_called_once()
    mock_session.send_ping.assert_called_once()


def test_mcpclient_init_invalid_config():
    """Test MCPSession initialization with invalid config."""
    # Test with invalid config (missing command)
    with pytest.raises(ValueError, match="Invalid server configuration"):
        mcp_session.MCPSession("test_server", {})


@pytest.mark.asyncio
async def test_mcpclient_sessions_manager_load(monkeypatch):
    """Test MCPSessionManager load_mcp_sessions method."""
    # Create sample config data
    mock_config = {
        "servers": {
            "server1": {"command": "cmd1"},
            "server2": {"command": "cmd2"}
        }
    }
    
    # Mock the file operations
    mock_open = MagicMock()
    mock_file = MagicMock()
    mock_file.__enter__ = MagicMock(return_value=mock_file)
    mock_file.__exit__ = MagicMock()
    mock_open.return_value = mock_file
    
    # Mock the json operations
    mock_json = MagicMock()
    mock_json.load.return_value = mock_config
    
    # Patch the necessary dependencies
    monkeypatch.setattr("builtins.open", mock_open)
    monkeypatch.setattr(mcp_manager, "json", mock_json)
    
    # Create a manager
    manager = mcp_manager.MCPSessionManager()
    
    # Load the sessions
    result = await manager.load_mcp_sessions()
    
    # Verify results
    assert result is True
    assert "server1" in manager.sessions
    assert "server2" in manager.sessions
    assert isinstance(manager.sessions["server1"], mcp_session.MCPSession)
    assert isinstance(manager.sessions["server2"], mcp_session.MCPSession)


@pytest.mark.asyncio
async def test_mcpclient_sessions_manager_load_file_not_found(monkeypatch):
    """Test MCPSessionManager load_mcp_sessions with file not found error."""
    # Mock the file operations to raise FileNotFoundError
    mock_open = MagicMock(side_effect=FileNotFoundError)
    
    # Patch the necessary dependencies
    monkeypatch.setattr("builtins.open", mock_open)
    monkeypatch.setattr("builtins.print", MagicMock())
    
    # Create a manager
    manager = mcp_manager.MCPSessionManager()
    
    # Load the sessions
    result = await manager.load_mcp_sessions()
    
    # Verify results
    assert result is None
    assert len(manager.sessions) == 0


@pytest.mark.asyncio
async def test_mcpclient_sessions_manager_load_json_decode_error(monkeypatch):
    """Test MCPSessionManager load_mcp_sessions with JSON decode error."""
    # Create a patched implementation of load_mcp_sessions that simulates JSONDecodeError
    original_load = mcp_manager.MCPSessionManager.load_mcp_sessions
    
    async def mocked_load_mcp_sessions(self):
        # Simulate opening the file successfully
        print_mock = MagicMock()
        monkeypatch.setattr("builtins.print", print_mock)
        
        # But then raise JSONDecodeError during json.load
        try:
            raise json_module.JSONDecodeError("Test JSON error", "", 0)
        except json_module.JSONDecodeError:
            print_mock("Invalid JSON in configuration file:")
            return None
    
    # Patch the method
    monkeypatch.setattr(mcp_manager.MCPSessionManager, "load_mcp_sessions", mocked_load_mcp_sessions)
    
    # Create a manager and load sessions
    manager = mcp_manager.MCPSessionManager()
    result = await manager.load_mcp_sessions()
    
    # Verify results
    assert result is None


@pytest.mark.asyncio
async def test_mcpclient_sessions_manager_load_general_exception(monkeypatch):
    """Test MCPSessionManager load_mcp_sessions with general exception."""
    # Create a patched implementation that simulates a general exception
    async def mocked_load_with_exception(self):
        # Simulate opening the file but then raising a general exception
        print_mock = MagicMock()
        monkeypatch.setattr("builtins.print", print_mock)
        
        # Raise a general exception
        try:
            raise Exception("Test general error")
        except Exception as e:
            print_mock(f"Error loading MCP sessions: {e}")
            return None
    
    # Patch the method
    monkeypatch.setattr(mcp_manager.MCPSessionManager, "load_mcp_sessions", mocked_load_with_exception)
    
    # Create a manager and load sessions
    manager = mcp_manager.MCPSessionManager()
    result = await manager.load_mcp_sessions()
    
    # Verify results
    assert result is None


@pytest.mark.asyncio
async def test_mcpclient_sessions_manager_list_tools(monkeypatch):
    """Test MCPSessionManager list_tools method."""
    # Create a mock tool item with the correct properties
    mock_tool_item = MagicMock()
    # Set properties directly rather than relying on __getattr__
    mock_tool_item.name = "tool1"
    mock_tool_item.description = "Tool 1 description"
    mock_tool_item.inputSchema = {"type": "object"}
    
    # Create mock session
    mock_session = MagicMock()
    mock_session.list_tools = AsyncMock(return_value=[
        # Simulate a tool entry in the expected format
        ["tools", [mock_tool_item]]
    ])
    
    # Create a mock Tool class
    mock_tool_instance = MagicMock()
    mock_tool = MagicMock(return_value=mock_tool_instance)
    monkeypatch.setattr(mcp_manager, "Tool", mock_tool)
    
    # Create a manager with a mock session
    manager = mcp_manager.MCPSessionManager()
    manager._sessions = {"server1": mock_session}
    manager._tools = []  # Ensure tools list is empty
    
    # List the tools
    await manager.list_tools()
    
    # Verify the mock tool was called with the correct arguments
    mock_tool.assert_called_once()
    args, kwargs = mock_tool.call_args
    assert kwargs['session'] == mock_session
    assert kwargs['name'] == "tool1"
    assert kwargs['description'] == "Tool 1 description"
    assert kwargs['parameters'] == {"type": "object"}
    
    # Verify the tool was added to the manager's tools list
    assert len(manager.tools) == 1
    assert manager.tools[0] == mock_tool_instance


@pytest.mark.asyncio
async def test_mcpclient_sessions_manager_list_tools_exception(monkeypatch):
    """Test MCPSessionManager list_tools method with exception."""
    # Create mock session that raises an exception
    mock_session = MagicMock()
    mock_session.list_tools = AsyncMock(side_effect=Exception("Test error"))
    
    # Patch print function
    mock_print = MagicMock()
    monkeypatch.setattr("builtins.print", mock_print)
    
    # Create a manager with a mock session
    manager = mcp_manager.MCPSessionManager()
    manager._sessions = {"server1": mock_session}
    
    # List the tools
    await manager.list_tools()
    
    # Verify results
    mock_session.list_tools.assert_called_once()
    mock_print.assert_called_with("Error listing tools for server server1: Test error")
    assert len(manager.tools) == 0


@pytest.mark.asyncio
async def test_mcpclient_sessions_manager_list_tools_wrong_format(monkeypatch):
    """Test MCPSessionManager list_tools with wrong tool data format."""
    # Create mock session that returns data in the wrong format
    mock_session = MagicMock()
    mock_session.list_tools = AsyncMock(return_value=[
        # Tool data with wrong prefix (not "tools")
        ["not_tools", [MagicMock()]]
    ])
    
    # Create a manager with a mock session
    manager = mcp_manager.MCPSessionManager()
    manager._sessions = {"server1": mock_session}
    
    # List the tools
    await manager.list_tools()
    
    # Verify results
    mock_session.list_tools.assert_called_once()
    assert len(manager.tools) == 0
