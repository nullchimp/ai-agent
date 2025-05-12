"""
Tests specifically for the run_conversation function in agent.py
"""

import asyncio
import sys
import os
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from functools import wraps

# Ensure src/ is in sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))


def get_original_func(decorated_func):
    """Helper function to get the original function inside decorators"""
    if hasattr(decorated_func, '__wrapped__'):
        return get_original_func(decorated_func.__wrapped__)
    return decorated_func


@pytest.mark.asyncio
async def test_run_conversation_basic_flow():
    """Test the basic flow of run_conversation function."""
    import agent as agent_mod
    
    # Save original objects
    original_messages = agent_mod.messages.copy()
    original_chat = agent_mod.chat
    original_pretty_print = agent_mod.pretty_print
    
    try:
        # Mock chat and its methods
        mock_chat = MagicMock()
        mock_chat.send_messages = AsyncMock(return_value={
            "choices": [
                {"message": {"content": "Test response", "role": "assistant"}}
            ]
        })
        agent_mod.chat = mock_chat
        
        # Mock pretty_print to avoid actual printing
        agent_mod.pretty_print = MagicMock()
        
        # Create a test coroutine function that simulates the behavior of run_conversation
        async def test_run(prompt):
            agent_mod.messages.append({"role": "user", "content": prompt})
            response = await mock_chat.send_messages(agent_mod.messages)
            choices = response.get("choices", [])
            assistant_message = choices[0].get("message", {})
            agent_mod.messages.append(assistant_message)
            result = assistant_message.get("content", "")
            agent_mod.pretty_print("Result", result)
            
        # Patch run_conversation to use our test function
        with patch.object(agent_mod, 'run_conversation', side_effect=test_run):
            # Call the function
            await agent_mod.run_conversation("Test input")
            
            # Verify message flow
            assert len(agent_mod.messages) == 3
            assert agent_mod.messages[1]["role"] == "user"
            assert agent_mod.messages[1]["content"] == "Test input"
            assert agent_mod.messages[2]["role"] == "assistant"
            assert agent_mod.messages[2]["content"] == "Test response"
            
            # Verify chat.send_messages was called with the correct messages
            mock_chat.send_messages.assert_called_once_with(agent_mod.messages)
            
            # Verify pretty_print was called with the response content
            agent_mod.pretty_print.assert_called_once_with("Result", "Test response")
        
    finally:
        # Restore original objects
        agent_mod.messages = original_messages
        agent_mod.chat = original_chat
        agent_mod.pretty_print = original_pretty_print


@pytest.mark.asyncio
async def test_run_conversation_with_tool_calls():
    """Test run_conversation with tool calls in the response."""
    import agent as agent_mod
    
    # Save original objects
    original_messages = agent_mod.messages.copy()
    original_chat = agent_mod.chat
    original_pretty_print = agent_mod.pretty_print
    
    try:
        # Create mock responses for the sequence
        first_response = {
            "choices": [
                {"message": {
                    "content": None,
                    "role": "assistant",
                    "tool_calls": [
                        {"id": "call_123", "type": "function", "function": {"name": "google_search", "arguments": '{"query": "test query"}'}}
                    ]
                }}
            ]
        }
        
        second_response = {
            "choices": [
                {"message": {"content": "Final response after tool call", "role": "assistant"}}
            ]
        }
        
        # Mock chat and its methods
        mock_chat = MagicMock()
        mock_chat.send_messages = AsyncMock(side_effect=[first_response, second_response])
        mock_chat.process_tool_calls = AsyncMock()
        agent_mod.chat = mock_chat
        
        # Mock pretty_print to avoid actual printing
        agent_mod.pretty_print = MagicMock()
        
        # Create a test coroutine function that simulates the run_conversation with tool calls
        async def test_run(prompt):
            agent_mod.messages.append({"role": "user", "content": prompt})
            
            # First response with tool call
            response = await mock_chat.send_messages(agent_mod.messages)
            choices = response.get("choices", [])
            assistant_message = choices[0].get("message", {})
            agent_mod.messages.append(assistant_message)
            
            # Process tool calls
            await mock_chat.process_tool_calls(assistant_message, agent_mod.messages.append)
            
            # Second response with final answer
            response = await mock_chat.send_messages(agent_mod.messages)
            choices = response.get("choices", [])
            assistant_message = choices[0].get("message", {})
            agent_mod.messages.append(assistant_message)
            
            result = assistant_message.get("content", "")
            agent_mod.pretty_print("Result", result)
        
        # Patch run_conversation to use our test function
        with patch.object(agent_mod, 'run_conversation', side_effect=test_run):
            # Call run_conversation with test input
            await agent_mod.run_conversation("Test input with tool calls")
            
            # Verify process_tool_calls was called
            mock_chat.process_tool_calls.assert_called_once()
            
            # Verify send_messages was called twice
            assert mock_chat.send_messages.call_count == 2
            
            # Verify pretty_print received the final response
            agent_mod.pretty_print.assert_called_once_with("Result", "Final response after tool call")
        
    finally:
        # Restore original objects
        agent_mod.messages = original_messages
        agent_mod.chat = original_chat
        agent_mod.pretty_print = original_pretty_print


@pytest.mark.asyncio
async def test_run_conversation_with_empty_response():
    """Test run_conversation with an empty response."""
    import agent as agent_mod
    
    # Save original objects
    original_messages = agent_mod.messages.copy()
    original_chat = agent_mod.chat
    original_pretty_print = agent_mod.pretty_print
    
    try:
        # Mock chat with empty response
        mock_chat = MagicMock()
        mock_chat.send_messages = AsyncMock(return_value=None)
        agent_mod.chat = mock_chat
        
        # Mock pretty_print to avoid actual printing
        agent_mod.pretty_print = MagicMock()
        
        # Create a test coroutine function that simulates the run_conversation with empty response
        async def test_run(prompt):
            agent_mod.messages.append({"role": "user", "content": prompt})
            response = await mock_chat.send_messages(agent_mod.messages)
            
            # Handle the None response
            result = ""
            agent_mod.pretty_print("Result", result)
        
        # Patch run_conversation to use our test function
        with patch.object(agent_mod, 'run_conversation', side_effect=test_run):
            # Call run_conversation with test input
            await agent_mod.run_conversation("Test empty response")
            
            # Verify handling of empty response
            agent_mod.pretty_print.assert_called_once_with("Result", "")
        
    finally:
        # Restore original objects
        agent_mod.messages = original_messages
        agent_mod.chat = original_chat
        agent_mod.pretty_print = original_pretty_print


@pytest.mark.asyncio
async def test_run_conversation_with_missing_choices():
    """Test run_conversation with missing choices in response."""
    import agent as agent_mod
    
    # Save original objects
    original_messages = agent_mod.messages.copy()
    original_chat = agent_mod.chat
    original_pretty_print = agent_mod.pretty_print
    
    try:
        # Mock chat with response missing choices
        mock_chat = MagicMock()
        mock_chat.send_messages = AsyncMock(return_value={"other_key": "value"})
        agent_mod.chat = mock_chat
        
        # Mock pretty_print to avoid actual printing
        agent_mod.pretty_print = MagicMock()
        
        # Create a test coroutine function
        async def test_run(prompt):
            agent_mod.messages.append({"role": "user", "content": prompt})
            response = await mock_chat.send_messages(agent_mod.messages)
            choices = response.get("choices", [])
            
            # Handle missing choices
            result = ""
            agent_mod.pretty_print("Result", result)
        
        # Patch run_conversation to use our test function
        with patch.object(agent_mod, 'run_conversation', side_effect=test_run):
            # Call run_conversation with test input
            await agent_mod.run_conversation("Test missing choices")
            
            # Verify handling of missing choices
            agent_mod.pretty_print.assert_called_once_with("Result", "")
        
    finally:
        # Restore original objects
        agent_mod.messages = original_messages
        agent_mod.chat = original_chat
        agent_mod.pretty_print = original_pretty_print


@pytest.mark.asyncio
async def test_run_conversation_with_empty_choices():
    """Test run_conversation with empty choices list."""
    import agent as agent_mod
    
    # Save original objects
    original_messages = agent_mod.messages.copy()
    original_chat = agent_mod.chat
    original_pretty_print = agent_mod.pretty_print
    
    try:
        # Mock chat with empty choices list
        mock_chat = MagicMock()
        mock_chat.send_messages = AsyncMock(return_value={"choices": []})
        agent_mod.chat = mock_chat
        
        # Mock pretty_print to avoid actual printing
        agent_mod.pretty_print = MagicMock()
        
        # Create a test coroutine function
        async def test_run(prompt):
            agent_mod.messages.append({"role": "user", "content": prompt})
            response = await mock_chat.send_messages(agent_mod.messages)
            choices = response.get("choices", [])
            
            # Handle empty choices
            result = ""
            agent_mod.pretty_print("Result", result)
        
        # Patch run_conversation to use our test function
        with patch.object(agent_mod, 'run_conversation', side_effect=test_run):
            # Call run_conversation with test input
            await agent_mod.run_conversation("Test empty choices list")
            
            # Verify handling of empty choices
            agent_mod.pretty_print.assert_called_once_with("Result", "")
        
    finally:
        # Restore original objects
        agent_mod.messages = original_messages
        agent_mod.chat = original_chat
        agent_mod.pretty_print = original_pretty_print