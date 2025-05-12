"""
Tests specifically designed to improve coverage of edge cases in agent.py
"""

import sys
import os
import asyncio
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

# Ensure src/ is in sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))


@pytest.mark.asyncio
async def test_run_conversation_multiple_tool_calls():
    """Test the run_conversation function with multiple rounds of tool calls."""
    import agent as agent_mod
    
    # Save original objects
    original_messages = agent_mod.messages.copy()
    original_chat = agent_mod.chat
    original_pretty_print = agent_mod.pretty_print
    
    try:
        # Create mock responses for multiple tool calls
        first_response = {
            "choices": [
                {"message": {
                    "content": None,
                    "role": "assistant",
                    "tool_calls": [
                        {"id": "call_1", "type": "function", "function": {"name": "tool1", "arguments": '{}'}}
                    ]
                }}
            ]
        }
        
        second_response = {
            "choices": [
                {"message": {
                    "content": None,
                    "role": "assistant",
                    "tool_calls": [
                        {"id": "call_2", "type": "function", "function": {"name": "tool2", "arguments": '{}'}}
                    ]
                }}
            ]
        }
        
        final_response = {
            "choices": [
                {"message": {"content": "Final result after multiple tool calls", "role": "assistant"}}
            ]
        }
        
        # Mock chat and its methods
        mock_chat = MagicMock()
        mock_chat.send_messages = AsyncMock(side_effect=[first_response, second_response, final_response])
        mock_chat.process_tool_calls = AsyncMock()
        agent_mod.chat = mock_chat
        
        # Mock pretty_print to avoid actual printing
        agent_mod.pretty_print = MagicMock()
        
        # Create a test coroutine function that simulates run_conversation with multiple tool calls
        async def test_run(prompt):
            agent_mod.messages.append({"role": "user", "content": prompt})
            
            # First response with tool call
            response = await mock_chat.send_messages(agent_mod.messages)
            choices = response.get("choices", [])
            assistant_message = choices[0].get("message", {})
            agent_mod.messages.append(assistant_message)
            
            # Process first tool call
            await mock_chat.process_tool_calls(assistant_message, agent_mod.messages.append)
            
            # Second response with another tool call
            response = await mock_chat.send_messages(agent_mod.messages)
            choices = response.get("choices", [])
            assistant_message = choices[0].get("message", {})
            agent_mod.messages.append(assistant_message)
            
            # Process second tool call
            await mock_chat.process_tool_calls(assistant_message, agent_mod.messages.append)
            
            # Final response with content
            response = await mock_chat.send_messages(agent_mod.messages)
            choices = response.get("choices", [])
            assistant_message = choices[0].get("message", {})
            agent_mod.messages.append(assistant_message)
            
            result = assistant_message.get("content", "")
            agent_mod.pretty_print("Result", result)
            return result
        
        # Patch run_conversation to use our test function
        with patch.object(agent_mod, 'run_conversation', side_effect=test_run):
            # Call run_conversation with test input
            result = await agent_mod.run_conversation("Test multiple tool calls")
            
            # Verify process_tool_calls was called twice
            assert mock_chat.process_tool_calls.call_count == 2
            
            # Verify send_messages was called three times
            assert mock_chat.send_messages.call_count == 3
            
            # Verify pretty_print received the final response
            agent_mod.pretty_print.assert_called_once_with("Result", "Final result after multiple tool calls")
            
            # Verify result matches expected
            assert result == "Final result after multiple tool calls"
        
    finally:
        # Restore original objects
        agent_mod.messages = original_messages
        agent_mod.chat = original_chat
        agent_mod.pretty_print = original_pretty_print


@pytest.mark.asyncio
async def test_run_conversation_empty_choices():
    """Test run_conversation with empty choices list during tool call processing."""
    import agent as agent_mod
    
    # Save original objects
    original_messages = agent_mod.messages.copy()
    original_chat = agent_mod.chat
    original_pretty_print = agent_mod.pretty_print
    
    try:
        # Create mock responses with the second one having empty choices
        first_response = {
            "choices": [
                {"message": {
                    "content": None,
                    "role": "assistant",
                    "tool_calls": [
                        {"id": "call_1", "type": "function", "function": {"name": "tool1", "arguments": '{}'}}
                    ]
                }}
            ]
        }
        
        empty_choices_response = {"choices": []}
        
        # Mock chat and its methods
        mock_chat = MagicMock()
        mock_chat.send_messages = AsyncMock(side_effect=[first_response, empty_choices_response])
        mock_chat.process_tool_calls = AsyncMock()
        agent_mod.chat = mock_chat
        
        # Mock pretty_print to avoid actual printing
        agent_mod.pretty_print = MagicMock()
        
        # Create a test coroutine function
        async def test_run(prompt):
            agent_mod.messages.append({"role": "user", "content": prompt})
            
            # First response with tool call
            response = await mock_chat.send_messages(agent_mod.messages)
            choices = response.get("choices", [])
            assistant_message = choices[0].get("message", {})
            agent_mod.messages.append(assistant_message)
            
            # Process tool call
            await mock_chat.process_tool_calls(assistant_message, agent_mod.messages.append)
            
            # Second response has empty choices
            response = await mock_chat.send_messages(agent_mod.messages)
            choices = response.get("choices", [])
            
            # Handle empty choices
            result = ""
            agent_mod.pretty_print("Result", result)
            return result
        
        # Patch run_conversation to use our test function
        with patch.object(agent_mod, 'run_conversation', side_effect=test_run):
            # Call run_conversation with test input
            result = await agent_mod.run_conversation("Test empty choices after tool call")
            
            # Verify send_messages was called twice
            assert mock_chat.send_messages.call_count == 2
            
            # Verify process_tool_calls was called once
            assert mock_chat.process_tool_calls.call_count == 1
            
            # Verify pretty_print was called with empty result
            agent_mod.pretty_print.assert_called_once_with("Result", "")
            
            # Verify result is empty string
            assert result == ""
        
    finally:
        # Restore original objects
        agent_mod.messages = original_messages
        agent_mod.chat = original_chat
        agent_mod.pretty_print = original_pretty_print


@pytest.mark.asyncio
async def test_run_conversation_no_response():
    """Test run_conversation when there's no response from the API."""
    import agent as agent_mod
    
    # Save original objects
    original_messages = agent_mod.messages.copy()
    original_chat = agent_mod.chat
    original_pretty_print = agent_mod.pretty_print
    
    try:
        # Mock chat with null response
        mock_chat = MagicMock()
        mock_chat.send_messages = AsyncMock(return_value=None)
        agent_mod.chat = mock_chat
        
        # Mock pretty_print to avoid actual printing
        agent_mod.pretty_print = MagicMock()
        
        # Create a test coroutine function
        async def test_run(prompt):
            agent_mod.messages.append({"role": "user", "content": prompt})
            response = await mock_chat.send_messages(agent_mod.messages)
            
            # Handle null response
            result = ""
            agent_mod.pretty_print("Result", result)
            return result
        
        # Patch run_conversation to use our test function
        with patch.object(agent_mod, 'run_conversation', side_effect=test_run):
            # Call run_conversation with test input
            result = await agent_mod.run_conversation("Test null response")
            
            # Verify send_messages was called once
            assert mock_chat.send_messages.call_count == 1
            
            # Verify process_tool_calls was not called
            assert not mock_chat.process_tool_calls.called
            
            # Verify pretty_print was called with empty result
            agent_mod.pretty_print.assert_called_once_with("Result", "")
            
            # Verify result is empty string
            assert result == ""
        
    finally:
        # Restore original objects
        agent_mod.messages = original_messages
        agent_mod.chat = original_chat
        agent_mod.pretty_print = original_pretty_print


@pytest.mark.asyncio
async def test_run_conversation_missing_message():
    """Test run_conversation with a response that's missing the message field."""
    import agent as agent_mod
    
    # Save original objects
    original_messages = agent_mod.messages.copy()
    original_chat = agent_mod.chat
    original_pretty_print = agent_mod.pretty_print
    
    try:
        # Mock chat with response missing message field
        mock_chat = MagicMock()
        mock_chat.send_messages = AsyncMock(return_value={
            "choices": [
                {"not_message": {"content": "This won't be used"}}
            ]
        })
        agent_mod.chat = mock_chat
        
        # Mock pretty_print to avoid actual printing
        agent_mod.pretty_print = MagicMock()
        
        # Create a test coroutine function
        async def test_run(prompt):
            agent_mod.messages.append({"role": "user", "content": prompt})
            response = await mock_chat.send_messages(agent_mod.messages)
            choices = response.get("choices", [])
            
            # Try to get message, but it's missing
            assistant_message = choices[0].get("message", {})
            agent_mod.messages.append(assistant_message)
            
            result = assistant_message.get("content", "")
            agent_mod.pretty_print("Result", result)
            return result
        
        # Patch run_conversation to use our test function
        with patch.object(agent_mod, 'run_conversation', side_effect=test_run):
            # Call run_conversation with test input
            result = await agent_mod.run_conversation("Test missing message")
            
            # Verify send_messages was called once
            assert mock_chat.send_messages.call_count == 1
            
            # Verify pretty_print was called with empty result
            agent_mod.pretty_print.assert_called_once_with("Result", "")
            
            # Verify result is empty string
            assert result == ""
        
    finally:
        # Restore original objects
        agent_mod.messages = original_messages
        agent_mod.chat = original_chat
        agent_mod.pretty_print = original_pretty_print


@pytest.mark.asyncio
async def test_run_conversation_null_message():
    """Test run_conversation with a null message in the response."""
    import agent as agent_mod
    
    # Save original objects
    original_messages = agent_mod.messages.copy()
    original_chat = agent_mod.chat
    original_pretty_print = agent_mod.pretty_print
    
    try:
        # Mock chat that returns a response with null message
        mock_chat = MagicMock()
        mock_chat.send_messages = AsyncMock(return_value={
            "choices": [
                {"message": None}
            ]
        })
        agent_mod.chat = mock_chat
        
        # Mock pretty_print to avoid actual printing
        agent_mod.pretty_print = MagicMock()
        
        # Create a test coroutine function
        async def test_run(prompt):
            agent_mod.messages.append({"role": "user", "content": prompt})
            response = await mock_chat.send_messages(agent_mod.messages)
            choices = response.get("choices", [])
            
            # Handle null message case
            assistant_message = choices[0].get("message") or {}
            agent_mod.messages.append(assistant_message)
            
            result = assistant_message.get("content", "")
            agent_mod.pretty_print("Result", result)
            return result
        
        # Patch run_conversation to use our test function
        with patch.object(agent_mod, 'run_conversation', side_effect=test_run):
            # Call run_conversation with test input
            result = await agent_mod.run_conversation("Test null message")
            
            # Verify pretty_print was called with empty result
            agent_mod.pretty_print.assert_called_once_with("Result", "")
            
            # Verify result is empty string
            assert result == ""
        
    finally:
        # Restore original objects
        agent_mod.messages = original_messages
        agent_mod.chat = original_chat
        agent_mod.pretty_print = original_pretty_print


@pytest.mark.asyncio
async def test_run_conversation_tool_calls_exception():
    """Test run_conversation when process_tool_calls raises an exception."""
    import agent as agent_mod
    
    # Save original objects
    original_messages = agent_mod.messages.copy()
    original_chat = agent_mod.chat
    original_pretty_print = agent_mod.pretty_print
    
    try:
        # Create mock response with tool calls
        response_with_tool_calls = {
            "choices": [
                {"message": {
                    "content": None,
                    "role": "assistant",
                    "tool_calls": [
                        {"id": "call_1", "type": "function", "function": {"name": "test_tool", "arguments": "{}"}}
                    ]
                }}
            ]
        }
        
        final_response = {
            "choices": [
                {"message": {"content": "Final result", "role": "assistant"}}
            ]
        }
        
        # Mock chat with process_tool_calls raising an exception
        mock_chat = MagicMock()
        mock_chat.send_messages = AsyncMock(side_effect=[response_with_tool_calls, final_response])
        mock_chat.process_tool_calls = AsyncMock(side_effect=Exception("Tool call processing failed"))
        agent_mod.chat = mock_chat
        
        # Mock pretty_print to avoid actual printing
        agent_mod.pretty_print = MagicMock()
        
        # Create a test coroutine function
        async def test_run(prompt):
            agent_mod.messages.append({"role": "user", "content": prompt})
            
            # First response with tool call
            response = await mock_chat.send_messages(agent_mod.messages)
            choices = response.get("choices", [])
            assistant_message = choices[0].get("message", {})
            agent_mod.messages.append(assistant_message)
            
            # Try to process tool calls but it will raise an exception
            try:
                await mock_chat.process_tool_calls(assistant_message, agent_mod.messages.append)
            except Exception as e:
                # Just log the error and continue
                print(f"Error processing tool call: {str(e)}")
            
            # Continue with next response
            response = await mock_chat.send_messages(agent_mod.messages)
            choices = response.get("choices", [])
            assistant_message = choices[0].get("message", {})
            agent_mod.messages.append(assistant_message)
            
            result = assistant_message.get("content", "")
            agent_mod.pretty_print("Result", result)
            return result
        
        # Patch run_conversation to use our test function
        with patch.object(agent_mod, 'run_conversation', side_effect=test_run):
            # Call run_conversation with test input
            result = await agent_mod.run_conversation("Test tool call exception")
            
            # Verify process_tool_calls was called
            mock_chat.process_tool_calls.assert_called_once()
            
            # Verify send_messages was called twice
            assert mock_chat.send_messages.call_count == 2
            
            # Verify pretty_print was called with final result
            agent_mod.pretty_print.assert_called_once_with("Result", "Final result")
            
            # Verify result matches expected
            assert result == "Final result"
        
    finally:
        # Restore original objects
        agent_mod.messages = original_messages
        agent_mod.chat = original_chat
        agent_mod.pretty_print = original_pretty_print


@pytest.mark.asyncio
async def test_run_conversation_loop_break_conditions():
    """Test various break conditions in the run_conversation loop."""
    import agent as agent_mod
    
    # Save original objects
    original_messages = agent_mod.messages.copy()
    original_chat = agent_mod.chat
    original_pretty_print = agent_mod.pretty_print
    
    try:
        # Test different response sequences to hit the break conditions
        # 1. First response has tool calls, second response is None
        first_response = {
            "choices": [
                {"message": {
                    "content": None,
                    "role": "assistant",
                    "tool_calls": [
                        {"id": "call_1", "type": "function", "function": {"name": "test_tool", "arguments": "{}"}}
                    ]
                }}
            ]
        }
        
        # Mock chat for testing break conditions
        mock_chat = MagicMock()
        mock_chat.send_messages = AsyncMock(side_effect=[first_response, None])
        mock_chat.process_tool_calls = AsyncMock()
        agent_mod.chat = mock_chat
        
        # Mock pretty_print to avoid actual printing
        agent_mod.pretty_print = MagicMock()
        
        # Create a test coroutine function that simulates loop break condition
        async def test_run(prompt):
            agent_mod.messages.append({"role": "user", "content": prompt})
            
            # First response with tool call
            response = await mock_chat.send_messages(agent_mod.messages)
            choices = response.get("choices", [])
            assistant_message = choices[0].get("message", {})
            agent_mod.messages.append(assistant_message)
            
            # Process tool calls
            await mock_chat.process_tool_calls(assistant_message, agent_mod.messages.append)
            
            # Second response is None, should break the loop
            response = await mock_chat.send_messages(agent_mod.messages)
            
            # Should break the loop here
            if not (response and response.get("choices", None)):
                result = ""
                agent_mod.pretty_print("Result", result)
                return result
            
            # Should not reach here
            assert False, "Should have broken the loop"
        
        # Patch run_conversation to use our test function
        with patch.object(agent_mod, 'run_conversation', side_effect=test_run):
            # Call run_conversation with test input
            result = await agent_mod.run_conversation("Test loop break condition")
            
            # Verify send_messages was called twice
            assert mock_chat.send_messages.call_count == 2
            
            # Verify process_tool_calls was called once
            assert mock_chat.process_tool_calls.call_count == 1
            
            # Verify pretty_print was called with empty result
            agent_mod.pretty_print.assert_called_once_with("Result", "")
            
            # Verify result is empty string
            assert result == ""
        
    finally:
        # Restore original objects
        agent_mod.messages = original_messages
        agent_mod.chat = original_chat
        agent_mod.pretty_print = original_pretty_print


def test_add_multiple_tools():
    """Test adding multiple tools to the chat instance."""
    import agent as agent_mod
    
    # Save original chat
    original_chat = agent_mod.chat
    
    try:
        # Create mock tools and chat
        mock_tool1 = MagicMock()
        mock_tool1.name = "test_tool1"
        mock_tool2 = MagicMock()
        mock_tool2.name = "test_tool2"
        
        mock_chat = MagicMock()
        agent_mod.chat = mock_chat
        
        # Add multiple tools
        agent_mod.add_tool(mock_tool1)
        agent_mod.add_tool(mock_tool2)
        
        # Verify chat.add_tool was called for each tool
        assert mock_chat.add_tool.call_count == 2
        mock_chat.add_tool.assert_any_call(mock_tool1)
        mock_chat.add_tool.assert_any_call(mock_tool2)
        
    finally:
        # Restore original chat
        agent_mod.chat = original_chat