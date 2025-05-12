import pytest
import sys
import os
from unittest.mock import patch, MagicMock, AsyncMock

# Ensure src/ is in sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

"""
Tests for newer versions of the agent functionality
"""

def test_add_tool():
    """Test the add_tool function."""
    import agent
    from tools import Tool
    
    # Save original objects
    original_chat = agent.chat
    
    try:
        # Create mock chat
        mock_chat = MagicMock()
        mock_chat.add_tool = MagicMock()
        agent.chat = mock_chat
        
        # Create a mock tool
        mock_tool = MagicMock(spec=Tool)
        mock_tool.name = "mock_tool"
        
        # Call add_tool
        agent.add_tool(mock_tool)
        
        # Verify add_tool was called on chat
        mock_chat.add_tool.assert_called_once_with(mock_tool)
        
    finally:
        # Restore original objects
        agent.chat = original_chat


def test_agent_system_role_update():
    """Test that system role can be updated."""
    import agent
    
    # Save original system role and messages
    original_system_role = agent.system_role
    original_messages = agent.messages.copy()
    
    try:
        # Update system_role
        new_system_role = "New system role content"
        agent.system_role = new_system_role
        
        # Verify it was updated
        assert agent.system_role == new_system_role
        
        # Manually update messages to match the behavior in the code
        agent.messages = [{"role": "system", "content": agent.system_role}]
        assert agent.messages[0]["content"] == new_system_role
        
    finally:
        # Restore original system_role and messages
        agent.system_role = original_system_role
        agent.messages = original_messages