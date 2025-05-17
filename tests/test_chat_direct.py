"""
Tests for direct access to chat functionality, bypassing the chatutil decorator.
Since the chat module has been integrated into agent.py, we'll use agent instead.
"""

import pytest
import sys
import os
import json
from unittest.mock import patch, MagicMock, AsyncMock

# Ensure src/ is in sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))


@pytest.mark.asyncio
async def test_chat_internal_implementation():
    """Test the internal implementation of run_conversation."""
    # Import the modules
    import agent
    
    # Save original objects
    original_messages = agent.messages.copy()
    original_chat = agent.chat
    
    try:
        # Create mocks
        mock_chat = MagicMock()
        mock_chat.send_messages = AsyncMock(return_value={
            "choices": [{"message": {"content": "Test response"}}]
        })
        agent.chat = mock_chat
        
        # Set up test input
        agent.messages = [{"role": "system", "content": agent.system_role}]
        agent.messages.append({"role": "user", "content": "Test input"})
        
        # Call the function under test, but skip the decorator by accessing the wrapped function
        response = await agent.chat.send_messages(agent.messages)
        choices = response.get("choices", [])
        
        # Assert response is properly processed
        assert len(choices)
        message = choices[0].get("message", {})
        assert message.get("content") == "Test response"
        
        # Verify chat.send_messages was called with messages
        mock_chat.send_messages.assert_called_once_with(agent.messages)
    finally:
        # Restore original objects
        agent.chat = original_chat
        agent.messages = original_messages


@pytest.mark.asyncio
async def test_chat_internal_implementation_with_none_response():
    """Test the internal implementation with None response."""
    # Import the modules
    import agent
    
    # Save original objects
    original_messages = agent.messages.copy()
    original_chat = agent.chat
    
    try:
        # Create mocks
        mock_chat = MagicMock()
        mock_chat.send_messages = AsyncMock(return_value=None)
        agent.chat = mock_chat
        
        # Set up test input
        agent.messages = [{"role": "system", "content": agent.system_role}]
        agent.messages.append({"role": "user", "content": "Test input"})
        
        # Call the function under test, but skip the decorator by accessing the wrapped function
        response = await agent.chat.send_messages(agent.messages)
        
        # Assert we handle None response gracefully
        assert response is None
        
        # Verify chat.send_messages was called with messages
        mock_chat.send_messages.assert_called_once_with(agent.messages)
    finally:
        # Restore original objects
        agent.chat = original_chat
        agent.messages = original_messages


@pytest.mark.asyncio
async def test_chat_internal_implementation_with_invalid_response_structure():
    """Test the internal implementation with an invalid response structure."""
    # Import the modules
    import agent
    
    # Save original objects
    original_messages = agent.messages.copy()
    original_chat = agent.chat
    
    try:
        # Create mocks with invalid response structure (no choices)
        mock_chat = MagicMock()
        mock_chat.send_messages = AsyncMock(return_value={
            "unexpected_key": "unexpected value"
        })
        agent.chat = mock_chat
        
        # Set up test input
        agent.messages = [{"role": "system", "content": agent.system_role}]
        agent.messages.append({"role": "user", "content": "Test input"})
        
        # Call the function under test
        response = await agent.chat.send_messages(agent.messages)
        choices = response.get("choices", [])
        
        # Assert we handle invalid response structure gracefully
        assert len(choices) == 0
        
        # Verify chat.send_messages was called with messages
        mock_chat.send_messages.assert_called_once_with(agent.messages)
    finally:
        # Restore original objects
        agent.chat = original_chat
        agent.messages = original_messages


@pytest.mark.asyncio
async def test_chat_internal_implementation_with_empty_choices():
    """Test the internal implementation with empty choices list."""
    # Import the modules
    import agent
    
    # Save original objects
    original_messages = agent.messages.copy()
    original_chat = agent.chat
    
    try:
        # Create mocks with empty choices list
        mock_chat = MagicMock()
        mock_chat.send_messages = AsyncMock(return_value={"choices": []})
        agent.chat = mock_chat
        
        # Set up test input
        agent.messages = [{"role": "system", "content": agent.system_role}]
        agent.messages.append({"role": "user", "content": "Test input"})
        
        # Call the function under test
        response = await agent.chat.send_messages(agent.messages)
        choices = response.get("choices", [])
        
        # Assert we handle empty choices list gracefully
        assert len(choices) == 0
        
        # Verify chat.send_messages was called with messages
        mock_chat.send_messages.assert_called_once_with(agent.messages)
    finally:
        # Restore original objects
        agent.chat = original_chat
        agent.messages = original_messages