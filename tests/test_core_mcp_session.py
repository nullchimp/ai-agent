import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from src.core.mcp.session import MCPSession


class TestMCPSession:
    @pytest.fixture
    def server_config(self):
        return {
            "command": "python",
            "args": ["test_script.py"],
            "env": {"TEST": "true"}
        }

    @pytest.fixture
    def session(self, server_config):
        return MCPSession("test_server", server_config)

    def test_init_success(self, session, server_config):
        assert session.name == "test_server"
        assert session._session is None
        assert session._tools == []

    def test_init_missing_command(self):
        server_config = {"args": ["test_script.py"]}
        with pytest.raises(ValueError, match="Invalid server configuration"):
            MCPSession("test_server", server_config)

    @pytest.mark.asyncio
    async def test_list_tools_success(self, session):
        mock_session = AsyncMock()
        mock_tool = Mock()
        mock_tool.name = "test_tool"
        mock_tool.description = "Test tool"
        mock_tool.inputSchema = {"type": "object"}
        
        mock_session.list_tools.return_value = [("tools", [mock_tool])]
        
        with patch.object(session, 'get_session', return_value=mock_session):
            with patch('src.core.mcp.session.Tool') as mock_tool_class:
                mock_tool_instance = Mock()
                mock_tool_class.return_value = mock_tool_instance
                
                result = await session.list_tools()
                
                mock_session.initialize.assert_called_once()
                mock_session.list_tools.assert_called_once()
                mock_tool_class.assert_called_once_with(
                    session=session,
                    name="test_tool",
                    description="Test tool",
                    parameters={"type": "object"}
                )
                assert result == [mock_tool_instance]

    @pytest.mark.asyncio
    async def test_list_tools_empty_response(self, session):
        mock_session = AsyncMock()
        mock_session.list_tools.return_value = None
        
        with patch.object(session, 'get_session', return_value=mock_session):
            result = await session.list_tools()
            
            assert result == []

    @pytest.mark.asyncio
    async def test_list_tools_error(self, session):
        from mcp.shared.exceptions import McpError
        from mcp.types import ErrorData

        mock_session = AsyncMock()
        error_data = ErrorData(code=-1, message="Connection error")
        mock_session.initialize.side_effect = McpError(error_data)
        
        with patch.object(session, 'get_session', return_value=mock_session):
            result = await session.list_tools()
            
            assert result == []

    def test_tools_property(self, session):
        test_tools = [Mock(), Mock()]
        session._tools = test_tools
        
        assert session.tools == test_tools

    @pytest.mark.asyncio
    async def test_call_tool_success(self, session):
        mock_session = AsyncMock()
        mock_result = {"content": [{"type": "text", "text": "success"}]}
        mock_session.call_tool.return_value = mock_result
        
        with patch.object(session, 'get_session', return_value=mock_session):
            result = await session.call_tool("test_tool", {"param": "value"})
            
            mock_session.initialize.assert_called_once()
            mock_session.call_tool.assert_called_once_with("test_tool", {"param": "value"})
            assert result == mock_result

    @pytest.mark.asyncio
    async def test_call_tool_error(self, session):
        from mcp.shared.exceptions import McpError
        from mcp.types import ErrorData
        
        mock_session = AsyncMock()
        error_data = ErrorData(code=-1, message="Tool error")
        mock_session.call_tool.side_effect = McpError(error_data)
        
        with patch.object(session, 'get_session', return_value=mock_session):
            result = await session.call_tool("test_tool", {})
            
            assert result is None

    @pytest.mark.asyncio
    async def test_send_ping_success(self, session):
        mock_session = AsyncMock()
        mock_session.send_ping.return_value = {"pong": True}
        
        with patch.object(session, 'get_session', return_value=mock_session):
            result = await session.send_ping()
            
            mock_session.initialize.assert_called_once()
            mock_session.send_ping.assert_called_once()
            assert result == {"pong": True}

    @pytest.mark.asyncio
    async def test_send_ping_error(self, session):
        from mcp.shared.exceptions import McpError
        from mcp.types import ErrorData
        
        mock_session = AsyncMock()
        error_data = ErrorData(code=-1, message="Ping error")
        mock_session.send_ping.side_effect = McpError(error_data)
        
        with patch.object(session, 'get_session', return_value=mock_session):
            result = await session.send_ping()
            
            assert result is None

    @pytest.mark.asyncio
    async def test_get_session_creates_new(self, session):
        mock_stdio = Mock()
        mock_write = Mock()
        mock_client_session = Mock()
        
        with patch('src.core.mcp.session.stdio_client', return_value=(mock_stdio, mock_write)) as mock_stdio_client:
            with patch('src.core.mcp.session.ClientSession', return_value=mock_client_session) as mock_client_session_class:
                with patch.object(session.exit_stack, 'enter_async_context') as mock_enter:
                    mock_enter.side_effect = [(mock_stdio, mock_write), mock_client_session]
                    
                    result = await session.get_session()
                    
                    assert result == mock_client_session
                    assert session._session == mock_client_session

    @pytest.mark.asyncio
    async def test_get_session_returns_existing(self, session):
        existing_session = Mock()
        session._session = existing_session
        
        result = await session.get_session()
        
        assert result == existing_session
