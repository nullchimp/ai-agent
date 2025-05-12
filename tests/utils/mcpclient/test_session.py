import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json
from utils.mcpclient.session import MCPSession
from mcp.shared.exceptions import McpError

@pytest.fixture
def mock_server_config():
    return {
        "command": "test_command",
        "args": ["--test"],
        "env": {"TEST_ENV": "value"}
    }

def test_init_valid_config(mock_server_config):
    """Test initialization with valid server configuration"""
    session = MCPSession("test_server", mock_server_config)
    assert session.name == "test_server"
    assert session.server_params.command == "test_command"
    assert session.server_params.args == ["--test"]
    assert session.server_params.env == {"TEST_ENV": "value"}
    assert session._session is None
    assert session._tools == []

def test_init_invalid_config():
    """Test initialization with invalid server configuration"""
    invalid_config = {}
    with pytest.raises(ValueError, match="Invalid server configuration"):
        MCPSession("test_server", invalid_config)

@pytest.mark.asyncio
async def test_list_tools_success(mock_server_config):
    """Test successful tool listing"""
    session = MCPSession("test_server", mock_server_config)
    
    # Mock the session and response
    mock_client_session = AsyncMock()
    mock_client_session.initialize = AsyncMock()
    mock_client_session.list_tools = AsyncMock()
    
    # Set up the mock tool data - create a proper mock that will handle attributes correctly
    mock_tool = MagicMock()
    mock_tool.name = "test_tool"  # Explicitly set the name attribute
    mock_tool.description = "Test tool"
    mock_tool.inputSchema = {"type": "object"}
    
    tool_data = [("tools", [mock_tool])]
    mock_client_session.list_tools.return_value = tool_data
    
    # Patch the get_session method to return our mock
    with patch.object(session, "get_session", return_value=mock_client_session):
        tools = await session.list_tools()
        
        # Verify the calls
        mock_client_session.initialize.assert_called_once()
        mock_client_session.list_tools.assert_called_once()
        
        # Verify the tool was properly created
        assert len(tools) == 1
        assert isinstance(tools[0].name, str)  # Check that name is a string
        assert tools[0].name == "test_tool"

@pytest.mark.asyncio
async def test_list_tools_empty(mock_server_config):
    """Test empty tool listing"""
    session = MCPSession("test_server", mock_server_config)
    
    # Mock the session and response
    mock_client_session = AsyncMock()
    mock_client_session.initialize = AsyncMock()
    mock_client_session.list_tools = AsyncMock(return_value=[])
    
    # Patch the get_session method to return our mock
    with patch.object(session, "get_session", return_value=mock_client_session):
        tools = await session.list_tools()
        
        # Verify the calls
        mock_client_session.initialize.assert_called_once()
        mock_client_session.list_tools.assert_called_once()
        
        # Verify no tools were created
        assert tools == []

@pytest.mark.asyncio
async def test_list_tools_error(mock_server_config):
    """Test error handling during tool listing"""
    session = MCPSession("test_server", mock_server_config)
    
    # Mock the session and response
    mock_client_session = AsyncMock()
    mock_client_session.initialize = AsyncMock()
    
    # Create a proper McpError mock with a message attribute
    mock_error = MagicMock()
    mock_error.message = "Test error"
    mock_client_session.list_tools = AsyncMock(side_effect=McpError(mock_error))
    
    # Patch the get_session method to return our mock
    with patch.object(session, "get_session", return_value=mock_client_session):
        tools = await session.list_tools()
        
        # Verify the calls
        mock_client_session.initialize.assert_called_once()
        mock_client_session.list_tools.assert_called_once()
        
        # Verify empty list is returned on error
        assert tools == []

@pytest.mark.asyncio
async def test_call_tool_success(mock_server_config):
    """Test successful tool call"""
    session = MCPSession("test_server", mock_server_config)
    
    # Mock the session and response
    mock_client_session = AsyncMock()
    mock_client_session.initialize = AsyncMock()
    mock_client_session.call_tool = AsyncMock(return_value={"result": "success"})
    
    # Patch the get_session method to return our mock
    with patch.object(session, "get_session", return_value=mock_client_session):
        result = await session.call_tool("test_tool", {"param": "value"})
        
        # Verify the calls
        mock_client_session.initialize.assert_called_once()
        mock_client_session.call_tool.assert_called_once_with("test_tool", {"param": "value"})
        
        # Verify the result
        assert result == {"result": "success"}

@pytest.mark.asyncio
async def test_call_tool_error(mock_server_config):
    """Test error handling during tool call"""
    session = MCPSession("test_server", mock_server_config)
    
    # Mock the session and response
    mock_client_session = AsyncMock()
    mock_client_session.initialize = AsyncMock()
    
    # Create a proper McpError mock with a message attribute
    mock_error = MagicMock()
    mock_error.message = "Test error"
    mock_client_session.call_tool = AsyncMock(side_effect=McpError(mock_error))
    
    # Patch the get_session method to return our mock
    with patch.object(session, "get_session", return_value=mock_client_session):
        result = await session.call_tool("test_tool", {"param": "value"})
        
        # Verify the calls
        mock_client_session.initialize.assert_called_once()
        mock_client_session.call_tool.assert_called_once_with("test_tool", {"param": "value"})
        
        # Verify None is returned on error
        assert result is None

@pytest.mark.asyncio
async def test_send_ping_success(mock_server_config):
    """Test successful ping"""
    session = MCPSession("test_server", mock_server_config)
    
    # Mock the session and response
    mock_client_session = AsyncMock()
    mock_client_session.initialize = AsyncMock()
    mock_client_session.send_ping = AsyncMock(return_value={"pong": True})
    
    # Patch the get_session method to return our mock
    with patch.object(session, "get_session", return_value=mock_client_session):
        result = await session.send_ping()
        
        # Verify the calls
        mock_client_session.initialize.assert_called_once()
        mock_client_session.send_ping.assert_called_once()
        
        # Verify the result
        assert result == {"pong": True}

@pytest.mark.asyncio
async def test_send_ping_error(mock_server_config):
    """Test error handling during ping"""
    session = MCPSession("test_server", mock_server_config)
    
    # Mock the session and response
    mock_client_session = AsyncMock()
    mock_client_session.initialize = AsyncMock()
    
    # Create a proper McpError mock with a message attribute
    mock_error = MagicMock()
    mock_error.message = "Test error"
    mock_client_session.send_ping = AsyncMock(side_effect=McpError(mock_error))
    
    # Patch the get_session method to return our mock
    with patch.object(session, "get_session", return_value=mock_client_session):
        result = await session.send_ping()
        
        # Verify the calls
        mock_client_session.initialize.assert_called_once()
        mock_client_session.send_ping.assert_called_once()
        
        # Verify None is returned on error
        assert result is None

@pytest.mark.asyncio
async def test_get_session_create_new(mock_server_config):
    """Test creating a new session"""
    session = MCPSession("test_server", mock_server_config)
    
    # Mock the async context managers
    mock_stdio = AsyncMock()
    mock_write = MagicMock()
    mock_client_session = AsyncMock()
    
    # Patch the context managers
    with patch("utils.mcpclient.session.stdio_client", return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=(mock_stdio, mock_write))
        )), \
         patch("utils.mcpclient.session.ClientSession", return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_client_session)
        )):
        
        result = await session.get_session()
        
        # Verify the session was created and cached
        assert result is mock_client_session
        assert session._session is mock_client_session
        
        # Call again to test caching
        second_result = await session.get_session()
        assert second_result is mock_client_session  # Should return the cached session