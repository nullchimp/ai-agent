"""
Tests for main functionality
"""

import asyncio
import os
import sys
from unittest.mock import patch, MagicMock, AsyncMock

import pytest

# Ensure src/ is in sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))


@pytest.mark.asyncio
async def test_mcp_discovery_success():
    """Test mcp_discovery with successful tools discovery"""
    import main
    
    # Mock the sessions_manager
    original_manager = main.session_manager
    
    try:
        mock_manager = MagicMock()
        mock_manager.discovery = AsyncMock(return_value=True)
        mock_manager.tools = [MagicMock(), MagicMock()]
        main.session_manager = mock_manager
        
        # Mock the add_tool function
        mock_add_tool = MagicMock()
        with patch('agent.add_tool', mock_add_tool):
            # Call the tested function
            await main.main()
            
            # Verify that discovery was called
            mock_manager.discovery.assert_called_once()
            
            # Verify that add_tool was called for each tool
            assert mock_add_tool.call_count == 2
            
    finally:
        # Restore original manager
        main.session_manager = original_manager


@pytest.mark.asyncio
async def test_mcp_discovery_no_sessions():
    """Test mcp_discovery with no sessions found"""
    import main
    
    # Mock the sessions_manager
    original_manager = main.session_manager
    
    try:
        mock_manager = MagicMock()
        mock_manager.discovery = AsyncMock(return_value=False)
        mock_manager.tools = []
        main.session_manager = mock_manager
        
        # Mock the add_tool function to verify it's not called
        mock_add_tool = MagicMock()
        
        # Mock agent_task to prevent actual execution
        mock_agent_task = AsyncMock()
        
        with patch('agent.add_tool', mock_add_tool), patch('main.agent_task', mock_agent_task):
            # Call the tested function
            await main.main()
            
            # Verify that discovery was called
            mock_manager.discovery.assert_called_once()
            
            # Verify that add_tool wasn't called (no tools)
            mock_add_tool.assert_not_called()
            
            # Verify that agent_task was called
            mock_agent_task.assert_called_once()
            
    finally:
        # Restore original manager
        main.session_manager = original_manager


@pytest.mark.asyncio
async def test_main_function():
    """Test the main function entry point"""
    import main
    
    # Save original functions
    original_agent_task = main.agent_task
    original_session_manager = main.session_manager
    
    try:
        # Create mocks
        mock_agent_task = AsyncMock()
        mock_session_manager = MagicMock()
        mock_session_manager.discovery = AsyncMock(return_value=True)
        mock_session_manager.tools = []
        
        # Replace with mocks
        main.agent_task = mock_agent_task
        main.session_manager = mock_session_manager
        
        # Call the main function
        await main.main()
        
        # Verify session_manager.discovery was called
        mock_session_manager.discovery.assert_called_once()
        
        # Verify agent_task was called
        mock_agent_task.assert_called_once()
        
    finally:
        # Restore original functions
        main.agent_task = original_agent_task
        main.session_manager = original_session_manager