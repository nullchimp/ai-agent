import pytest
import asyncio
import json
import os
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from contextlib import AsyncExitStack

from src.core.mcp.session import MCPSession
from src.core.mcp.sessions_manager import MCPSessionManager
from src.tools import Tool


class TestMCPSession:
    def test_mcp_session_init_success(self):
        server_config = {
            "command": "python",
            "args": ["-m", "test_server"],
            "env": {"TEST": "value"}
        }
        
        session = MCPSession("test_server", server_config)
        assert session.name == "test_server"
        assert session.server_params.command == "python"
        assert session.server_params.args == ["-m", "test_server"]
        assert session.server_params.env == {"TEST": "value"}

    def test_mcp_session_init_missing_command(self):
        server_config = {
            "args": ["-m", "test_server"]
        }
        
        with pytest.raises(ValueError, match="Invalid server configuration"):
            MCPSession("test_server", server_config)

    def test_mcp_session_init_empty_command(self):
        server_config = {
            "command": None,
            "args": ["-m", "test_server"]
        }
        
        with pytest.raises(ValueError, match="Invalid server configuration"):
            MCPSession("test_server", server_config)

    def test_mcp_session_tools_property(self):
        server_config = {"command": "python"}
        session = MCPSession("test_server", server_config)
        
        # Initially empty
        assert session.tools == []
        
        # After setting _tools
        mock_tool = Mock(spec=Tool)
        session._tools = [mock_tool]
        assert session.tools == [mock_tool]

    @pytest.mark.asyncio
    async def test_get_session_creates_new_session(self):
        server_config = {"command": "python"}
        session = MCPSession("test_server", server_config)
        
        mock_stdio = Mock()
        mock_write = Mock()
        mock_client_session = Mock()
        
        with patch('src.core.mcp.session.stdio_client') as mock_stdio_client, \
             patch('src.core.mcp.session.ClientSession') as mock_client_session_class:
            
            # Mock the async context manager
            mock_stdio_client.return_value.__aenter__ = AsyncMock(return_value=(mock_stdio, mock_write))
            mock_stdio_client.return_value.__aexit__ = AsyncMock(return_value=None)
            
            mock_client_session_class.return_value.__aenter__ = AsyncMock(return_value=mock_client_session)
            mock_client_session_class.return_value.__aexit__ = AsyncMock(return_value=None)
            
            # Mock exit stack
            with patch.object(session.exit_stack, 'enter_async_context') as mock_enter:
                mock_enter.side_effect = [(mock_stdio, mock_write), mock_client_session]
                
                result = await session.get_session()
                
                assert result == mock_client_session
                assert session._session == mock_client_session
                assert mock_enter.call_count == 2

    @pytest.mark.asyncio
    async def test_get_session_returns_existing_session(self):
        server_config = {"command": "python"}
        session = MCPSession("test_server", server_config)
        
        mock_existing_session = Mock()
        session._session = mock_existing_session
        
        result = await session.get_session()
        assert result == mock_existing_session

    @pytest.mark.asyncio
    async def test_list_tools_success(self):
        server_config = {"command": "python"}
        session = MCPSession("test_server", server_config)
        
        mock_session = AsyncMock()
        mock_tool_data = Mock()
        mock_tool_data.name = "test_tool"
        mock_tool_data.description = "Test tool description"
        mock_tool_data.inputSchema = {"type": "object"}
        
        mock_session.list_tools.return_value = [
            ("tools", [mock_tool_data])
        ]
        
        with patch.object(session, 'get_session', return_value=mock_session):
            tools = await session.list_tools()
            
            assert len(tools) == 1
            tool = tools[0]
            assert isinstance(tool, Tool)
            assert tool.name == "test_tool"
            assert tool.description == "Test tool description"
            assert tool.parameters == {"type": "object"}
            
            mock_session.initialize.assert_called_once()
            mock_session.list_tools.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_tools_empty_response(self):
        server_config = {"command": "python"}
        session = MCPSession("test_server", server_config)
        
        mock_session = AsyncMock()
        mock_session.list_tools.return_value = None
        
        with patch.object(session, 'get_session', return_value=mock_session):
            tools = await session.list_tools()
            assert tools == []

    @pytest.mark.asyncio
    async def test_list_tools_no_tools_section(self):
        server_config = {"command": "python"}
        session = MCPSession("test_server", server_config)
        
        mock_session = AsyncMock()
        mock_session.list_tools.return_value = [
            ("other", [])
        ]
        
        with patch.object(session, 'get_session', return_value=mock_session):
            tools = await session.list_tools()
            assert tools == []

    @pytest.mark.asyncio
    async def test_list_tools_mcp_error(self):
        server_config = {"command": "python"}
        session = MCPSession("test_server", server_config)
        
        mock_session = AsyncMock()
        
        with patch('src.core.mcp.session.McpError') as MockMcpError:
            mock_session.initialize.side_effect = MockMcpError("Connection failed")
            
            with patch.object(session, 'get_session', return_value=mock_session):
                tools = await session.list_tools()
                assert tools == []

    @pytest.mark.asyncio
    async def test_call_tool_success(self):
        server_config = {"command": "python"}
        session = MCPSession("test_server", server_config)
        
        mock_session = AsyncMock()
        mock_result = {"success": True, "data": "result"}
        mock_session.call_tool.return_value = mock_result
        
        with patch.object(session, 'get_session', return_value=mock_session):
            result = await session.call_tool("test_tool", {"param": "value"})
            
            assert result == mock_result
            mock_session.initialize.assert_called_once()
            mock_session.call_tool.assert_called_once_with("test_tool", {"param": "value"})

    @pytest.mark.asyncio
    async def test_call_tool_mcp_error(self):
        server_config = {"command": "python"}
        session = MCPSession("test_server", server_config)
        
        mock_session = AsyncMock()
        
        with patch('src.core.mcp.session.McpError') as MockMcpError:
            mock_session.call_tool.side_effect = MockMcpError("Tool call failed")
            
            with patch.object(session, 'get_session', return_value=mock_session):
                result = await session.call_tool("test_tool", {})
                assert result is None

    @pytest.mark.asyncio
    async def test_send_ping_success(self):
        server_config = {"command": "python"}
        session = MCPSession("test_server", server_config)
        
        mock_session = AsyncMock()
        mock_result = {"pong": True}
        mock_session.send_ping.return_value = mock_result
        
        with patch.object(session, 'get_session', return_value=mock_session):
            result = await session.send_ping()
            
            assert result == mock_result
            mock_session.initialize.assert_called_once()
            mock_session.send_ping.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_ping_mcp_error(self):
        server_config = {"command": "python"}
        session = MCPSession("test_server", server_config)
        
        mock_session = AsyncMock()
        
        with patch('src.core.mcp.session.McpError') as MockMcpError:
            mock_session.send_ping.side_effect = MockMcpError("Ping failed")
            
            with patch.object(session, 'get_session', return_value=mock_session):
                result = await session.send_ping()
                assert result is None


class TestMCPSessionManager:
    def test_mcp_session_manager_init(self):
        manager = MCPSessionManager()
        assert manager._sessions == {}
        assert manager._tools == []

    def test_sessions_property(self):
        manager = MCPSessionManager()
        mock_session = Mock()
        manager._sessions["test"] = mock_session
        
        assert manager.sessions == {"test": mock_session}

    def test_tools_property(self):
        manager = MCPSessionManager()
        mock_tool = Mock()
        manager._tools = [mock_tool]
        
        assert manager.tools == [mock_tool]

    @pytest.mark.asyncio
    async def test_load_mcp_sessions_success(self):
        config_data = {
            "servers": {
                "test_server": {
                    "command": "python",
                    "args": ["-m", "test"]
                },
                "another_server": {
                    "command": "node",
                    "args": ["server.js"]
                }
            }
        }
        
        manager = MCPSessionManager()
        
        with patch('builtins.open', mock_open_with_json(config_data)):
            result = await manager.load_mcp_sessions("config.json")
            
            assert result is True
            assert len(manager._sessions) == 2
            assert "test_server" in manager._sessions
            assert "another_server" in manager._sessions

    @pytest.mark.asyncio
    async def test_load_mcp_sessions_file_not_found(self):
        manager = MCPSessionManager()
        
        with patch('builtins.open', side_effect=FileNotFoundError("File not found")):
            with patch('builtins.print') as mock_print:
                result = await manager.load_mcp_sessions("nonexistent.json")
                
                assert result is None
                mock_print.assert_called_with("Configuration file not found: nonexistent.json")

    @pytest.mark.asyncio
    async def test_load_mcp_sessions_invalid_json(self):
        manager = MCPSessionManager()
        
        with patch('builtins.open', mock_open_with_content("invalid json")):
            with patch('builtins.print') as mock_print:
                result = await manager.load_mcp_sessions("config.json")
                
                assert result is None
                mock_print.assert_called_with("Invalid JSON in configuration file: config.json")

    @pytest.mark.asyncio
    async def test_load_mcp_sessions_other_exception(self):
        manager = MCPSessionManager()
        
        with patch('builtins.open', side_effect=PermissionError("Access denied")):
            with patch('builtins.print') as mock_print:
                result = await manager.load_mcp_sessions("config.json")
                
                assert result is None
                mock_print.assert_called_with("Error loading MCP sessions: Access denied")

    @pytest.mark.asyncio
    async def test_list_tools_success(self):
        manager = MCPSessionManager()
        
        mock_session1 = AsyncMock()
        mock_session2 = AsyncMock()
        
        mock_tool1 = Mock(spec=Tool)
        mock_tool2 = Mock(spec=Tool)
        mock_tool3 = Mock(spec=Tool)
        
        mock_session1.list_tools.return_value = [mock_tool1, mock_tool2]
        mock_session2.list_tools.return_value = [mock_tool3]
        
        manager._sessions = {
            "server1": mock_session1,
            "server2": mock_session2
        }
        
        await manager.list_tools()
        
        assert len(manager._tools) == 3
        assert mock_tool1 in manager._tools
        assert mock_tool2 in manager._tools
        assert mock_tool3 in manager._tools

    @pytest.mark.asyncio
    async def test_list_tools_with_exception(self):
        manager = MCPSessionManager()
        
        mock_session1 = AsyncMock()
        mock_session2 = AsyncMock()
        
        mock_tool1 = Mock(spec=Tool)
        
        mock_session1.list_tools.return_value = [mock_tool1]
        mock_session2.list_tools.side_effect = Exception("Connection failed")
        
        manager._sessions = {
            "server1": mock_session1,
            "server2": mock_session2
        }
        
        with patch('builtins.print') as mock_print:
            await manager.list_tools()
            
            assert len(manager._tools) == 1
            assert mock_tool1 in manager._tools
            mock_print.assert_called_with("Error listing tools for server server2: Connection failed")

    @pytest.mark.asyncio
    async def test_discovery_success(self):
        config_data = {
            "servers": {
                "test_server": {
                    "command": "python",
                    "args": ["-m", "test"]
                }
            }
        }
        
        manager = MCPSessionManager()
        
        with patch('builtins.open', mock_open_with_json(config_data)), \
             patch.object(manager, 'list_tools', new_callable=AsyncMock) as mock_list_tools:
            
            await manager.discovery("config.json")
            
            assert len(manager._sessions) == 1
            mock_list_tools.assert_called_once()

    @pytest.mark.asyncio
    async def test_discovery_failed_load(self):
        manager = MCPSessionManager()
        
        with patch.object(manager, 'load_mcp_sessions', return_value=None), \
             patch('builtins.print') as mock_print:
            
            await manager.discovery("config.json")
            
            mock_print.assert_called_with("No valid MCP sessions found in configuration")


def mock_open_with_json(data):
    """Helper to mock open with JSON data"""
    return patch('builtins.open', new_callable=lambda: Mock(
        return_value=Mock(
            __enter__=Mock(return_value=Mock(read=Mock(return_value=json.dumps(data)))),
            __exit__=Mock(return_value=None)
        )
    ))


def mock_open_with_content(content):
    """Helper to mock open with string content"""
    return patch('builtins.open', new_callable=lambda: Mock(
        return_value=Mock(
            __enter__=Mock(return_value=Mock(read=Mock(return_value=content))),
            __exit__=Mock(return_value=None)
        )
    ))
