"""
Tests for MCP client functionality
"""

import pytest
import sys
import os
import json
from unittest.mock import patch, MagicMock, AsyncMock

# Ensure src/ is in sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../src')))

# Import the modules being tested
from utils.mcpclient.sessions_manager import MCPSessionManager


@pytest.mark.asyncio
async def test_mcpclient_list_tools():
    """Test listing tools from MCP sessions."""
    # Mock MCP session
    mock_session = AsyncMock()
    mock_session.list_tools = AsyncMock(return_value=['tool1', 'tool2'])
    
    # Create an MCPSessionManager instance
    manager = MCPSessionManager()
    manager._sessions = {'test_server': mock_session}
    
    # Call list_tools
    await manager.list_tools()
    
    # Verify session.list_tools was called
    mock_session.list_tools.assert_called_once()
    
    # Verify tools were added to the manager's tools list
    assert manager.tools == ['tool1', 'tool2']


@pytest.mark.asyncio
async def test_mcpclient_sessions_manager_load():
    """Test loading MCP sessions from a configuration file."""
    # Create a temporary config file
    config_content = {
        'servers': {
            'test_server': {
                'url': 'https://example.com',
                'key': 'test_key'
            }
        }
    }
    
    # Use an in-memory file mock instead of a real file
    with patch('builtins.open', MagicMock()), \
         patch('json.load', return_value=config_content), \
         patch('utils.mcpclient.session.MCPSession', return_value=AsyncMock()):
        
        # Create an MCPSessionManager instance
        manager = MCPSessionManager()
        
        # Call load_mcp_sessions with the mock config path
        result = await manager.load_mcp_sessions('mock_config.json')
        
        # Verify sessions were created successfully
        assert result is True
        assert 'test_server' in manager._sessions


@pytest.mark.asyncio
async def test_mcpclient_sessions_manager_load_file_not_found():
    """Test loading MCP sessions when config file doesn't exist."""
    # Mock open to raise FileNotFoundError
    with patch('builtins.open', side_effect=FileNotFoundError()), \
         patch('builtins.print') as mock_print:
        
        # Create an MCPSessionManager instance
        manager = MCPSessionManager()
        
        # Call load_mcp_sessions with a non-existent config path
        result = await manager.load_mcp_sessions('nonexistent_config.json')
        
        # Verify result indicates failure - implementation returns None on error
        assert result is None
        assert len(manager._sessions) == 0
        mock_print.assert_called_with(f"Configuration file not found: nonexistent_config.json")


@pytest.mark.asyncio
async def test_mcpclient_sessions_manager_list_tools():
    """Test that list_tools calls list_tools on each session."""
    # Create mock sessions
    mock_session1 = AsyncMock()
    mock_session1.list_tools = AsyncMock(return_value=['tool1'])
    
    mock_session2 = AsyncMock()
    mock_session2.list_tools = AsyncMock(return_value=['tool2'])
    
    # Create an MCPSessionManager instance
    manager = MCPSessionManager()
    manager._sessions = {
        'server1': mock_session1,
        'server2': mock_session2
    }
    
    # Call list_tools
    await manager.list_tools()
    
    # Verify list_tools was called on each session
    mock_session1.list_tools.assert_called_once()
    mock_session2.list_tools.assert_called_once()
    
    # Verify tools from both sessions were combined
    assert len(manager.tools) == 2
    assert 'tool1' in manager.tools
    assert 'tool2' in manager.tools


@pytest.mark.asyncio
async def test_mcpclient_sessions_manager_list_tools_wrong_format():
    """Test handling of invalid tool format from sessions."""
    # Create a mock session returning invalid tool format
    mock_session = AsyncMock()
    mock_session.list_tools = AsyncMock(return_value=123)  # Not a list
    
    # Create an MCPSessionManager instance
    manager = MCPSessionManager()
    manager._sessions = {'server': mock_session}
    
    # Expect error handled gracefully
    with patch('builtins.print') as mock_print:
        await manager.list_tools()
    
    # Verify list_tools was called
    mock_session.list_tools.assert_called_once()
    
    # The manager should have an empty tools list
    # Since the invalid response shouldn't be added
    assert manager.tools == []


@pytest.mark.asyncio
async def test_mcpclient_sessions_manager_discovery():
    """Test the discovery method of MCPSessionManager."""
    # Create a manager instance
    manager = MCPSessionManager()
    
    # Mock the required methods
    manager.load_mcp_sessions = AsyncMock(return_value=True)
    manager.list_tools = AsyncMock()
    
    # Call discovery
    with patch('builtins.print') as mock_print:
        await manager.discovery("mock_config.json")
    
    # Verify methods were called
    manager.load_mcp_sessions.assert_called_once_with("mock_config.json")
    manager.list_tools.assert_called_once()
    
    # Test with load_mcp_sessions returning None (error case)
    manager.load_mcp_sessions.reset_mock()
    manager.list_tools.reset_mock()
    manager.load_mcp_sessions.return_value = None
    
    # Call discovery again
    with patch('builtins.print') as mock_print:
        await manager.discovery("mock_config.json")
    
    # Verify load_mcp_sessions was called but not list_tools
    manager.load_mcp_sessions.assert_called_once_with("mock_config.json")
    manager.list_tools.assert_not_called()
    mock_print.assert_any_call("No valid MCP sessions found in configuration")


def test_mcpclient_sessions_manager_properties():
    """Test the properties of MCPSessionManager."""
    # Create a manager instance
    manager = MCPSessionManager()
    
    # Set some values
    manager._sessions = {'test': 'session'}
    manager._tools = ['tool1', 'tool2']
    
    # Verify properties return the correct values
    assert manager.sessions == {'test': 'session'}
    assert manager.tools == ['tool1', 'tool2']
