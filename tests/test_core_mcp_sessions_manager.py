import pytest
from unittest.mock import AsyncMock, Mock, patch, mock_open
import json
from src.core.mcp.sessions_manager import MCPSessionManager


class TestMCPSessionManager:
    @pytest.fixture
    def manager(self):
        return MCPSessionManager()

    @pytest.fixture
    def mock_session(self):
        session = Mock()
        session.name = "test_server"
        session.tools = [Mock(name="test_tool")]
        return session

    @pytest.fixture
    def config_data(self):
        return {
            "servers": {
                "test_server": {
                    "command": "python",
                    "args": ["test_script.py"],
                    "env": {"TEST": "true"}
                },
                "second_server": {
                    "command": "node",
                    "args": ["server.js"]
                }
            }
        }

    @pytest.mark.asyncio
    async def test_discovery_success(self, manager, config_data):
        config_path = "/path/to/config.json"
        
        with patch('builtins.open', mock_open(read_data=json.dumps(config_data))):
            with patch.object(manager, 'load_mcp_sessions', return_value=True) as mock_load:
                with patch.object(manager, 'list_tools') as mock_list_tools:
                    await manager.discovery(config_path)
                    
                    mock_load.assert_called_once_with(config_path)
                    mock_list_tools.assert_called_once()

    @pytest.mark.asyncio
    async def test_discovery_no_sessions(self, manager):
        config_path = "/path/to/config.json"
        
        with patch.object(manager, 'load_mcp_sessions', return_value=None):
            await manager.discovery(config_path)
            
            # Should not crash

    @pytest.mark.asyncio
    async def test_load_mcp_sessions_success(self, manager, config_data):
        config_path = "/path/to/config.json"
        
        with patch('builtins.open', mock_open(read_data=json.dumps(config_data))):
            with patch('src.core.mcp.sessions_manager.mcp.MCPSession') as mock_session_class:
                mock_session1 = Mock()
                mock_session2 = Mock()
                mock_session_class.side_effect = [mock_session1, mock_session2]
                
                result = await manager.load_mcp_sessions(config_path)
                
                assert result is True
                assert len(manager._sessions) == 2
                assert "test_server" in manager._sessions
                assert "second_server" in manager._sessions
                assert manager._sessions["test_server"] == mock_session1
                assert manager._sessions["second_server"] == mock_session2

    @pytest.mark.asyncio
    async def test_load_mcp_sessions_file_not_found(self, manager):
        config_path = "/nonexistent/config.json"
        
        with patch('builtins.open', side_effect=FileNotFoundError()):
            result = await manager.load_mcp_sessions(config_path)
            
            assert result is None
            assert len(manager._sessions) == 0

    @pytest.mark.asyncio
    async def test_load_mcp_sessions_invalid_json(self, manager):
        config_path = "/path/to/config.json"
        
        with patch('builtins.open', mock_open(read_data="invalid json")):
            result = await manager.load_mcp_sessions(config_path)
            
            assert result is None
            assert len(manager._sessions) == 0

    @pytest.mark.asyncio
    async def test_load_mcp_sessions_exception(self, manager, config_data):
        config_path = "/path/to/config.json"
        
        with patch('builtins.open', mock_open(read_data=json.dumps(config_data))):
            with patch('src.core.mcp.sessions_manager.mcp.MCPSession', side_effect=Exception("Session error")):
                result = await manager.load_mcp_sessions(config_path)
                
                assert result is None

    @pytest.mark.asyncio
    async def test_list_tools_success(self, manager):
        mock_session = AsyncMock()
        mock_tool1 = Mock(name="tool1")
        mock_tool2 = Mock(name="tool2")
        mock_session.list_tools.return_value = [mock_tool1, mock_tool2]
        
        manager._sessions["test_server"] = mock_session
        
        await manager.list_tools()
        
        assert len(manager._tools) == 2
        assert mock_tool1 in manager._tools
        assert mock_tool2 in manager._tools

    @pytest.mark.asyncio
    async def test_list_tools_with_exception(self, manager, mock_session):
        mock_session.list_tools.side_effect = Exception("Tool listing error")
        manager._sessions["test_server"] = mock_session
        
        await manager.list_tools()
        
        # Should not crash, tools list should remain empty
        assert len(manager._tools) == 0

    @pytest.mark.asyncio
    async def test_list_tools_empty_sessions(self, manager):
        await manager.list_tools()
        
        assert len(manager._tools) == 0

    @pytest.mark.asyncio
    async def test_list_tools_multiple_sessions(self, manager):
        mock_session1 = AsyncMock()
        mock_session1.list_tools.return_value = [Mock(name="tool1")]
        
        mock_session2 = AsyncMock()
        mock_session2.list_tools.return_value = [Mock(name="tool2"), Mock(name="tool3")]
        
        manager._sessions["server1"] = mock_session1
        manager._sessions["server2"] = mock_session2
        
        await manager.list_tools()
        
        assert len(manager._tools) == 3

    def test_sessions_property(self, manager, mock_session):
        manager._sessions["test_server"] = mock_session
        
        result = manager.sessions
        
        assert result == manager._sessions
        assert "test_server" in result

    def test_tools_property(self, manager):
        mock_tools = [Mock(name="tool1"), Mock(name="tool2")]
        manager._tools = mock_tools
        
        result = manager.tools
        
        assert result == mock_tools

    def test_sessions_property_empty(self, manager):
        result = manager.sessions
        
        assert result == {}

    def test_tools_property_empty(self, manager):
        result = manager.tools
        
        assert result == []
